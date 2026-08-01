## 📋 Progress Made on Date and Time (31 July 2026)

Completed 20 Client-Requested Changes across Homepage, Data Hygiene, Third-Party Auth, Admin HQ, User Profile, and Security.

### 1. Implementation Summary of 20 Requested Changes

| # | Feature / Change | Status | Implementation Details |
|---|------------------|--------|------------------------|
| **1** | Homepage: "Browse Products" smooth link | **COMPLETED** | Updated CTA button `href` to `#train-section` ("Our World") with smooth scrolling. |
| **2** | Homepage: Standout section headings | **COMPLETED** | Added colorful theme pill badges (`tangerine`, `sea`, `matcha`) and rounded accent underlines in `home.html`. |
| **3** | Homepage: Hero text order | **COMPLETED** | Reordered hero section so *"Safe. Durable. Playful."* appears first, followed by brand description. |
| **4** | Homepage: "Who We Serve" 3-card grid | **COMPLETED** | Transformed list into a responsive 3-column card grid with staggered intersection observer animations. |
| **5** | Homepage: Safety resources card container | **COMPLETED** | Styled safety resources block into a contained high-trust card container with icons & background gradients. |
| **6** | Contact Info: Hotline update | **COMPLETED** | Replaced `9924343003` with `+91 7433 026 008` across backend, templates, JS, PDF generator, `.env`, and docs. |
| **7** | Data Hygiene: Phone placeholders | **COMPLETED** | Standardized all form phone placeholders to `+91 9876543210` in `view_all.html` and `profile.html`. |
| **8** | Data Hygiene: Email placeholders | **COMPLETED** | Standardized form email placeholders to `yourname@example.com` in `login.html` and `signup.html`. |
| **9** | Contact Info: Business email update | **COMPLETED** | Updated contact email to `info@akidsenterprise.com` across backend and frontend templates. |
| **10** | Catalog: "All Play Equipment" feature | **SKIPPED (PER USER)** | Explicit directive: *"If that's the case leave all play equipment be don't do anything to it"*. Left intact. |
| **11** | Auth: Google Sign-In / Sign-Up | **COMPLETED** | Created credentials setup guide (`docs/CREDENTIALS_SETUP.md`), added `.env` keys, added Google button to `login.html`/`signup.html`, and added `google_login`/`google_callback` views. |
| **12** | Admin HQ: Product Stock input | **COMPLETED** | Added `stock` input field (default 10) to Add Product modal in `admin_dashboard.html` and updated `add_product` view. |
| **13** | Admin HQ: Edit Product modal & route | **COMPLETED** | Added Edit button to table row, Edit Product modal in `admin_dashboard.html`, and `edit_product` view + `/admin-panel/products/<pk>/edit/` route. |
| **14** | Admin HQ: Left-flush layout & hide chat FAB | **COMPLETED** | Adjusted sidebar container grid to left-flush (`260px 1fr`), tightened margins, and hidden Mohanlal chat FAB on admin pages. |
| **15** | Profile: Multi-color avatar picker | **COMPLETED** | Added `avatar_color` to `UserProfile`, migration `0017`, swatch picker UI in `profile.html`, and dynamic avatar background in `base.html`. |
| **16** | Profile: Saved addresses (max 5) + default | **COMPLETED** | Created `Address` model (max 5 cap), auto-migrated legacy `shipping_address`, added CRUD in `profile.html`, and pre-filled checkout shipping address. |
| **17** | Profile: 30-day username change cooldown | **COMPLETED** | Added `username_changed_at` to `UserProfile`, added 30-day non-stacking cooldown validation in `profile_view`, and added locked status UI. |
| **18** | Profile: Forgot Password link in sidebar | **COMPLETED** | Added "Forgot / Reset Password" entry point in account sidebar on `profile.html` linking to `set_password`. |
| **19** | Auth: Passwordless sign-in via Firebase link | **COMPLETED** | Added setup guide (`docs/CREDENTIALS_SETUP.md`), added `firebase_login` API view, added passwordless modal prompt, and created `set_password.html`. |
| **20** | Auth: Remove admin invitation helper text | **COMPLETED** | Removed *"Admin access requires school invitation."* text from `login.html`. |

### 2. Files Modified / Created
- `docs/CREDENTIALS_SETUP.md` (NEW)
- `frontend/templates/products/set_password.html` (NEW)
- `backend/products/migrations/0017_userprofile_avatar_color_and_more.py` (NEW)
- `backend/products/models.py`
- `backend/products/views.py`
- `backend/products/urls.py`
- `backend/products/tests.py`
- `frontend/templates/products/home.html`
- `frontend/templates/products/login.html`
- `frontend/templates/products/signup.html`
- `frontend/templates/products/admin_dashboard.html`
- `frontend/templates/products/profile.html`
- `frontend/templates/products/checkout.html`
- `frontend/templates/products/view_all.html`
- `frontend/templates/base.html`
- `backend/products/pdf_generator.py`
- `.env`
- `context.md`

**Test Status**: All 20 unit tests pass cleanly (`python backend/manage.py test products`).

---

## 📋 Progress Made on Date and Time (31 July 2026 21:22)

### Client Feature Enhancements: Profile Avatar Customization, Change Password Modal, & Forgot Password Flow

Completed further UI/UX and functional enhancements focusing on User Profile Avatar customization, Change Password modal security, Forgot Password flow redesign, and password visibility toggles.

#### 1. Implementation Breakdown

| Component | Feature / Enhancement | Implementation Details |
|-----------|-----------------------|------------------------|
| **Profile Avatar** | Expanded Color Choices | Supported 12 avatar background colors (`sea`, `tangerine`, `blush`, `matcha`, `coral`, `lavender`, `mint`, `midnight`, `emerald`, `sunset`, `berry`). Removed `butter`. Updated backend validation in `views.py`. |
| **Profile Avatar** | Modal Selection & Styling | Added dedicated Avatar Color modal with live preview, color name display, and clean card highlighting (active ring + tint). Removed checkmarks & palette references. |
| **Navbar Avatar** | Dynamic Navbar Avatar | Updated `base.html` top navbar profile button to dynamically reflect the logged-in user's `avatar_color` choice across the entire site. |
| **Account Profile** | Change Password Modal | Replaced sidebar "Forgot / Reset Password" link on `profile.html` with a **Change Password modal** prompt asking for Current Password, New Password, and Confirm New Password. |
| **Account Profile** | Password Verification Endpoint | Created `change_password_view` (`/auth/change-password/`) validating current password against `request.user.check_password()`, checking password match and 6-char length before saving and re-authenticates user. |
| **Auth / Login** | Inline Forgot Password Form | Replaced browser `prompt()` alert box on `login.html` with a smooth sliding inline Forgot Password form with email input and inline error handling. |
| **Auth / Login** | Firebase Passwordless Link Flow | Updated `firebase_login` view to trigger real Firebase email links via REST API (`sendOobCode`). Created `forgot_password_waiting.html` ("Check Your Email" waiting screen). Added `firebase_email_callback` (`/auth/firebase-callback/`) to verify link `oobCode` and log user in. |
| **Set Password Page** | Password Visibility Toggles | Added eye icon show/hide toggle buttons to both password fields on `set_password.html` along with minimum length instructions and success toast redirect to profile. |

#### 2. Modified & Created Files
- `frontend/templates/products/forgot_password_waiting.html` (NEW)
- `frontend/templates/products/profile.html`
- `frontend/templates/products/login.html`
- `frontend/templates/products/set_password.html`
- `frontend/templates/base.html`
- `backend/products/views.py`
- `backend/products/urls.py`
- `context.md`

---

## 📋 Progress Made on Date and Time (31 July 2026 21:52)

### Train Locomotive & Wooden Tire Redesign Across Pages

Completed the replacement of the CSS locomotive with the wooden train engine graphic (`train.png`) and updated train compartment wheels/tires across category pages to match the wooden tire design.

#### 1. Implementation Breakdown

| Component | Feature / Enhancement | Implementation Details |
|-----------|-----------------------|------------------------|
| **Train Engine** | Wooden Train Replacement | Replaced the CSS/icon train engine in `home.html` with the static image `train.png`. Positioned animated smoke puff (`train-engine-smoke`) over the wooden smokestack. Increased the engine size to `18rem` and adjusted vertical offset (`translateY(1.5rem)`) for perfect wheel track alignment. |
| **Train Wheels / Tires** | Wooden Tire Theme | Updated `.train-compartment` wheels in `theme.css` to feature radial-gradient wooden textures (`#FDE68A` to `#92400E`), walnut borders (`#78350F`), inner ring highlights, and warm realistic shadows to perfectly match `train.png`. |
| **Train Track & Sleeper** | Wooden Track Palette | Updated `.train-track` and sleeper gradients from black to warm wood tones (`#78350F`, `#92400E`). |
| **Category Pages** | Carriage Header Cards | Added `.page-carriage-card` to `listing.html` (Indoor), `outdoors.html` (Outdoor), `shreemsports.html` (Shreem Sports), and `view_all.html` (Catalogue Flow) to give category headers matching train carriage styling and wooden tires. Separated home page train carriages with distinct gaps and spanned the connectors (`.train-connector::after`) to bridge them cleanly. |

#### 2. Modified Files
- `frontend/templates/products/home.html`
- `frontend/static/css/theme.css`
- `frontend/templates/products/listing.html`
- `frontend/templates/products/outdoors.html`
- `frontend/templates/products/shreemsports.html`
- `frontend/templates/products/view_all.html`
- `frontend/templates/base.html`
- `docs/progress.md`
---

## 📋 Progress Made on Date and Time (1 August 2026)

### Security & Financial Integrity Remediation Pass (Re-Audit to 97/100 A)

Completed the full remediation pass targeting every audit dimension in `docs/audit/latest-report.md` (now `docs/audit/audit-reports.md`). Overall score raised from **75 (B)** to **97 (A)**.

| # | Feature / Change | Status | Implementation Details |
|---|------------------|--------|------------------------|
| **1** | Remove hardcoded admin credentials | **COMPLETED** | Removed `admin@gmail.com`/`123456` fallbacks from `_read_env_file` and `login_view`. Admin is now a real Django superuser bootstrapped via `create_admin_from_env` management command (run in `vercel.json` buildCommand). Zero occurrences remain in production code (grep-verified). |
| **2** | Fail-fast production startup | **COMPLETED** | `settings.py::validate_production_env()` raises `ImproperlyConfigured` in prod (`DJANGO_DEBUG=False`) when `SECRET_KEY`/`ADMIN_EMAIL`/`ADMIN_PASSWORD` are missing; logs a warning locally. |
| **3** | IDOR fix (order_success + invoice) | **COMPLETED** | Both views now filter by `request.user` with a 404 for non-owners (no existence leak). Staff can view any order. Invoice endpoint aligned to the same pattern (was 403). |
| **4** | GST-exclusive tax single source of truth | **COMPLETED** | New `products/utils.py::calculate_gst()`. `Order.subtotal_amount` + `gst_amount` fields (migration 0018). `checkout_view` + `pdf_generator.py` both call the shared function. |
| **5** | GST backfill for existing orders | **COMPLETED** | Migration 0019 recalculates subtotal/GST/total on every existing order using the GST-exclusive formula. Production Supabase (pooler) backfill **corrected 5 existing orders**; dev DB had 0 legacy orders. |
| **6** | ALLOWED_HOSTS / SECRET_KEY from env | **COMPLETED** | `ALLOWED_HOSTS` read from env (default: akidsenterprise.com, www.akidsenterprice.com, localhost, 127.0.0.1, *.vercel.app). Strong `SECRET_KEY` generated and added to `.env`. |
| **7** | CSRF on admin & chat APIs | **COMPLETED** | All `@csrf_exempt` removed. Frontend sends `X-CSRFToken` (main.js chat, login/signup firebase fetch, view_all inquiry). Hidden `{% csrf_token %}` form in `base.html` guarantees the cookie on every page. |
| **8** | XSS fixes (chat + autocomplete) | **COMPLETED** | `escapeHtml()` applied to search-autocomplete dropdown fields (unreachable route, fixed defensively). Chat escaping hardened. |
| **9** | Security headers | **COMPLETED** | `SecurityHeadersMiddleware` adds lenient CSP (pdf.js-safe, `worker-src blob:`), `Permissions-Policy`. Settings add HSTS (prod-gated), nosniff, frame options, `SECURE_PROXY_SSL_HEADER`, Referrer-Policy. |
| **10** | Env-driven DEBUG | **COMPLETED** | `DJANGO_DEBUG` env var, defaults True locally. Production must set `DJANGO_DEBUG=False`. |
| **11** | Tests for every fix | **COMPLETED** | 22 new tests added across `tests.py`/`test_orders.py`/`test_inquiries.py` (CSRF rejection, IDOR 404, GST math, PDF invoice, startup fail-fast, credential-literal scan). **44/44 pass.** |
| **12** | Re-audit & reporting | **COMPLETED** | `latest-report.md` renamed to `audit-reports.md` (content preserved). New re-scan report appended with scorecard 97/100. History JSON written. |

#### 2. Modified & Created Files
- `backend/products/utils.py` (NEW)
- `backend/products/management/commands/create_admin_from_env.py` (NEW)
- `backend/products/migrations/0018_order_gst_amount_order_subtotal_amount.py` (NEW)
- `backend/products/migrations/0019_backfill_order_gst.py` (NEW)
- `backend/little_fingers/middleware.py`
- `backend/little_fingers/settings.py`
- `backend/products/views.py`
- `backend/products/models.py`
- `backend/products/pdf_generator.py`
- `backend/products/tests.py`
- `backend/products/test_orders.py`
- `backend/products/test_inquiries.py`
- `frontend/static/js/main.js`
- `frontend/templates/base.html`
- `frontend/templates/products/login.html`
- `frontend/templates/products/signup.html`
- `frontend/templates/products/view_all.html`
- `frontend/templates/products/home.html`
- `frontend/templates/products/listing.html`
- `frontend/templates/products/outdoors.html`
- `frontend/templates/products/shreemsports.html`
- `frontend/templates/products/search_results.html`
- `vercel.json`
- `.env`
- `docs/audit/audit-reports.md`
- `docs/audit/history/2026-08-01-rescan.json`
- `docs/progress.md`

**Test Status**: All 44 unit tests pass cleanly (`DATABASE_URL= python manage.py test products`).
