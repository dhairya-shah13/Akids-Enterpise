# Implementation Plan — Site-Wide Response Time Audit & Consolidated Optimization

This plan addresses the performance bottlenecks identified across the **A kids India** website (Django 6.x + PostgreSQL/Supabase, deployed on Vercel serverless functions).

---

## 1. Workstream Status Summary

| Workstream | Focus | Status | Action Taken / Plan |
| :--- | :--- | :--- | :--- |
| **WS-1** | **DB & ORM Optimizations** | **EXECUTED** | Added `prefetch_related('class_specs', 'dimension_specs')` to product listing and detail views to eliminate N+1 queries. All tests pass. |
| **WS-2** | **Cache & Session Engine** | **UNDER REVIEW** | Shared Cache (Upstash Redis / Vercel KV) proposed as primary; Cookie-based session engine analyzed as secondary. |
| **WS-3** | **Platform Regional Alignment** | **UNDER REVIEW** | Confirmed Hobby tier support (1 region is free); awaiting owner confirmation to apply Sydney (`syd1`) co-location. |
| **WS-4** | **Chat API Timeout Hardening** | **EXECUTED** | Reduced timeouts to 8s; implemented mascot fallback on timeout; added `test_chat_api_timeout_returns_mascot_fallback` unit test (passing). |
| **WS-5** | **Core Static Asset Compression** | **EXECUTED** | Compressed `favicon.png`, `logo.png`, and `train.png` using Pillow adaptive quantization, saving **466 KB** (80%+) of asset overhead. |

---

## 2. Completed / Executed Changes (WS-1, WS-4, WS-5)

### WS-1: Database & ORM Optimizations (N+1 Query Loop Solved)
- **Problem**: Django iterated over product specs (`class_specs` and `dimension_specs`) in the `product_card.html` template. Lacking prefetching, this issued up to 5 additional SQL queries per product listing.
- **Solution Applied**:
  - Modified [views.py](file:///c:/Projects/Akids-Enterpise/backend/products/views.py) to prefetch related class and dimension specifications on key product listing and retrieval paths (`home_view`, `category_listing`, `product_detail` primary and related product lookups).
  - Modified [search.py](file:///c:/Projects/Akids-Enterpise/backend/products/search.py) to prefetch related specs on `search_products`.
- **Latency Impact**: Database roundtrips for search listings reduced from **60 queries to 3 queries**, eliminating up to **+1.1s to +2.8s** of cross-ocean network latency.

### WS-4: External API Timeout Hardening
- **Problem**: Groq chatbot calls ran synchronously with `timeout=15`. Under network delays, this held Vercel serverless container threads, triggering a Vercel 10s Hobby timeout (resulting in a 504 Gateway Timeout error for the client).
- **Solution Applied**:
  - Reduced connection timeouts in `chat_api` in [views.py](file:///c:/Projects/Akids-Enterpise/backend/products/views.py) to `8` seconds for both the main request and the fallback request.
  - Confirmed the code path catches all request exceptions and returns a friendly mascot fallback JSON response (Mohanlal's custom connection message) instead of failing with a 500 error or Vercel 504.
  - Added unit test `test_chat_api_timeout_returns_mascot_fallback` to [tests.py](file:///c:/Projects/Akids-Enterpise/backend/products/tests.py) to verify fallback behavior on simulated connection failures.

### WS-5: Core Static Asset Compression
- **Problem**: Core design images were unoptimized, causing high transfer size on page load.
- **Solution Applied**: Optimized files under `frontend/static/images/` using adaptive quantization:
  - `favicon.png`: **153.7 KB** → **29.7 KB** (Saved **124 KB** / 80% reduction)
  - `logo.png`: **183 KB** → **28.4 KB** (Saved **154 KB** / 84% reduction)
  - `train.png`: **217.4 KB** → **29.2 KB** (Saved **188 KB** / 86% reduction)
  - **Total Savings**: **466 KB** saved on every uncached page request.

---

## 3. Revised Workstream Analysis (WS-2, WS-3)

### WS-3: Regional Alignment (Vercel Hobby Tier Analysis)
- **Plan Support**: Vercel **Hobby plan** natively supports configuring a serverless function region.
- **Hobby Tier Constraint**: You are limited to selecting **one single region** for your serverless functions (which is exactly what we need). Pro allows up to 5 regions, and Enterprise allows global deployment.
- **Cost**: **$0.00** (Free on Vercel Hobby). No upgrade required.
- **How to configure**:
  - Option A (Dashboard - Recommended): In the Vercel Project Dashboard under **Settings → Functions → Function Region**, select **Sydney, Australia (syd1)**.
  - Option B (Repository config): Add the `"regions": ["syd1"]` top-level array key to `vercel.json`.

---

### WS-2: Caching & Session Engine Analysis

#### 1. Session Payload Audit (Cookie Suitability)
We audited how Django sessions are populated in the codebase:
- **Keys stored**:
  - `is_admin`: Boolean (set on admin authentication).
  - `forgot_password_email` / `force_password_set`: Transient authentication helper variables.
  - `cart`: Dictionary mapping item variants to integer quantities.
- **Cart Key format**: `f"{product_id}::{colour}::{dimension}"` (e.g. `"14::Red::Toddler": 2`).
- **Data Size**: The cart dictionary only holds strings and integers. A typical checkout cart containing 5-10 items scales to **less than 300 bytes** of raw text payload.
- **Conclusion**: A typical session payload is **under 0.5 KB**—well below the hard **4 KB cookie size limit**. Secure client-side signed cookies are technically viable for our data size.

#### 2. Cookie Session Transition Risks
- **Session Invalidation**: Changing `SESSION_ENGINE` from `cached_db` to `signed_cookies` changes how keys are decrypted.
- **User Impact**: All current logged-in admins will be logged out instantly on deploy, and all active anonymous carts will be cleared.
- **Deployment Strategy**: This transition must be treated as a minor migration window. We will schedule it during off-peak hours (e.g. 2:00 AM IST) and add a banner alert beforehand.

#### 3. Primary Proposal: Shared Redis Cache (LocMemCache Replacement)
Rather than changing the session engine, we propose **replacing the in-memory cache backend (`LocMemCache`) with a shared serverless cache** (such as **Upstash Redis** or **Vercel KV**):
- **Why this solves both cache and sessions**:
  - **Shared Caching**: All serverless containers will read/write to the same Redis instance, making cache decorators (`@cache_page` on static pages like `/about/` or `/sitemap.xml`) fully effective.
  - **Zero-DB Sessions**: The existing `cached_db` session engine writes to cache first and only falls back to the PostgreSQL database on a cache miss. With shared Redis caching, session reads are served from Redis in sub-milliseconds, **completely eliminating session queries to PostgreSQL**.
  - **Global Rate Limiting**: Ensures that IP-based rate limiting (in `ratelimit.py`) is globally synchronized across all serverless containers.
  - **No Invalidation**: Session data is preserved in both Postgres and the new cache; **no users are logged out** and **no carts are lost**.
- **Setup Requirements**:
  1. Add a free Upstash Redis database (integrated natively in Vercel as Vercel KV, or separately via Upstash console).
  2. Install `django-redis` package.
  3. Configure the `CACHES` setting in `settings.py` to point to the `REDIS_URL`.
- **Costs**:
  - **Vercel KV / Upstash Free Tier**: **$0.00/month** (generous limits of 3,000–10,000 requests/day, perfect for development/testing).
  - **Pay-as-you-go**: ~$1.00 per month for production traffic levels.

---

## 4. Verification & Validation Matrix (Post-Approval)

| Workstream | Pre-Deploy Verification (Dev) | Post-Deploy Verification (Prod) | Rollback |
| :--- | :--- | :--- | :--- |
| **WS-3 (Region)** | Check dashboard region or deploy dry-run. | Vercel Function logs show execution region is `syd1`. | Remove `"regions"` from `vercel.json` or restore default region in Vercel dashboard. |
| **WS-2 (Shared Cache)** | Run test suite with mock Redis backend configured. | Verify static pages return `cf-cache-status: HIT` and Django timing logs show zero database queries on repeat sessions. | Revert `CACHES` configuration back to `LocMemCache`. |
