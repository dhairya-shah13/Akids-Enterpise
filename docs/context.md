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
│
├── docs/                       # Project Documentation
│   ├── context.md              # THIS FILE (Moved from root)
│   ├── Audit.md                # Universal Deep-Scan Audit Instructions
│   ├── CREDENTIALS_SETUP.md    # Guide for setting up Google/Firebase credentials
│   ├── progress.md             # High-level project progress tracking
│   └── audit/                  # Generated Audit Reports
│       ├── latest-report.md    # Most recent deep-scan audit report
│       └── history/            # Historical audit scorecards (.json)
│
├── backend/                    # Django backend
│   ├── manage.py               # Django management script
│   ├── little_fingers/         # Django project settings package
│   └── products/               # Products Django app (models, views, logic)
│
├── frontend/                   # Django templates & static assets
│   ├── static/                 # CSS (Tailwind + Theme), JS (main.js), Images, Catalogues
│   └── templates/              # Django templates (base, home, listing, detail, admin, etc.)
│
└── ponytail/                   # Ponytail AI agent framework (installed)
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
- **Shopping Cart & Checkout**: Stock-aware, atomic transactions, 18% GST computation.
- **Inquiry System**: Batch catalog quotes, WhatsApp integration, WON/LOST closure outcomes.
- **Admin HQ**: SPA-style full-width dashboard for managing products, orders (no-scroll 9-column table with `table-fixed` layout), and inquiries with visual reports.
- **User Profile**: Saved addresses, customizable avatars, 30-day username cooldown.
- **Security**: Google OAuth 2.0 and Firebase Passwordless Sign-In (Magic Links).

---

## 📋 Progress Made on Date and Time (2026-08-01 12:28)

### Admin HQ — Full-Width Layout & Orders Table No-Scroll Fix

Removed the side gaps in the Admin HQ page and fixed the Orders table so all 9 columns are visible without horizontal scrolling.

| **Layout** | Changed `max-w-7xl` → `max-w-full` on banner and grid containers | `admin_dashboard.html` |
| **Orders Table** | Removed `overflow-x-auto` and `min-w-[1200px]`, switched to `table-fixed` with %-based column widths | `admin_dashboard.html` |
| **Compact Styling** | Reduced padding (`p-4` → `px-2 py-3`), shrank fonts, added `truncate` with tooltips on text-heavy columns | `admin_dashboard.html` |
| **Contact Links** | Wired footer email and phone icon links to `mailto:info@akidsenterprise.com` and `tel:+917433026008` | `base.html` |
| **Shreem Sports** | Removed search and product list/catalog sections (Coming Soon) | `shreemsports.html` |
| **Navbar** | Removed brand text and enlarged the `logo.png` image size | `base.html` |
| **Search Suggestions** | Implemented `/api/search-suggestions/` endpoint and route | `views.py`, `urls.py` |
| **Documentation** | Updated progress and context docs | `docs/progress.md`, `docs/context.md` |

---

*Last Updated: 2026-08-01 12:40. Maintainer: AI Agent. Please update this document whenever model schemas, workflows, or views undergo changes.*
