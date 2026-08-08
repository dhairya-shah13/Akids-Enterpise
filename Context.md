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

## Open Audit Findings
- [Resolved] Duplicate home route mapping on URL `/` bypassed `views.home_view` by calling static `TemplateView.as_view` directly.
- [Resolved] Lack of unique meta descriptions on category listing and company static pages.
- [Resolved] Missing product-specific JSON-LD structured data on `/product/<id>/` pages.
- [Resolved] Conflicting brand name usage (`Little Fingers` vs `A kids India`) in templates.
- [Resolved] Server Error (500) on `/sitemap.xml` fixed by returning QuerySet rather than generator iterator and setting HTTPS protocol.
- [Resolved] Created physical asset `frontend/static/robots.txt` and routed via `vercel.json` edge CDN and Django `robots_txt` view.
- [Resolved] Injected `BreadcrumbList` JSON-LD schema across company pages and product detail templates.

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
