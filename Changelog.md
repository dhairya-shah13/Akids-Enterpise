# Changelog

## [2026-08-10 10:34]

### [Category: Dev] — Added Edge Caching for 404 responses to stop Vercel Abuse
What changed: Added `custom_404` handler in `backend/products/views.py` and registered it in `backend/little_fingers/urls.py` via `handler404 = 'products.views.custom_404'`. The custom handler returns a 404 response with `Cache-Control: public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800` headers.
Why: To prevent bots from exhausting Vercel free limits (1.7M function invocations). By setting edge caching headers on 404s, Vercel caches the bogus URL responses at the edge instead of routing every missing file request to the Python backend.
Bug fixed: Vercel usage spike / Function Invocations exhaustion.
Root cause: Django's default 404 handler does not set `Cache-Control` edge caching headers, causing every missing route to invoke a serverless function.

## [2026-08-09 23:31]

### [Category: Dev] — Safe project cleanup: deleted approved Category A/B files
What changed: Per owner approval ("Delete Category A, B" with exception of admin/user manuals), removed via `git rm` (fully recoverable from git history): Category A zero-risk files — `homepage1.html` (orphaned homepage mockup), root `logo.png` (byte-identical duplicate of `frontend/static/images/logo.png`), `catalogues/Indoor Catalogue March 2026-.pdf` and `catalogues/Outdoor Catalogue March 2026-.pdf` (byte-identical duplicates of the WS-4 static copies). Category B files — `catalogues/new Outdoor & Soft Play Components March 2026-.pdf` (never served, only a source doc), `backend/products/management/commands/import_catalogue.py` (dev-only command, zero references), and docs/ files `Audit.md`, `context.md`, `progress.md`, `audit/audit-reports.md`, `audit-report-2026-08-08.md`, `audit/history/2026-08-01.json`, `audit/history/2026-08-01-rescan.json`, `CREDENTIALS_SETUP.md`. Also removed the `ponytail/` gitlink submodule (git rm -r --cached + working dir) and the untracked `implementationplan.md`. Exception honored: `docs/admin_manual.md` and `docs/user_manual.md` retained. Reference-checked every deletion (imports/templates/routes/static/vercel.json) — no dangling references; remaining vercel.json edge-404 routes for /homepage1.html, /logo.png, /ponytail are intentional and need no file. Validation: py_compile OK, `manage.py check` no issues, full test suite 63 tests OK.
Why: Owner-approved read-only cleanup audit (Category A = zero-risk deletions, Category B = human-reviewed deletions) to slim the repo before the production push and Vercel courtesy unblock.
Bug fixed (if applicable): n/a.
Root cause (if applicable): n/a.

## [2026-08-09 23:35]

### [Category: Dev] — Production traffic/bot-abuse mitigation implemented (WS-1..WS-5, approved plan)
What changed: Implemented implementationplan.md WS-1..WS-5. WS-1: vercel.json edge `status:404` routes for probe paths (/wp-admin/, /wp-login.php, /xmlrpc.php, /.env, /.git, /config, /phpmyadmin, /etc, /backend/, /server-status, /actuator, /wp-json, /wordpress, /homepage1.html, /logo.png, /.claude, /ponytail), /favicon.ico route, and edge route for /catalogue/pdf/(indoor|outdoor)/ serving static copies with immutable cache. WS-2: CsrfCookieBootstrapMiddleware now sets csrftoken only when the client lacks it (enables Vercel edge caching); new GET /api/csrf/ endpoint; main.js ensureCsrf() lazy fallback before chat/inquiry POSTs; public_cache_control decorator (s-maxage for anonymous GET, private,no-store otherwise) applied to home/category/product/search/view_all; company_page cache reduced 30m->5m + s-maxage; api_search_suggestions + sitemap cached; view_all_products cache_page removed (was leaking logged-in user PII via shared cache — C3), product_codes list cached instead; admin dashboard updateInquiryStatus reloads via loadInquiries() + tab badge sync instead of full-page re-fetch. WS-3: new ratelimit.py (dependency-free, Django cache) with per-IP limits on login 10/min, signup 5/5min, firebase_login 5/5min, resend_verification 3/5min, change_password 10/min, chat_api 10/min, submit_inquiry 10/5min; signup DNS check memoized (lru_cache). WS-4: serve_catalogue_pdf repointed to frontend/static/catalogues copies (md5-verified identical) with immutable cache header. WS-5: 8 new tests (csrf endpoint, rate limits incl. signup regression, view_all PII guard); full suite 63 tests pass; dev smoke tests pass (routes 200, anonymous s-maxage, authenticated private/no-store, login 302, rate limit 429/error after threshold, CSRF 403 for cookie-less POSTs, PDF headers).
Why: Owner-approved plan to stop Vercel usage exhaustion (1.7M function invocations, 30GB origin transfer) from catch-all routing + blocked edge caching + un-cached public pages + unlimited expensive endpoints, while preserving all functionality, auth, CSRF, API contracts, and schema.

## [2026-08-09 22:55]

### [Category: Dev] — Production traffic / bot-abuse / request-loop audit + implementation plan
What changed: Performed a full repository audit (routing, middleware, views, templates, static assets, tests, Vercel config) for the production traffic spike (≈1.7M function invocations, ~30 GB origin transfer) and produced `implementationplan.md` at the repo root. No code changed — the plan awaits owner approval per RULES.md §2. Root causes identified: (C1) vercel.json catch-all sends every request (incl. 404s/probes) into the WSGI function; (C2) CsrfCookieBootstrapMiddleware forces Set-Cookie on every response, blocking Vercel edge caching; (C3) view_all_products @cache_page(60*5) leaks logged-in user prefill PII across users; plus missing rate limits on login/signup/chat/inquiry/firebase endpoints, catalogue PDFs streamed through the function, and uncached public pages. No request loops, polling, or cron jobs found.
Why: Owner requested a RULES.md-compliant audit + implementation plan before any fix, to keep production online after a Vercel courtesy unblock without re-exhausting limits.

## [BingSiteAuth.xml XML Verification Route] — 2026-08-08, 15:05
**Type:** Technical
**Page(s):** /BingSiteAuth.xml
**Summary:** Configured `/BingSiteAuth.xml` route across Vercel Edge CDN (`vercel.json`), static assets (`frontend/static/BingSiteAuth.xml`), and Django view (`backend/products/views.py` & `urls.py`) to serve Bing Webmaster verification XML payload cleanly without 404 errors.
**Keyword(s) targeted:** N/A
**Files touched:** frontend/static/BingSiteAuth.xml, vercel.json, backend/products/views.py, backend/products/urls.py

## [Bing Webmaster Tools Verification] — 2026-08-08, 15:01
**Type:** Technical
**Page(s):** All (site-wide via base.html)
**Summary:** Added Bing Webmaster Tools site verification meta tag (`msvalidate.01`) to enable domain verification for Bing search engine indexing.
**Keyword(s) targeted:** N/A
**Files touched:** frontend/templates/base.html

## [Physical robots.txt Asset & Breadcrumb JSON-LD Schema] — 2026-08-08, 14:55
**Type:** Technical | Schema | Robots | Audit
**Page(s):** /robots.txt, site-wide
**Summary:** Created physical `frontend/static/robots.txt` asset per Section 8 of SEO.md, added Vercel edge route in vercel.json, bound Django's `robots_txt` view to serve the static asset, injected `BreadcrumbList` JSON-LD schema across template graphs, and published audit report at docs/audit-report-2026-08-08.md.
**Keyword(s) targeted:** N/A
**Files touched:** frontend/static/robots.txt, vercel.json, backend/products/views.py, frontend/templates/products/company_page.html, frontend/templates/products/product_detail.html, docs/audit-report-2026-08-08.md, Context.md

### What changed
- Created physical asset `frontend/static/robots.txt` with explicit search engine & AI crawler permissions (`Googlebot`, `Bingbot`, `GPTBot`, `ChatGPT-User`, `Google-Extended`, `PerplexityBot`, `ClaudeBot`, `anthropic-ai`).
- Added edge CDN route `/robots.txt` -> `frontend/static/robots.txt` in `vercel.json`.
- Updated `robots_txt` view in `backend/products/views.py` to read directly from `frontend/static/robots.txt`.
- Injected `BreadcrumbList` JSON-LD schema into `company_page.html` and `product_detail.html`.
- Generated `docs/audit-report-2026-08-08.md` and updated `Context.md`.

### Why
To execute the complete `SEO.md` (RankSynth) specification and satisfy repository governance rules in `RULES.md`.

## [Fix Broken Sitemap Generation] — 2026-08-08, 14:45
**Type:** Technical
**Page(s):** /sitemap.xml
**Summary:** Fixed Server Error (500) on `/sitemap.xml` caused by `ProductSitemap.items()` returning a generator via `.iterator()`, which Django's sitemap paginator cannot measure with `len()`. Replaced with an ordered QuerySet and enforced HTTPS protocol on all sitemap URLs.
**Keyword(s) targeted:** N/A
**Files touched:** backend/products/views.py

### What changed
- Removed `.iterator()` from `ProductSitemap.items()` and replaced with `.order_by('id')` to return a standard QuerySet.
- Added `protocol = 'https'` to both `ProductSitemap` and `StaticViewSitemap` to ensure all sitemap URLs use HTTPS.

### Why
The sitemap endpoint was returning a 500 error in production, blocking Google Search Console submission.

### Bug fixed
`/sitemap.xml` returned `TypeError: object of type 'generator' has no len()` and a 500 Server Error.

### Root cause
`ProductSitemap.items()` used `.iterator()` which returns a generator. Django's `Paginator` calls `len()` on the items list, which is unsupported on generators.

## [Google Search Console Verification] — 2026-08-08, 13:52
**Type:** Technical
**Page(s):** All (site-wide via base.html)
**Summary:** Added Google Search Console site verification meta tag to enable domain ownership verification for akidsenterprise.com.
**Keyword(s) targeted:** N/A
**Files touched:** frontend/templates/base.html

## [SEO/AEO/GEO Optimization & Naming Alignment] — 2026-08-08, 13:10
**Type:** Technical | Schema | Robots | Sitemap
**Page(s):** /, /robots.txt, /sitemap.xml, /indoors/, /outdoors/, /shreemsports/, /about/, /safety-standards/, /testimonials/, /contact/, /privacy-policy/, /terms-of-service/, /product/<id>/
**Summary:** Implemented the RankSynth SEO checklist: updated robots.txt crawler permissions, updated sitemap paths, removed duplicate static home route bypass, resolved title and description duplication issues across all static and product pages, and injected Product JSON-LD schema.
**Keyword(s) targeted:** A kids India, kindergarten furniture, playground equipment, kids sports gear
**Files touched:** backend/products/urls.py, backend/products/views.py, frontend/templates/products/company_page.html, frontend/templates/products/listing.html, frontend/templates/products/outdoors.html, frontend/templates/products/shreemsports.html, frontend/templates/products/product_detail.html, all other product templates for branding.

### What changed
- Commented out the duplicate home route `/` mapping to `TemplateView` in `backend/products/urls.py`, allowing the dynamic `views.home_view` to execute and display featured products.
- Added `privacy_policy` and `terms_of_service` pages to the sitemap generator in `backend/products/views.py`.
- Rewrote the `robots_txt` view in `backend/products/views.py` to allow and manage AI crawler bots explicitly.
- Added `meta_description` metadata to static pages inside `COMPANY_PAGES` in `backend/products/views.py`, and updated `company_page.html` to inject these values dynamically.
- Overrode title, meta description, and social graph meta tags in listing pages and static pages.
- Injected Product JSON-LD structured data into `product_detail.html`.
- Updated site-wide template branding from `Little Fingers` to `A kids India` for consistency.

### Why
To execute the SEO/AEO/GEO optimization prompt from `SEO.md` and satisfy the technical/brand requirements.

### Bug fixed
Duplicate home route bypassed dynamic home rendering (no featured products displayed on the home page).
Duplicate page titles/descriptions and missing product schema.

### Root cause
Overlapping routes in `urls.py` and missing template block overrides for titles/metadata.
