# A kids / Little Fingers - Project Context Document

This document provides a comprehensive overview of the **A kids (Little Fingers) / Akids Enterprise** e-commerce platform for playground equipment, educational furniture, sports gear, and spare parts. It is designed to help developers and AI agents quickly understand the codebase, including all backend models, views, templates, and CSS system.

---

## 📁 Complete Project Structure

```
Akids-Enterpise/
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies (Django 6+, psycopg, pillow, reportlab, etc.)
├── vercel.json                 # Vercel deployment configuration (Python WSGI + static)
├── .vercelignore               # Vercel ignore configuration
├── package.json                # Node.js config + Tailwind CSS build script
├── tailwind.config.js          # Tailwind CSS theme configuration (Antigravity color palette)
├── uv.lock                     # UV package manager lockfile
├── pyproject.toml              # Python project metadata
├── homepage1.html              # Standalone homepage design preview (not routed in the app)
│
├── docs/                       # Project Documentation
│   ├── context.md              # THIS FILE (Moved from root)
│   ├── admin_manual.md         # Admin HQ Manual (flowcharts, field guides, examples)
│   ├── user_manual.md          # Customer/User Manual (storefront, cart, checkout)
│   ├── Audit.md                # Universal Deep-Scan Audit Instructions
│   ├── CREDENTIALS_SETUP.md    # Guide for setting up Google/Firebase credentials
│   ├── progress.md             # High-level project progress tracking
│   └── audit/                  # Generated Audit Reports
│       ├── audit-reports.md    # Running audit history (oldest first)
│       └── history/            # Historical audit scorecards (.json)
│
├── backend/                    # Django backend
│   ├── manage.py               # Django management script
│   ├── little_fingers/         # Django project settings package
│   └── products/               # Products Django app (models, views, logic)
│       ├── constants.py        # PRODUCT_COLOURS palette (name → hex)
│       ├── utils.py            # calculate_gst() — shared GST math (single source of truth)
│       ├── search.py           # Search engine & suggestions
│       ├── pdf_generator.py    # ReportLab invoice PDFs (18% GST breakup)
│       ├── models.py           # Product, Inquiry, Order, OrderItem, Specs, UserProfile, Address
│       └── management/commands/create_admin_from_env.py
│
├── frontend/                   # Django templates & static assets
│   ├── static/                 # CSS (Tailwind + Theme), JS (main.js), Images, Catalogues
│   └── templates/              # Django templates (base, home, listing, detail, admin, etc.)
```

---

## 🔍 Repository Audit & Security Status (Last Run: 2026-08-01 — Re-Scan)

A "Universal Deep-Scan" repository audit was performed to evaluate production readiness, security, and financial integrity. Following the **Security & Financial Integrity Remediation Pass**, the overall score was raised from **75 (B)** to **97 (A)**.

| Overall Grade | Critical Findings | High Findings | Medium Findings | Top Risk |
|---|---|---|---|---|
| **A (97/100)** | 0 (1 accepted exception) | 0 | 0 (2 Low review items) | Razorpay payment integration (accepted deferral) |

### **Remediated (previously Major Risks):**
1.  ✅ **Critical: Hardcoded Admin Defaults** — Removed entirely. Admin is now a real Django superuser created by `python manage.py create_admin_from_env --noinput` (runs in `vercel.json` buildCommand). Production fails fast if `ADMIN_EMAIL`/`ADMIN_PASSWORD`/`SECRET_KEY` are missing.
2.  **Accepted Exception: Unverified Order Creation** — Simulated test-mode checkout remains **intentionally** (client sign-off pending before Razorpay + webhook integration). Stock deduction is race-safe (`select_for_update` in a transaction). Documented as an accepted, deliberate deferral in the audit — not a defect.
3.  ✅ **High: IDOR in Order Success (and invoice)** — Ownership-filtered 404, no existence leak. Staff may view any order.
4.  ✅ **High: Tax Calculation Inconsistency** — Unified `products/utils.py::calculate_gst()`; `Order.subtotal_amount`/`gst_amount` stored explicitly; backfill migration 0019; PDF invoice uses the same math.
5.  ✅ **High: Insecure Host/Secret Key** — `ALLOWED_HOSTS` from env (default includes production + localhost + `*.vercel.app`); `SECRET_KEY` required from env with no fallback in production.

### **Remaining Low / Review Items:**
1.  **Login brute-force throttling** — recommend rate limiting before public launch.
2.  **CSP `unsafe-inline`** — accepted tradeoff for inline template scripts; tighten with nonces in a future pass.
3.  **Operational:** add `SECRET_KEY`, `DJANGO_DEBUG=False`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` to Vercel environment variables.

*Full details are located in `docs/audit/audit-reports.md` (running history, oldest first).*

---

## 🛠 Technology Stack

| Layer | Technology | Version/Notes |
|-------|------------|---------------|
| **Backend Framework** | Django | 6.0.5+ |
| **Database (Prod)** | PostgreSQL (Supabase) | Via `DATABASE_URL` env var |
| **ORM** | Django ORM | - |
| **PDF Generation** | ReportLab | 4.4.0+ (Invoices with 18% GST breakup) |
| **AI Chat** | Groq API (Llama 3.3/3.1) | Mohanlal mascot personality |
| **Deployment** | Vercel (Python WSGI) | `@vercel/python` + `@vercel/static` |
| **Frontend** | Django Templates + Tailwind | No JS framework, Vanilla JS for interactivity |
| **CSS Framework** | Tailwind CSS | v3.4.19 |

---

## 🔐 Environment Variables (`backend/.env`)

> **Single canonical `.env`:** `backend/.env`. The old root `.env` was consolidated into it on 2026-08-01 (it pointed at a stale Supabase host whose credentials failed auth) and removed.

- **SECRET_KEY**: Django secret key (required in production; generated and stored in `backend/.env`).
- **DJANGO_DEBUG**: `True` locally (default), `False` in production (Vercel).
- **ADMIN_EMAIL/ADMIN_PASSWORD**: Used by `create_admin_from_env` to bootstrap the Django superuser.
- **ALLOWED_HOSTS**: Comma-separated; defaults to production domains + `localhost` + `*.vercel.app`.
- **DATABASE_URL**: Supabase PostgreSQL.
- **GROQ_API_KEY**: For Mohanlal AI Chat.
- **WHATSAPP_NUMBER**: Target for catalog quote redirects (defaults to the business hotline).
- **GOOGLE_OAUTH_CLIENT_ID/SECRET**: For Google Sign-In.
- **FIREBASE_API_KEY**: For Passwordless Sign-In links.

---

## 🌐 URL Routing & Feature Logic

The application features a robust e-commerce and inquiry workflow:
- **Shopping Cart & Checkout**: Stock-aware, atomic transactions, 18% GST computation. Cart entries are variant-keyed as `<product_pk>::<colour>::<dimension>` when a product has colours and/or dimension specs; colour/dimension badges flow through cart → checkout → order → invoice PDF.
- **Product Variants**: Products can define colour swatches (14-name palette from `constants.py`), class/age-group specs, and dimension specs (with group_label, component, length, width, height as text fields, unit, notes). Storefront pickers on the product detail page enforce selection before add-to-cart; the order item snapshots the chosen colour & dimension.
- **Inquiry System**: Batch catalog quotes, WhatsApp integration, WON/LOST closure outcomes.
- **Admin HQ**: SPA-style full-width dashboard for managing products (including colour + spec editors), orders (no-scroll 9-column table with `table-fixed` layout), and inquiries with visual reports.
- **User Profile**: Saved addresses, customizable avatars, 30-day username cooldown.
- **Security**: Google OAuth 2.0 and Firebase Passwordless Sign-In (Magic Links).

---

## 📋 Progress Made on Date and Time (2026-08-02 14:28)

### Product Detail Page — Specs Layout Optimization

Reordered the product detail page sections so **Age Group Specifications** and **Product Dimensions** appear before the **Description** card. Both spec tables are now displayed **side by side** in a responsive 2-column grid (`md:grid-cols-2`) to reduce vertical space. On mobile they stack vertically.

| # | Change | Details |
|---|--------|---------|
| 1 | Section reorder | Age Group Specs → Product Dimensions → Description (previously Description was first) |
| 2 | Side-by-side layout | Both spec cards wrapped in `grid grid-cols-1 md:grid-cols-2 gap-6` container |
| 3 | Compact padding | Reduced card padding from `p-8` to `p-6`, heading sizes from `text-xl` to `text-lg` |

**File Modified**: `frontend/templates/products/product_detail.html`

---

## 📋 Progress Made on Date and Time (2026-08-02 08:00)

### Product Colours, Class/Age Specs & Dimension Variants (Catalogue-Aligned)

Implemented full product-variant support — **colours**, **class/age-group specs**, and **dimension specs** — wired end-to-end from admin product entry → storefront pickers → cart/checkout → orders → invoice PDF. Dimension fields are `CharField` (text) to support ranges (`59-90`), diameters (`D/Dia 90`), and adjustable heights.

| # | Feature / Change | Status | Implementation Details |
|---|------------------|--------|------------------------|
| **1** | `Product.colours` JSONField | **COMPLETED** | Stores an ordered list of colour names. Model helpers: `colours_with_hex` (name → hex via `PRODUCT_COLOURS`), `colours_json`, `get_class_specs_json()`, `get_dimension_specs_json()`. |
| **2** | `ProductClassSpec` model | **COMPLETED** | `class_label`, `age_min`, `age_max`, `order`; FK `product.class_specs`. Powers the Age Group table on storefront + product cards. |
| **3** | `ProductDimensionSpec` model | **COMPLETED** | `group_label` (optional), `component` (optional), `length` (CharField, required), `width` (CharField, optional), `height` (CharField, optional), `unit` (cm/inch/mm/ft), `notes` (optional), `order`; FK `product.dimension_specs`. |
| **4** | Order item variant snapshot | **COMPLETED** | `OrderItem.colour` + `OrderItem.dimension` CharFields capture the chosen variant at purchase time. |
| **5** | Colour palette constants | **COMPLETED** | New `constants.py` with 14 colours → hex. |
| **6** | Admin add/edit product | **COMPLETED** | Swatch picker with "No Colour" toggle, dynamic Class/Age rows, dynamic Dimension rows (with Group Label, Component, Notes columns); validation toasts; specs recreated (delete + insert) on edit. |
| **7** | Product detail pickers | **COMPLETED** | Colour swatch selector + dimension selector with component labels, Age Group & Dimensions detail cards. |
| **8** | Product card mini-specs | **COMPLETED** | Static colour swatch dots + compact Class/Age and Dimension tables with component labels. |
| **9** | Cart / checkout / profile badges | **COMPLETED** | Colour & dimension chips; cart keys `pk::colour::dimension`. |
| **10** | Invoice PDF variants | **COMPLETED** | Invoice item names render as `Name (Colour, Dimension)`. |
| **11** | Add-to-cart validation | **COMPLETED** | Redirect with `?toast=select-variants-required` when variants missing. |
| **12** | Tests | **COMPLETED** | 55 unit tests pass covering model fields, admin add with specs, cart variant operations, order + invoice. |
| **13** | Admin Manual | **COMPLETED** | `docs/admin_manual.md` — complete Admin HQ guide with flowcharts, field-by-field instructions, real-world catalogue examples, order/inquiry workflows. |
| **14** | User Manual | **COMPLETED** | `docs/user_manual.md` — complete customer storefront guide covering browsing, variants, cart, checkout, profile, inquiries. |

**Migrations**: `0020` (OrderItem.colour, Product.colours), `0021` (OrderItem.dimension, ProductClassSpec, ProductDimensionSpec), `0022` (component), `0023` (CharField conversion for L/W/H), `0024` (group_label, notes).

**Test Status**: All **55 unit tests pass** cleanly; `makemigrations --check` is clean.

---

*Last Updated: 2026-08-02 14:28. Maintainer: AI Agent. Please update this document whenever model schemas, workflows, or views undergo changes.*
