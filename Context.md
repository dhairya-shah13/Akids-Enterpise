# Project Context

## Brand
- **Name**: A kids India
- **Offering**: Kindergarten Furniture, Playground Equipment & Sports Gear
- **Audience**: Schools, daycare centres, and homes in India
- **Tone**: Trustworthy, safe, durable, playful, and professional

## Project Profile
- **Primary type**: Ecommerce (preschool furniture, playgrounds, sports equipment)
- **Secondary type**: none
- **Local profile applies**: no (nationwide manufacturer/supplier)
- **International profile applies**: no (serves the Indian market)
- **Page-type → template map**:
  - `/` (Home) → Template B (Category / Home)
  - `/indoors/` → Template B (Category)
  - `/outdoors/` → Template B (Category)
  - `/shreemsports/` → Template B (Category)
  - `/about/`, `/safety-standards/`, `/testimonials/`, `/contact/`, `/privacy-policy/`, `/terms-of-service/` → `company_page.html` Template
  - `/product/<id>/` → Template B (Product Detail)

## Keyword Baseline
- `kindergarten furniture`: rank not ranking, intent commercial, locale en-IN, last checked 2026-08-08
- `educational playground equipment`: rank not ranking, intent commercial, locale en-IN, last checked 2026-08-08
- `classroom furniture India`: rank not ranking, intent commercial, locale en-IN, last checked 2026-08-08
- `kids sports gear`: rank not ranking, intent commercial, locale en-IN, last checked 2026-08-08

## Site Structure
- `/` (Home) | Purpose: Brand introduction and featured selections | Target Keyword: `A kids India` | Template: Category/Home
- `/indoors/` | Purpose: Category listing for indoor furniture | Target Keyword: `kindergarten furniture` | Template: Category Listing
- `/outdoors/` | Purpose: Category listing for playgrounds | Target Keyword: `playground equipment` | Template: Category Listing
- `/shreemsports/` | Purpose: Category listing for sports items | Target Keyword: `kids sports gear` | Template: Category Listing
- `/about/` | Purpose: Company background and values | Target Keyword: `about A kids` | Template: Company Page
- `/safety-standards/` | Purpose: Information on quality standards | Target Keyword: `safety standards` | Template: Company Page
- `/testimonials/` | Purpose: Customer reviews and quotes | Target Keyword: `testimonials` | Template: Company Page
- `/contact/` | Purpose: Contact info and quotes request | Target Keyword: `contact A kids` | Template: Company Page
- `/privacy-policy/` | Purpose: Privacy practices disclosure | Target Keyword: `privacy policy` | Template: Company Page
- `/terms-of-service/` | Purpose: Terms of use disclosure | Target Keyword: `terms of service` | Template: Company Page
- `/product/<id>/` | Purpose: Individual product detail | Target Keyword: product name | Template: Product Detail

## Topic Clusters
- **Indoor Cluster**:
  - Pillar: `/indoors/` (Indoor Carriage)
  - Clusters: `/product/<id>/` (Indoor products)
- **Outdoor Cluster**:
  - Pillar: `/outdoors/` (Outdoor Carriage)
  - Clusters: `/product/<id>/` (Outdoor products)
- **Sports Cluster**:
  - Pillar: `/shreemsports/` (Sports Carriage)
  - Clusters: `/product/<id>/` (Sports products)

## Audit Findings
- [APPROVED + PARTIALLY IMPLEMENTED 2026-08-11] Cloudflare outer-perimeter plan (`IMPLEMENTATIONPLAN.md`) approved by owner. The plan's only repository change (§7) is implemented: `ratelimit.client_ip()` prefers `CF-Connecting-IP` (Cloudflare overwrites client-supplied values; it APPENDS to XFF so the first hop is spoofable) with XFF-first-hop fallback; 3 new tests; full suite 66/66 pass. §13 OWNER RUNBOOK added (step-by-step Hostinger + Cloudflare dashboard actions: zone, DNS table incl. DKIM selector, SSL Full (strict), WAF Free Managed Ruleset + probe rule, Bot Fight Mode, 1 consolidated rate-limit rule, 4 cache rules, NS handover, verification curls, rollback). Remaining work is owner-executed via the runbook: Cloudflare zone + config, Hostinger NS change, post-switch verification.
- [PLANNED 2026-08-11] Cloudflare outer-perimeter integration audited and planned in `IMPLEMENTATIONPLAN.md` (awaiting owner approval — nothing applied). Owner choices: Cloudflare Free, full NS handover, Vercel Hobby, new CF account. Verified DNS: NS = Hostinger (`nebula/aurora.dns-parking.com`), apex A `216.198.79.1` = Vercel edge (308→www), www CNAME → Vercel DNS, MX/SPF = Hostinger, DMARC `p=none`, DKIM selector unknown (fetch from Hostinger panel), `akids-enterpise.vercel.app` live = direct-origin bypass. Free-plan constraints: 1 rate-limiting rule (7 POST endpoints consolidated into one 60/min Managed Challenge rule), basic Bot Fight Mode, Free Managed Ruleset only. Vercel Hobby: no Firewall custom rules / no Attack Challenge Mode → origin IP-lock impossible (documented; optional Pro upgrade later). One justified minimal code change proposed: `ratelimit.client_ip()` prefers `CF-Connecting-IP` (Cloudflare appends to XFF → first hop spoofable) + unit test. 4 cache rules planned: auth bypass / /static/* / /catalogue/pdf/* / public HTML respect-origin `s-maxage`. Rollback = grey-cloud DNS-only flip or NS revert.
- [CLEANED 2026-08-09] Owner-approved deletions (Category A/B, exception: admin_manual/user_manual kept): `homepage1.html`, root `logo.png`, `catalogues/` root PDFs (incl. `new Outdoor & Soft Play Components March 2026-.pdf`), `backend/products/management/commands/import_catalogue.py`, `docs/Audit.md`, `docs/context.md`, `docs/progress.md`, `docs/audit/audit-reports.md`, `docs/audit-report-2026-08-08.md`, `docs/audit/history/*.json`, `docs/CREDENTIALS_SETUP.md`, `ponytail/` gitlink, `implementationplan.md`. All byte-identical duplicates verified by md5; zero dangling references (only stale string: `views.py:546` error message still mentions deleted docs/CREDENTIALS_SETUP.md — cosmetic). 63 tests pass.
- [IMPLEMENTED 2026-08-09] `implementationplan.md` (repo root) WS-1..WS-5 approved and applied: edge 404 routes for probes + PDF edge routes (C1/H4), conditional csrftoken middleware + /api/csrf/ + s-maxage edge caching for anonymous GETs (C2/H5), view_all PII leak removed (C3), rate limits on login/signup/firebase/resend/change-password/chat/inquiry + DNS memoization (H1–H3/H6). No request loops or cron jobs found. Deployed; follow-up 404 edge caching shipped 2026-08-10 (below). Known: rate limits are per-instance (locmem) — Vercel Firewall rules recommended as global layer; pre-existing `/shreem_sports/view-all-products/` returns 404 (view accepts indoor/outdoor only); duplicate google_login/google_callback definitions in views.py are pre-existing dead code.
- [IMPLEMENTED 2026-08-10] Edge caching for 404 responses (follow-up to WS-1..WS-5): `custom_404` handler added to `backend/products/views.py` and registered via `handler404 = 'products.views.custom_404'` in `backend/little_fingers/urls.py`. Returns the 404 template with `Cache-Control: public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800` so Vercel serves missing/probe URLs from the edge instead of invoking a serverless function per request. Production deploy triggered (commit 3b3abe0).
- [CHANGED 2026-08-10] robots.txt iterated on production to curb crawler load, then reverted to a minimal file: on 2026-08-09 a temporary full block (`User-agent: * Disallow: /` + `User-agent: meta-externalagent Disallow: /`) was added and removed within the hour ("bots crawling stopped", 2026-08-10). Final state: single `User-agent: *` + `Allow: /`, disallows for /admin/, /admin-panel/, /login/, /logout/, /cart/, /checkout/, /profile/, /search-results/, `/*?*session=`, plus sitemap line. NOTE: the explicit per-crawler sections from the 2026-08-08 SEO.md §8 implementation (Googlebot, Bingbot, GPTBot, ChatGPT-User, Google-Extended, PerplexityBot, ClaudeBot, anthropic-ai) were dropped in the revert — AI crawlers remain permitted implicitly via `User-agent: *` (no guardrail violation), but explicit Allow blocks should be restored for AI-citation eligibility.
- [2026-08-08] Minor: Google Analytics 4 (gtag.js, property G-W0ZED4768G) installed site-wide in `base.html`; IndexNow push submitted site URLs for Bing/Yandex/Seznam discovery; padded square logo referenced in `base.html` so the search-result favicon renders correctly.

## Open Audit Findings
- [Resolved] Vercel function limits exhausted by bot traffic (1.7M invocations). Implemented custom_404 handler in views.py with s-maxage caching to serve bot 404s from the edge network. Deployed to production 2026-08-10 (commit 797df90 + deploy trigger 3b3abe0).
- [Resolved] Duplicate home route mapping on URL `/` bypassed `views.home_view` by calling static `TemplateView.as_view` directly.
- [Resolved] Lack of unique meta descriptions on category listing and company static pages.
- [Resolved] Missing product-specific JSON-LD structured data on `/product/<id>/` pages.
- [Resolved] Conflicting brand name usage (`Little Fingers` vs `A kids India`) in templates.
- [Resolved] Server Error (500) on `/sitemap.xml` fixed by returning QuerySet rather than generator iterator and setting HTTPS protocol.
- [Resolved] Created physical asset `frontend/static/robots.txt` and routed via `vercel.json` edge CDN and Django `robots_txt` view.
- [Resolved] Injected `BreadcrumbList` JSON-LD schema across company pages and product detail templates.
- [Open] robots.txt lost its explicit AI-crawler Allow sections (GPTBot, ChatGPT-User, Google-Extended, PerplexityBot, ClaudeBot, anthropic-ai) during the 2026-08-10 "bots crawling stopped" revert. Not a blanket block — `User-agent: *` still permits all crawlers — but per SEO.md §8 the explicit Allow blocks should be restored to keep the site AI-citation eligible.
- [Open] Direct-origin bypass: `akids-enterpise.vercel.app` serves the full site and bypasses Cloudflare (or any CDN in front of the domain). Not fixable on Vercel Hobby (no Attack Challenge Mode / Firewall custom rules). Existing mitigations remain: Django rate limits + CSRF, `custom_404` edge caching, `vercel.json` edge-404 routes. Optional Vercel Pro upgrade for true origin lock (Firewall IP allowlist of Cloudflare ranges + Attack Challenge Mode) — see IMPLEMENTATIONPLAN.md §6.

## Entity Profile
- **Verified external profiles**:
  - Website: https://akidsenterprise.com
  - Email: info@akidsenterprise.com
  - Phone: +91 7433 026 008

## Backlink Profile
- Referring domains: 0 (development)
- DA-DR: 0
- Anchor-text distribution: none

## Review / Reputation Status
- Self-hosted testimonials page: `/testimonials/`

## Content Decay Watchlist
- None (initial launch)

## Competitive Gap Watchlist
- None

## AI Citation Log
- None

## Analytics Baseline
- Analytics stack: Google Analytics 4 (gtag.js, property G-W0ZED4768G) installed site-wide in `base.html` (2026-08-08).
- Organic Sessions: 0
- Conversion Rate: 0%

## Content Backlog
- None

## Architecture Overview
- **Backend Stack**: Django 6.x, PostgreSQL / SQLite
- **Frontend Stack**: Tailwind CSS, HTML5, Vanilla JavaScript
- **Core Conventions**:
  - Static views use cached pages (`@cache_page(60 * 30)`).
  - Clean separation between Django models and templates.
  - Consistent H1-H3 semantics across templates.
