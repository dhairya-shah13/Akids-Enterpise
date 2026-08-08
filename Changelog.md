# Changelog

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
