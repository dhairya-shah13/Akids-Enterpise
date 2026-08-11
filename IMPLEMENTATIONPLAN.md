# Implementation Plan — Cloudflare Outer Perimeter for A Kids India (Vercel + Django)

> **Status: APPROVED 2026-08-11 — owner typed "Proceed with the plan".**
> §7 (the only repository change) is **IMPLEMENTED**: `ratelimit.client_ip()`
> now prefers `CF-Connecting-IP`, with 3 new unit tests — full suite **66/66 pass**.
> Everything else is **Cloudflare-side / DNS-side / Vercel-side** and is executed by
> the owner using the step-by-step **OWNER RUNBOOK in §13** (Hostinger + Cloudflare).

---

## 1. Purpose & Scope

Add **Cloudflare (Free plan)** as an outer perimeter in front of the existing Vercel
deployment:

```
Internet → Cloudflare (DNS / CDN / WAF-Free-Managed / Bot Fight Mode / Rate Limiting)
        → Vercel Edge (vercel.json routes, custom_404 edge caching, existing protections)
        → Django 6.x application (auth, CSRF, per-endpoint rate limits, sessions)
```

- **In scope:** Cloudflare account/zone setup, DNS nameserver handover (Hostinger →
  Cloudflare), SSL mode, WAF managed ruleset, Bot Fight Mode, one consolidated rate
  limiting rule, cache rules, monitoring, rollback.
- **Out of scope (explicitly):** SEO work, code changes beyond the single justified
  proposal in §7, any change to Vercel Firewall rules (none exist to change on Hobby —
  see §6), email provider migration.
- **Non-goals that must not happen:** weakening/removing existing Django or Vercel
  protections; caching authenticated or private responses; proxying mail records.

---

## 2. Current-State Findings (verified 2026-08-11)

### 2.1 Repository / application

- **Stack:** Django 6.x (`backend/little_fingers/`, `backend/products/`), WSGI via
  `backend/little_fingers/wsgi.py`, Tailwind/HTML/vanilla JS frontend, deployed on Vercel.
- **Existing protections (do not undo):**
  - `custom_404` handler (`views.py:2342`) registered via `handler404` in `urls.py`,
    returns `Cache-Control: public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800`
    so probe/missing-URL traffic is served from the edge.
  - `vercel.json` edge routes: `/static/*` (immutable cache), `/robots.txt`,
    `/BingSiteAuth.xml`, `/favicon.ico`, `/catalogue/pdf/(indoor|outdoor)/`, plus
    `status:404` edge routes for probe paths (`/wp-admin/`, `/wp-login.php`,
    `/xmlrpc.php`, `/.env`, `/.git`, `/config`, `/phpmyadmin`, `/etc`, `/server-status`,
    `/actuator`, `/backend(.*)`, `/homepage1.html`, `/logo.png`, `/ponytail`, …).
  - Conditional CSRF middleware (`CsrfCookieBootstrapMiddleware`) + `GET /api/csrf/`
    + lazy `ensureCsrf()` in `main.js` — new visitors landing on edge-cached pages can
    still POST.
  - `public_cache_control` decorator: anonymous GETs get `public, s-maxage=…`,
    authenticated/admin requests get `private, no-store`.
  - Django per-IP rate limits (**locmem = per-instance, not global**):
    login `10/60s`, signup `5/300s`, resend_verification `3/300s`, firebase_login
    `5/300s`, change_password `10/60s`, chat_api `10/60s`, submit_inquiry `10/300s`
    (`backend/products/ratelimit.py`).
  - `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`, `CSRF_TRUSTED_ORIGINS`
    (akidsenterprise.com, www, akids-enterpise.vercel.app), HSTS 1y + preload,
    `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` in prod.
- **External integrations (all egress; unaffected by proxying):** Firebase Auth
  (`identitytoolkit.googleapis.com`), Google OAuth, Groq LLM (`api.groq.com` for
  `/api/chat/`), Supabase + Google Drive (`lh3.googleusercontent.com`) + Unsplash for
  product images. **No inbound webhooks / payment gateway** (checkout currently
  simulates payment; Razorpay is a documented future item — so no webhook path
  needs allowlisting).

### 2.2 Route inventory → protection class

| Class | Routes (Django `urls.py`) | Cloudflare treatment |
|---|---|---|
| Public static/cacheable | `/static/*`, `/favicon.ico`, `/robots.txt`, `/BingSiteAuth.xml` | Cache (CDN) |
| Public cached HTML | `/`, `/indoors/`, `/outdoors/`, `/shreemsports/`, `/product/<id>/`, `/about/`, `/safety-standards/`, `/testimonials/`, `/contact/`, `/privacy-policy/`, `/terms-of-service/`, `/search`, `<module>/view-all-products/`, `/catalogue/pdf/*`, `/sitemap.xml` | Cache, respect origin `s-maxage` |
| Public dynamic | `/api/csrf/`, `/api/search-suggestions/` | No cache (or short TTL) |
| Auth / sensitive (never cache) | `/login/`, `/signup/`, `/logout/`, `/auth/*`, `/set-password/`, `/profile/`, `/cart*`, `/checkout/`, `/order-success/`, `/admin/`, `/admin-panel/*`, `/api/admin/*` | Bypass cache; rate-limit auth POSTs |
| High-abuse POST endpoints | `/login/`, `/signup/`, `/auth/firebase-login/`, `/auth/resend-verification/`, `/auth/change-password/`, `/api/chat/`, `/api/inquiries/` | Cloudflare rate limit (1 consolidated rule, Free limit) |

### 2.3 DNS (publicly verified via DNS queries — not assumed)

- **Nameservers:** `nebula.dns-parking.com`, `aurora.dns-parking.com` → **Hostinger
  DNS**. Domain likely registered at Hostinger (confirm registrar login during
  implementation).
- `akidsenterprise.com` **A → 216.198.79.1** — serves HTTP **308 Permanent Redirect →
  `https://www.akidsenterprise.com/`** with `Server: Vercel` (`X-Vercel-Id: bom1…`).
  So the apex is **already on Vercel** (edge IP, Mumbai region).
- `www.akidsenterprise.com` **CNAME → `f9d97632cce184a4.vercel-dns-017.com`** (Vercel DNS).
- **MX:** `mx1.hostinger.com` (pref 5), `mx2.hostinger.com` (pref 10) → Hostinger mail.
- **TXT:** `v=spf1 include:_spf.mail.hostinger.com include:_spf.firebasemail.com ~all`;
  `google-site-verification=MDpK56nhqTXdfeuLhAGelHCAsAaeOL2GsPsIwSxdW_c`;
  `firebase=a-kids-enterprise-c39f2`.
- **DMARC:** `_dmarc.akidsenterprise.com` TXT `v=DMARC1; p=none`.
- **DKIM:** `default._domainkey`, `hostinger._domainkey`, `google._domainkey` → all
  NXDOMAIN. Selector unknown — **must be pulled from the Hostinger mail panel during
  implementation and re-created in Cloudflare DNS (DNS-only).** If Hostinger mail is
  not actively used, confirm before dropping it; **never proxied either way.**
- **Direct-origin exposure:** `https://akids-enterpise.vercel.app` returns 200 with
  the full site. This is a live origin that **bypasses Cloudflare** and cannot be
  IP-locked on Vercel **Hobby** (§6).

### 2.4 Gaps this plan closes

1. No WAF/global rate limit ahead of Vercel (Django limits are per-instance locmem —
   a bot farm rotating Vercel instances/regions evades them).
2. `client_ip()` in `ratelimit.py` trusts the **first hop of `X-Forwarded-For`**, which
   is **spoofable** once Cloudflare is in front (Cloudflare *appends* to client-supplied
   XFF rather than overwriting it). §7 proposes the one justified code change.
3. `akids-enterpise.vercel.app` remains reachable directly (Hobby limitation — §6).

---

## 3. Target Architecture & What Cloudflare Will Do

| Layer | Protect | Block | Allow | Cache |
|---|---|---|---|---|
| Cloudflare DNS | Zone hosting after NS handover | — | All records (proxied: A/CNAME; DNS-only: MX/TXT/DMARC/DKIM) | — |
| Cloudflare CDN | Static + public HTML | — | — | `/static/*`, `/catalogue/pdf/*`, public HTML (respect origin `s-maxage`) |
| Cloudflare WAF (Free Managed Ruleset) | App from SQLi/XSS/LFI/scanners | Malicious payloads, known scanner patterns | Legitimate requests | — |
| Cloudflare Custom Rule (probes) | Origin transfer | `/wp-admin/`, `/wp-login.php`, `/xmlrpc.php`, `/.env`, `/.git`, `/config`, `/phpmyadmin`, `/actuator`, `/server-status`, `/backend(.*)` | — | — |
| Cloudflare Bot Fight Mode (Free) | App from bot abuse | (via challenge) meta-externalagent, aggressive scrapers, headless bots | Verified search engines (Googlebot, Bingbot — Cloudflare's built-in allowlist) | — |
| Cloudflare Rate Limiting (1 rule) | Auth/chat/inquiry endpoints | (Managed Challenge after threshold) distributed brute-force/spam | Normal browsing incl. NAT'd school/daycare users (generous threshold + challenge, not block) | — |
| Vercel Edge (unchanged) | Origin | — | — | Existing `s-maxage`/404 caching continues |

---

## 4. Phase-by-Phase Configuration (to be applied ONLY after approval)

### Phase 0 — Pre-flight checklist
- [ ] Confirm registrar = Hostinger and credentials available (owner).
- [ ] Capture full current DNS record set from Hostinger panel (including any records
      not visible via public queries — e.g. DKIM selector, any subdomains).
- [ ] Confirm Hostinger email is actively used; identify DKIM selector (owner / Hostinger panel).
- [ ] Verify no other service depends on `akidsenterprise.com` DNS that isn't in §2.3.
- [ ] Baseline Vercel usage metrics (function invocations, origin transfer, edge requests)
      from the Vercel dashboard for before/after comparison.

### Phase 1 — Cloudflare account + zone (start from scratch)
1. Create Cloudflare account (free) → **Add site `akidsenterprise.com`** (Free plan).
2. Let Cloudflare **scan/import existing DNS records**; review every record against §2.3.
3. Verify imported records and fix discrepancies **before** the nameserver change.
4. Cloudflare will present two nameservers (`ns1.cloudflare.com` / `ns2.cloudflare.com`
   — exact values shown in dashboard) — do **not** change NS yet; proceed to Phase 2 first.

### Phase 2 — SSL/TLS (before going live)
- **SSL/TLS encryption mode → Full (strict)** (Vercel presents a valid publicly trusted
  cert for both apex and www; Full-strict is safe and required to avoid the Flexible
  HTTP-downgrade redirect loop).
- Enable **Always Use HTTPS** and **Automatic HTTPS Rewrites** (Edge Certificates tab).
- Confirm **Universal SSL** shows "Active" for `akidsenterprise.com` + `www` (a few
  minutes after zone activation; status can be checked before NS switch — see Phase 6).
- Leave **HSTS** off at Cloudflare (origin already sends `max-age=31536000;
  includeSubDomains; preload`; do not double-declare — Cloudflare HSTS could lock in
  misconfiguration states that would be harder to roll back).

### Phase 3 — Security configuration (Free plan)
1. **WAF → Managed Rules:** enable the **Cloudflare Free Managed Ruleset** (the only
   managed ruleset available on Free) with its default action (`Block`). Cloudflare
   Managed Ruleset + OWASP Core Ruleset are **not** available on Free — noted, not
   blocking (Free ruleset covers high-impact/exploited patterns).
2. **Custom Rules (one rule):** block known probe paths at the edge so they never reach
   Vercel (complements — does not replace — the existing `vercel.json` edge-404 routes):
   ```
   (http.request.uri.path matches "(?i)^/(wp-admin|wp-login\\.php|xmlrpc\\.php|wordpress|\\.env|\\.git|config|phpmyadmin|actuator|server-status|etc)(/|\\?|$)")
   → Action: Block
   ```
   (Custom WAF rules support regex in match expressions; verify syntax in dashboard.)
   *Note:* Free-plan custom-rule count is small (~5–10); we use **1**.
3. **Bot Fight Mode (Free tier) — ON.** This is the legacy/basic toggle (Super Bot Fight
   Mode requires Pro). It **challenges** (does not hard-block) suspicious bots; verified
   search engines are allowlisted by Cloudflare. `meta-externalagent`, aggressive
   scrapers and headless bots get challenged before reaching Vercel. Watch §10 for
   false positives. **SEO note:** AI crawlers (GPTBot/ClaudeBot etc.) are *not* on the
   free verified-bot allowlist, so they may be challenged — acceptable per owner
   priority ("SEO is explicitly not a priority"), and reversible in one click.
4. **Rate Limiting — ONE rule (Free-plan limit is 1):** consolidate all seven
   high-abuse POST endpoints into a single rule:
   ```
   Name: "Auth/Chat/Inquiry POST backstop"
   Expression:
     (http.request.method eq "POST" and
      http.request.uri.path in {
        "/login/" "/signup/" "/auth/firebase-login/" "/auth/resend-verification/"
        "/auth/change-password/" "/api/chat/" "/api/inquiries/"
      })
   Characteristics: IP address (default)
   Threshold: 60 requests per 60 seconds   ← generous: fine-grained per-endpoint
                                              limits live in Django (10/min etc.);
                                              this rule is the global backstop for
                                              distributed abuse
   Action: Managed Challenge               ← never Block: NAT'd schools/daycares
                                              share one public IP and must not be
                                              locked out
   ```
   - Free-plan caveat: no "count only requests sent to origin" toggle (that is
     Business+); all matching requests count. All seven endpoints are non-cacheable,
     so this is equivalent in practice.
   - Exact Free-plan limit re-verified against Cloudflare docs (Free = 1, Pro = 2,
     Business = 5). If we later need separate thresholds per endpoint, that requires
     Pro (2 rules) or Business (5 rules) — note for future.
5. **Transform Rules:** none required. (Optional later: none on Free add value here.)

### Phase 4 — Cache Rules (Free plan allows 10; we use ~4)
Cache Rules are evaluated in order; **first match wins**, so sensitive bypass rules
come first. All rules scoped to hostname in `{akidsenterprise.com, www.akidsenterprise.com}`.

| # | Name | Match | Setting |
|---|---|---|---|
| 1 | Never cache auth/private | `http.request.uri.path starts_with "/admin-panel/" or starts_with "/admin/" or starts_with "/login" or starts_with "/signup" or starts_with "/auth/" or starts_with "/profile" or starts_with "/cart" or starts_with "/checkout" or starts_with "/order-success" or starts_with "/set-password" or starts_with "/api/"` | **Bypass cache** (always origin) |
| 2 | Static assets | `http.request.uri.path starts_with "/static/"` | **Cache Everything**, edge TTL 30 days, eligible for cache |
| 3 | Catalogue PDFs | `http.request.uri.path starts_with "/catalogue/pdf/"` | **Cache Everything**, edge TTL 1 day (origin sends immutable already) |
| 4 | Public HTML (respect origin) | path in {`/` `/indoors/` `/outdoors/` `/shreemsports/` `/about/` `/safety-standards/` `/testimonials/` `/contact/` `/privacy-policy/` `/terms-of-service/`} or starts_with `/product/` or starts_with `/search` or starts_with `/view-all-products` or in {`/sitemap.xml` `/robots.txt` `/BingSiteAuth.xml`} | **Cache Everything**, TTL **Respect origin** (honors Django's `public, s-maxage=60…300, stale-while-revalidate`) |

**Safety mechanisms that make this safe (verified):**
- Cloudflare **will not cache responses containing `Set-Cookie`** (default behaviour) →
  first-time visitors and any POST/login responses bypass the cache automatically.
- Authenticated requests already receive `Cache-Control: private, no-store` from
  `public_cache_control` → never cached.
- The existing first-visit CSRF-cookie gap is already handled by `/api/csrf/` +
  `main.js ensureCsrf()` (Rule 1 excludes `/api/csrf/` from caching).
- Product-data staleness ≤ TTL (60–300 s) matches current Vercel behaviour; a manual
  "Purge Everything" in the dashboard is available for admin edits.

### Phase 5 — DNS records (final state in Cloudflare)

| Record | Type | Value | Proxy |
|---|---|---|---|
| `@` | A | `216.198.79.1` (Vercel edge; keep as-is) | **Proxied (orange)** |
| `www` | CNAME | `f9d97632cce184a4.vercel-dns-017.com` | **Proxied (orange)** |
| `@` | MX | `mx1.hostinger.com` (5), `mx2.hostinger.com` (10) | **DNS-only** (MX is never proxied by Cloudflare) |
| `@` | TXT | `v=spf1 include:_spf.mail.hostinger.com include:_spf.firebasemail.com ~all` | DNS-only |
| `@` | TXT | `google-site-verification=MDpK56nhqTXdfeuLhAGelHCAsAaeOL2GsPsIwSxdW_c` | DNS-only |
| `@` | TXT | `firebase=a-kids-enterprise-c39f2` | DNS-only |
| `_dmarc` | TXT | `v=DMARC1; p=none` | DNS-only |
| `<selector>._domainkey` | TXT | (from Hostinger panel — verify before NS switch) | DNS-only |

- The apex A→www 308 redirect is implemented **inside Vercel** and is unaffected by
  proxying; keep it.
- (Alternative if Vercel recommends it: apex CNAME with Cloudflare CNAME flattening —
  not required; keep A for minimal change.)

### Phase 6 — Nameserver handover (owner executes, after Phases 1–5 verified)
1. In Hostinger DNS panel, replace NS with the two Cloudflare nameservers shown in the
   Cloudflare dashboard.
2. Wait for propagation (typically minutes–48 h; Cloudflare dashboard shows "Active").
3. Keep **all** records per Phase 5 (MX/TXT/DMARC/DKIM DNS-only).
4. Only after NS change: flip A + www to **Proxied** (if Cloudflare scan set them
   DNS-only by default) — or pre-set proxied so they go live proxied; **recommended
   order: flip to proxied only after the site is confirmed working DNS-only**
   (avoids any Cloudflare-rule misconfig taking the site down).
5. Post-switch checks: §9 smoke tests.

---

## 5. How Vercel's Existing Protections Continue (Layer 2)

Nothing on Vercel or Django is removed or weakened:
- `vercel.json` probe edge-404 routes and `custom_404` edge caching remain (now
  defense-in-depth behind Cloudflare's probe rule).
- Django CSRF, sessions, `public_cache_control`, per-endpoint rate limits remain the
  fine-grained layer; Cloudflare adds the global backstop (Django's locmem limits are
  per-instance and can be evaded by distributed traffic — that is exactly the gap the
  Cloudflare rule closes).
- No duplicate/contradictory blocking: Cloudflare uses challenge/block at the edge;
  Vercel/Django respond 404/429 as before. Rule intent is aligned (stop probes, protect
  auth/chat/inquiry, cache only public content).

---

## 6. Vercel Hobby — Honest Constraints (owner chose Hobby)

- **No Vercel Firewall custom rules and no Attack Challenge Mode on Hobby.** Therefore:
  - We **cannot** IP-lock the origin to Cloudflare ranges (the "origin lock" many guides
    describe requires Pro).
  - `https://akids-enterpise.vercel.app` **will remain reachable** and bypasses
    Cloudflare's WAF/bot/rate-limit layers. This is a **documented limitation**, not a
    regression: that origin already carries the same Django-level protections (rate
    limits, CSRF, `custom_404` edge caching, `vercel.json` edge-404 routes), so abuse
    there is partially absorbed and does not burn function invocations for probe paths.
  - Note: the prompt stated "Vercel Firewall is active (AI Bots = DENY …)" — that
    contradicts Hobby; **verify current Vercel plan in the dashboard during Phase 0**.
    If the account is actually Pro, we gain two optional hardening steps:
    (a) Firewall custom rule `if src.ip not in $cloudflare_ips → Block` using an IP
    list populated from Cloudflare's published ranges, and
    (b) Attack Challenge Mode to neutralize `*.vercel.app` traffic.
- **Future Pro upgrade (optional, not required for this plan):** enables the two steps
  above for a true origin lock. Cost decision for the owner later.

---

## 7. Repository Changes (exactly one, minimal, justified)

**Proposed change — `backend/products/ratelimit.py` `client_ip()` hardening.**
- **Why Cloudflare cannot solve this:** Cloudflare *appends* to `X-Forwarded-For`
  instead of overwriting it, so the first XFF hop — which Django's
  `client_ip()` currently trusts — is **client-spoofable** once Cloudflare fronts the
  site. An attacker could inject a fake first hop to dodge the Django per-IP limits on
  proxied traffic. `CF-Connecting-IP` is authoritative (Cloudflare strips/overwrites any
  client-supplied value), but is only meaningful when traffic actually came via
  Cloudflare.
- **Change (≈6 lines):** prefer `CF-Connecting-IP` when present; fall back to the
  current XFF-first-hop behaviour otherwise:
  ```python
  def client_ip(request):
      # Cloudflare overwrites any client-supplied CF-Connecting-IP, so it is the
      # authoritative client address for proxied traffic. Fall back to the first
      # X-Forwarded-For hop (Vercel's format) for direct-origin traffic.
      cf = request.META.get('HTTP_CF_CONNECTING_IP', '').strip()
      if cf:
          return cf
      xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
      if xff:
          return xff.split(',')[0].strip()
      return request.META.get('REMOTE_ADDR', '')
  ```
- **Justification per requirement #12:** this is the *only* app change; Cloudflare
  cannot fix server-side trust of a header it deliberately appends to.
- **Residual risk (documented):** an attacker hitting the origin directly (vercel.app,
  reachable on Hobby) can still spoof `CF-Connecting-IP` to evade Django per-IP limits.
  This is no worse than today (XFF first hop is equally spoofable on that path) and
  does not affect Cloudflare's own rate limiting (which keys on its own view of the IP).
- **Tests:** add a small unit test for `client_ip()` (CF-Connecting-IP present; absent
  → XFF first hop; neither → REMOTE_ADDR). Existing suite: 63 tests, must stay green.

**No other code changes are required.** CSRF/cookie/cache behaviour is already
compatible with Cloudflare proxying (§4 Phase 4 safety mechanisms).

---

## 8. Email & DNS Integrity

- MX/SPF/DMARC/DKIM/verification TXT records are **DNS-only** — Cloudflare does not
  proxy MX or TXT records, so the NS handover cannot route mail through Cloudflare.
- Recreate the DKIM selector in Cloudflare DNS **before** the NS switch (fetch from the
  Hostinger mail panel; selector unknown — see Phase 0).
- Do **not** enable Cloudflare "Email Routing" (it would hijack MX — out of scope).
- Verify outbound/inbound mail after the switch (send test to/from
  info@akidsenterprise.com).

---

## 9. Validation Plan (post-implementation, maps to requirements)

| # | Requirement | How we verify |
|---|---|---|
| 1 | Perimeter position | `curl -sI https://www.akidsenterprise.com/` shows `CF-Ray` header + origin still returns `Server: Vercel`; Vercel Firewall/Django untouched |
| 2 | Bot protection | Security Events show meta-externalagent / probe paths challenged/blocked at CF; Googlebot still crawls (bot fight allowlist) |
| 3 | DDoS absorbing layer | Cloudflare analytics show edge absorbing request spikes; Vercel function-invocation graph flat |
| 4 | WAF | Security Events show Free Managed Ruleset hits (SQLi/XSS test payloads → blocked) |
| 5 | Rate limiting | Scripted burst of >60 POSTs/min across the 7 endpoints → Managed Challenge (429/403/verify); normal POSTs unaffected |
| 6 | Caching only public | Cache-hit ratio on `/static/*`/HTML; `cf-cache-status: HIT` on public pages; `BYPASS/MISS` on `/login/`, `/profile/`, `/api/chat/`; no `Set-Cookie` responses cached |
| 7 | Origin-abuse reduction | Before/after Vercel usage: function invocations + origin transfer trend down for probe-heavy paths |
| 8 | Vercel protections intact | `vercel.json` probe routes still return edge 404 (check via direct origin or curl); `custom_404` headers unchanged |
| 9 | Functionality preserved | 63-test Django suite green; smoke: login, signup, CSRF POST, chat, inquiry, cart/checkout, admin, catalogue PDF, static assets |
| 10 | Email/DNS | MX/SPF/DMARC/DKIM all DNS-only; test mail both directions |
| 11 | Origin protection | Documented Hobby limitation (§6); verify vercel.app reachable and note residual risk |
| 12 | Minimal code changes | Single 6-line `client_ip()` change + test (§7) |
| 13 | No auto-deploy | This document + explicit "Proceed with implementation plan" gate |
| 14 | No over-blocking | All non-obviously-malicious traffic → challenge/rate-limit/monitor; zero hard blocks beyond probe paths + WAF malicious payloads |
| 15 | Monitoring | Cloudflare Analytics + Security Events dashboards; Vercel usage dashboard; §10 watchlist |

---

## 10. Failure Modes & Watchlist

1. **Misconfigured cache serving private content** — prevented by Rule 1 (bypass) +
   Cloudflare's no-`Set-Cookie`-caching default; verify `cf-cache-status` on auth pages.
2. **SSL mode errors** — Flexible would cause a redirect loop (HTTP→HTTPS at origin);
   wrong cert → 525/526. Set **Full (strict)**; if 522/523/524 (timeouts) or 521
   (origin down) appear, check Vercel directly first.
3. **NS change breaks mail** — MX/TXT never proxied; still verify mail and keep the old
   NS pair documented for instant rollback.
4. **Rate-limit false positives** — schools/daycares share NAT IPs; threshold is
   generous (60/min) and action is Managed Challenge (never Block). Watch Security
   Events for repeated challenges from Indian ISP ranges.
5. **Bot Fight Mode false positives** — corporate proxies/AV scanners may be
   challenged; disable in one click if a legit customer complains (SEO/AI crawlers are
   explicitly non-priority here).
6. **XFF/CF-Connecting-IP spoofing** — addressed by §7; residual direct-origin
   spoofing documented and no worse than today.
7. **Stale cache after admin product edits** — TTL ≤ 300 s; use Purge Everything in
   the dashboard for urgent edits.
8. **Cloudflare IP range changes** — only relevant if we later add a Vercel-side IP
   allowlist (Pro); Cloudflare publishes ranges at cloudflare.com/ips-v4 and ips-v6 —
   re-import on change.
9. **HSTS interplay** — origin HSTS (1y, preload) continues to apply; Cloudflare HSTS
   stays OFF to keep rollback trivial (DNS-only flip still works for browsers that have
   cached HSTS: flipping proxy→DNS-only keeps serving HTTPS from Vercel, so no risk).
10. **Universal SSL not yet active** — check before NS switch; do not go live proxied
    until SSL shows Active.

---

## 11. Rollback Procedure (Cloudflare-only; never touches Vercel/Django)

**Instant (primary):**
1. **DNS-only rollback:** in Cloudflare DNS, set A + www from *Proxied* to *DNS-only*
   (grey cloud). Cloudflare stops applying WAF/bot/rate-limit/cache and resolves
   straight to Vercel. Site stays online within seconds–minutes (DNS TTL).
2. **Disable features individually** (no DNS change needed):
   - Bot Fight Mode → OFF (toggle).
   - Rate Limiting rule → disabled.
   - WAF Free Managed Ruleset → disabled.
   - Custom probe rule → disabled.
   - Cache Rules → deleted (cache purge happens automatically on rule removal).

**Full revert (last resort):**
3. Change nameservers back to Hostinger (`nebula`/`aurora.dns-parking.com`) in the
   registrar panel; remove the Cloudflare zone. Propagation typically
   minutes–48 h; DNS served from Hostinger again.
4. After any rollback: rerun §9 smoke tests (login/chat/inquiry/static) to confirm
   Vercel + Django behave as before (they were never modified).

---

## 12. Approval Gate

Per RULES.md §2.2 and owner instruction:
- [ ] Owner types **"Proceed with implementation plan"** to authorize Phase 0–6.
- [ ] Owner has registrar/Hostinger access for the NS change (confirmed: yes).
- [ ] Post-implementation, `Changelog.md` + `Context.md` will be updated per RULES.md §8.1.

**Open items to confirm at Phase 0 (not blockers for this plan):**
- Actual Vercel plan (Hobby vs Pro) — prompt contradicts itself; §6 covers both.
- DKIM selector from the Hostinger mail panel.
- Whether Hostinger email must keep working (MX exists → assumed yes).
- Cloudflare Free custom-rule exact count (dashboard shows it; we use 1–2).

---

## 13. OWNER RUNBOOK — Hostinger & Cloudflare (step-by-step)

> Everything here is done by YOU in the Cloudflare and Hostinger dashboards (I cannot
> access those accounts). The only repo change (§7) is already implemented and tested.
> Do Cloudflare **Part A first**, then Hostinger **Part B**, then verify **Part C**.
> Estimated total time: 45–90 min plus nameserver propagation.

### Part A — Cloudflare (create zone, configure everything BEFORE touching Hostinger)

**A1. Create the account + zone**
1. Go to https://dash.cloudflare.com/sign-up → create a free account (or sign in).
2. **Add site** → enter `akidsenterprise.com` → select the **Free** plan.
3. Cloudflare scans your existing DNS records. Click **Continue** — do **not** change
   nameservers yet; you will do that in Part B.

**A2. Review DNS records (Security → DNS → Records)**
Ensure the following exist exactly (Cloudflare's scan usually imports them):

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | `@` | `216.198.79.1` (Vercel edge — currently serves the apex→www redirect) | Proxied (orange) **✓** |
| CNAME | `www` | `f9d97632cce184a4.vercel-dns-017.com` | Proxied (orange) **✓** |
| MX | `@` | `mx1.hostinger.com` (priority 5) | DNS-only (grey) — MX is never proxied |
| MX | `@` | `mx2.hostinger.com` (priority 10) | DNS-only |
| TXT | `@` | `v=spf1 include:_spf.mail.hostinger.com include:_spf.firebasemail.com ~all` | DNS-only |
| TXT | `@` | `google-site-verification=MDpK56nhqTXdfeuLhAGelHCAsAaeOL2GsPsIwSxdW_c` | DNS-only |
| TXT | `@` | `firebase=a-kids-enterprise-c39f2` | DNS-only |
| TXT | `_dmarc` | `v=DMARC1; p=none` | DNS-only |
| TXT | `<selector>._domainkey` | DKIM value — **get from Hostinger mail panel** (selector unknown; Part B2) | DNS-only |

**Proxied = orange cloud. DNS-only = grey cloud.** Mail + verification TXT records must
stay grey. If the scan imported them grey, that is correct — leave them.

**A3. SSL/TLS (before going live)**
1. **SSL/TLS → Overview → Encryption mode → Full (strict)**.
2. **SSL/TLS → Edge Certificates**: enable **Always Use HTTPS** and **Automatic HTTPS
   Rewrites**. Leave **HSTS off** (Django already sends HSTS).
3. Check **Universal SSL** shows **Active** for both `akidsenterprise.com` and
   `www.akidsenterprise.com` (usually 5–15 min; can be up to 24 h — proceed with the
   rest while it issues).

**A4. Security — WAF**
1. **Security → WAF → Custom rules → Create rule:**
   - Name: `Block known probe paths`
   - Expression: `(http.request.uri.path matches "(?i)^/(wp-admin|wp-login\\.php|xmlrpc\\.php|wordpress|\\.env|\\.git|config|phpmyadmin|actuator|server-status|etc)(/|\\?|$)")`
   - Action: **Block** → Deploy.
2. **Security → WAF → Managed rules**: enable the **Cloudflare Free Managed Ruleset**
   with its default action (Block).

**A5. Security — Bots**
- **Security → Bots → Bot Fight Mode → ON.** It challenges (not hard-blocks) suspicious
  bots; Googlebot/Bingbot are allowlisted by Cloudflare. If a real customer ever gets
  challenged, turn this off in one click (see rollback).

**A6. Security — Rate limiting (Free plan = 1 rule)**
- **Security → Rate limiting → Create rule:**
  - Name: `Auth/Chat/Inquiry POST backstop`
  - Expression:
    ```
    (http.request.method eq "POST" and http.request.uri.path in {"/login/" "/signup/" "/auth/firebase-login/" "/auth/resend-verification/" "/auth/change-password/" "/api/chat/" "/api/inquiries/"})
    ```
  - Period: **60 seconds**, Requests: **60**
  - Action: **Managed Challenge** (never Block — schools/daycares share one public IP)
  - Deploy.

**A7. Caching — Cache Rules (Free plan allows 10; we use 4)**
**Caching → Cache rules → Create rule** four times, in this order (order matters):

1. **`Never cache auth/private`** — match:
   `http.request.uri.path starts_with "/admin-panel/" or starts_with "/admin/" or starts_with "/login" or starts_with "/signup" or starts_with "/auth/" or starts_with "/profile" or starts_with "/cart" or starts_with "/checkout" or starts_with "/order-success" or starts_with "/set-password" or starts_with "/api/"`
   → **Bypass cache**.
2. **`Static assets`** — match: `http.request.uri.path starts_with "/static/"`
   → **Cache Everything**, Edge TTL **30 days**.
3. **`Catalogue PDFs`** — match: `http.request.uri.path starts_with "/catalogue/pdf/"`
   → **Cache Everything**, Edge TTL **1 day**.
4. **`Public HTML (respect origin)`** — match:
   `(http.request.uri.path in {"/" "/indoors/" "/outdoors/" "/shreemsports/" "/about/" "/safety-standards/" "/testimonials/" "/contact/" "/privacy-policy/" "/terms-of-service/" "/sitemap.xml" "/robots.txt" "/BingSiteAuth.xml"} or http.request.uri.path starts_with "/product/" or starts_with "/search" or starts_with "/view-all-products")`
   → **Cache Everything**, TTL **Respect origin** (Django already sends `s-maxage`).

> Safety: Cloudflare never caches responses with `Set-Cookie`, and authenticated pages
> already return `Cache-Control: private, no-store` — so rule 1 is a belt-and-braces
> guard, and private data can never be served from cache.

### Part B — Hostinger (DNS handover)

**B1. Before changing anything**
1. Log in to Hostinger → **hPanel → Domains → akidsenterprise.com → DNS/Nameservers**.
2. **Copy every existing DNS record** (MX, SPF, DKIM, DMARC, TXT, A, CNAME) into a
   notes file — this is your rollback reference. Find the **DKIM selector** under
   Hostinger **Emails → domain → DNS/Email records** (or hPanel mail) and copy its TXT
   value into Cloudflare (A2, last row) **before** the switch.

**B2. Change nameservers**
1. In Cloudflare **Overview**, copy the two assigned nameservers
   (e.g. `xxx.ns.cloudflare.com` and `yyy.ns.cloudflare.com`).
2. In Hostinger DNS settings, replace `nebula.dns-parking.com` / `aurora.dns-parking.com`
   with the two Cloudflare nameservers. **Save.**
3. Do NOT delete anything else at Hostinger — Cloudflare now serves DNS.

**B3. Wait for propagation**
- Cloudflare **Overview** shows **Pending Nameserver Update → Active** (minutes to 48 h;
  usually under an hour). Site and email keep working throughout (MX unchanged).

**B4. Go live proxied**
- Once Cloudflare shows the zone **Active**, confirm A + `www` records in Cloudflare DNS
  are **Proxied (orange)**. If they are grey, toggle them to orange now.

### Part C — Post-switch verification (you can run these)

```bash
nslookup -type=NS akidsenterprise.com          # → should show *.ns.cloudflare.com
curl -sI https://www.akidsenterprise.com/       # → look for: cf-ray: ... server: cloudflare
curl -sI https://akidsenterprise.com/           # → 308 redirect to https://www.akidsenterprise.com/
curl -sI https://www.akidsenterprise.com/login/ # → cf-cache-status: BYPASS/DYNAMIC (never HIT)
```
- First `curl` to `/` twice → second shows `cf-cache-status: HIT` (public HTML cached).
- Browse the site normally: home, product, login, signup, chat, inquiry, cart,
  admin-panel, catalogue PDF.
- **Email check:** send a message to info@akidsenterprise.com and confirm it arrives
  (Hostinger webmail); also send one from it.
- **Vercel dashboard:** function invocations / origin transfer should stay low.
- **Cloudflare Analytics + Security Events:** watch blocked/challenged requests, and
  confirm `meta-externalagent` / probe paths are being stopped before Vercel.

### Part D — Rollback quick reference (if anything misbehaves)

| Problem | Fix (Cloudflare-only, instant) |
|---|---|
| Real users blocked | Bot Fight Mode → OFF; rate-limit action → OFF/raise threshold |
| Cache serving something wrong | Delete Cache Rules (or set rule 1 wider); purge cache: Caching → Purge Everything |
| Anything broken | DNS → set A + www to **DNS-only (grey)** — Cloudflare layers off, site served straight from Vercel |
| Worst case | Change nameservers back to Hostinger (`nebula`/`aurora.dns-parking.com`); delete Cloudflare zone |

Vercel and Django are never touched during rollback — they were never modified.
