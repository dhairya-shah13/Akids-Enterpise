# Little Fingers - Project Context Document

This document provides a comprehensive overview of the **Little Fingers** e-commerce platform for playground equipment and educational furniture. It is designed to help developers and AI agents quickly understand the codebase without spending hours exploring.

---

## 📁 Project Structure

```
Akids-Enterpise/
├── .claude/                    # Claude Code configuration
├── .git/                       # Git repository
├── .env                        # Environment variables (secrets - DO NOT COMMIT)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── vercel.json                 # Vercel deployment configuration
├── context.md                  # THIS FILE
├── backend/                    # Django backend
│   ├── manage.py               # Django management script
│   ├── db.sqlite3              # SQLite database (development)
│   ├── little_fingers/         # Django project settings
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py         # Main settings file
│   │   ├── urls.py             # Root URL configuration
│   │   ├── wsgi.py             # WSGI entry point
│   │   └── __pycache__/
│   └── products/               # Products Django app
│       ├── __init__.py
│       ├── admin.py            # Django admin config
│       ├── apps.py             # App configuration
│       ├── models.py           # Product model
│       ├── views.py            # All view logic (auth, cart, admin, products)
│       ├── urls.py             # Product URL routing
│       ├── tests.py            # Tests placeholder
│       └── migrations/         # Database migrations
│           ├── 0001_initial.py
│           ├── 0002_product_image_file_alter_product_image_url.py
│           ├── 0003_alter_product_price.py
│           └── 0004_product_discount_price_product_sku_product_stock.py
└── frontend/                   # Django templates & static assets
    ├── static/
    │   └── css/
    │       └── main.css        # Design system & utilities (neo-brutalist)
    ├── media/                  # User uploads (product images)
    └── templates/
        ├── base.html           # Base template with header/footer/nav
        ├── 404.html            # Custom 404 page
        └── products/
            ├── admin_dashboard.html   # Admin panel
            ├── cart.html              # Shopping cart
            ├── home.html              # Landing page
            ├── listing.html           # Indoors category
            ├── outdoors.html          # Outdoors category
            ├── parts.html             # Parts category
            ├── rfsports.html          # RF Sports category
            ├── product_detail.html    # Product detail page
            ├── login.html             # Login page
            └── signup.html            # Signup page
```

---

## 🛠 Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Backend Framework** | Django | 6.0.5+ |
| **Database** | PostgreSQL (Supabase) / SQLite (dev) | - |
| **ORM** | Django ORM | - |
| **Auth** | Django Auth + Custom session-based admin | - |
| **Static Files** | WhiteNoise | 6.11.0 |
| **Image Storage** | Supabase Storage | - |
| **Deployment** | Vercel (Python) | - |
| **Frontend** | Django Templates + Vanilla CSS/JS | - |
| **Design System** | Custom CSS (neo-brutalist) | - |
| **Fonts** | Google Fonts (Nunito, Inter, Fredoka One, Material Symbols) | - |

---

## 🔐 Environment Variables (`.env`)

```env
# Admin credentials (used for admin panel access)
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD=123456

# Supabase PostgreSQL connection
DATABASE_URL=postgresql://postgres:Akids%4018088@db.raonllwzgumhalpjdmqe.supabase.co:5432/postgres

# Supabase Storage (for product images)
SUPABASE_URL=https://raonllwzgumhalpjdmqe.supabase.co
SUPABASE_KEY=sb_publishable_jm6m6Qn7c5FmnEd0ZC967A_zAvArXRm
SUPABASE_BUCKET=products
```

> **Security Note**: The `.env` file is in `.gitignore`. Never commit real secrets. Use Vercel environment variables for production.

---

## 🗄 Database Schema

### Product Model (`backend/products/models.py`)

```python
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('INDOORS', 'Indoors'),
        ('OUTDOORS', 'Outdoors'),
        ('PARTS', 'Parts'),
        ('RFSPORTS', 'RF Sports'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='INDOORS')
    price = models.DecimalField(max_digits=14, decimal_places=2)
    discount_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    image_file = models.ImageField(upload_to='products/', null=True, blank=True)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    sku = models.CharField(max_length=50, null=True, blank=True)
    stock = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def display_image(self):
        """Returns image_file.url > image_url > fallback Unsplash image"""
```

### Migration History
- `0001_initial` - Initial Product model
- `0002` - Added `image_file`, altered `image_url`
- `0003` - Altered `price` field
- `0004` - Added `discount_price`, `sku`, `stock`

---

## 🌐 URL Routing

### Root URLs (`backend/little_fingers/urls.py`)
```python
urlpatterns = [
    path('admin/', admin.site.urls),           # Django admin
    path('', include('products.urls')),        # All product routes
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Dev media serving
```

### Product URLs (`backend/products/urls.py`)
| Path | View | Name |
|------|------|------|
| `/` | `TemplateView(home.html)` | `home` |
| `/indoors/` | `indoors_view` | `indoors` |
| `/outdoors/` | `outdoors_view` | `outdoors` |
| `/parts/` | `parts_view` | `parts` |
| `/rfsports/` | `rfsports_view` | `rfsports` |
| `/product/<pk>/` | `product_detail` | `product_detail` |
| `/login/` | `login_view` | `admin_login` |
| `/signup/` | `signup_view` | `signup` |
| `/logout/` | `logout_view` | `admin_logout` |
| `/cart/` | `cart_view` | `cart` |
| `/cart/add/<pk>/` | `add_to_cart` | `add_to_cart` |
| `/cart/remove/<pk>/` | `remove_from_cart` | `remove_from_cart` |
| `/cart/update/<pk>/` | `update_cart` | `update_cart` |
| `/admin-panel/` | `admin_dashboard` | `admin_dashboard` |
| `/admin-panel/products/add/` | `add_product` | `add_product` |
| `/admin-panel/products/<pk>/delete/` | `delete_product` | `delete_product` |

---

## 🧠 Core Views Logic (`backend/products/views.py`)

### Authentication & Session Management

**Admin Login** (custom, not Django admin):
- Checks `.env` `ADMIN_EMAIL`/`ADMIN_PASSWORD` first
- Sets `request.session['is_admin'] = True`
- Redirects to admin dashboard

**Regular User Auth**:
- Uses Django's `authenticate()` with email as username
- Standard `login()`/`logout()` flow
- Session-based cart persists across auth states

**Logout**: Flushes session + Django logout

### Cart System (Session-based)
```python
# Cart stored in session: request.session['cart'] = { 'product_pk': quantity }
# Helper: get_cart_data(request) -> (cart_items_list, subtotal)
# Cart item: { 'product': Product, 'quantity': int, 'total_price': Decimal }
```

### Product Views
- **Category listings**: `indoors_view`, `outdoors_view`, `parts_view`, `rfsports_view` all use `category_listing()` helper
- **Product detail**: Shows related products (same category, latest 3)
- **Admin dashboard**: Hardcoded sales data + product list
- **Add product**: Handles Supabase upload, local file, or image URL

### Image Upload to Supabase
```python
def upload_photo_to_supabase(file_obj):
    # Uses SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET from env
    # Generates UUID filename, uploads to Supabase Storage
    # Returns public URL on success, None on failure
```

---

## 🎨 Frontend Architecture

### Design System (`frontend/static/css/main.css`)

**Neo-Brutalist Style**:
- Thick borders (`3px solid #1A1A2E`)
- Offset shadows (`4px 4px 0 #1A1A2E`)
- Playful rotations (`rotate-1`, `rotate-2`, etc.)
- Bounce animations on buttons

**Design Tokens**:
```css
--primary: #F5A623;      /* Yellow */
--secondary: #2ECC71;    /* Green */
--accent: #3498DB;       /* Blue */
--danger: #E74C3C;       /* Red */
--neutral-dark: #1A1A2E; /* Near black */
--neutral-light: #F8F9FA;
--font-heading: 'Nunito';
--font-body: 'Inter';
--font-accent: 'Fredoka One';
```

**Utility Classes**: Container, Flex, Grid, Spacing, Colors, Typography, Neo-brutalist helpers

### Base Template (`frontend/templates/base.html`)

**Key Components**:
1. **Sticky Header** with logo, nav links (desktop), hamburger menu (mobile)
2. **Responsive Navigation**: Desktop flex nav, mobile slide-down drawer
3. **Cart/Admin/User actions** in header (context-aware)
4. **Footer** with grass-border decoration
5. **FAB** (chat bubble) fixed bottom-right
6. **Mobile menu toggle** JavaScript

### Template Inheritance
```
base.html
├── home.html           (hero, categories, trending, newsletter)
├── listing.html        (Indoors grid)
├── outdoors.html       (Outdoors grid)
├── parts.html          (Parts grid)
├── rfsports.html       (RF Sports grid)
├── product_detail.html (Single product + related)
├── cart.html           (Cart items, quantities, checkout)
├── login.html          (Email/password + admin credentials)
├── signup.html         (Username/email/password)
├── admin_dashboard.html (Sales stats, product table, add form)
└── 404.html            (Custom not found)
```

---

## ⚙️ Django Settings Highlights (`backend/little_fingers/settings.py`)

```python
# Database: PostgreSQL (Supabase) if DATABASE_URL set, else SQLite
# Static files: WhiteNoise + frontend/static + staticfiles (collectstatic)
# Media files: frontend/media
# Templates: frontend/templates
# Debug: True (dev)
# Allowed hosts: ['*']
```

### Installed Apps
- Django defaults (admin, auth, contenttypes, sessions, messages, staticfiles)
- `products` (custom app)

### Middleware Order
1. SecurityMiddleware
2. **WhiteNoiseMiddleware** (static files)
3. SessionMiddleware
4. CommonMiddleware
5. CsrfViewMiddleware
6. AuthenticationMiddleware
7. MessageMiddleware
8. XFrameOptionsMiddleware

---

## 🚀 Deployment (Vercel)

### `vercel.json`
```json
{
  "version": 2,
  "builds": [
    { "src": "backend/little_fingers/wsgi.py", "use": "@vercel/python" },
    { "src": "frontend/static/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/static/(.*)", "dest": "frontend/static/$1" },
    { "src": "/(.*)", "dest": "backend/little_fingers/wsgi.py" }
  ]
}
```

**Build Process**: Vercel runs `pip install -r requirements.txt` then serves via WSGI.

**Required Vercel Environment Variables**:
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `DATABASE_URL`
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET`
- `SECRET_KEY` (generate new for production)

---

## 🔧 Development Commands

```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r ../requirements.txt

# Database
python manage.py migrate
python manage.py createsuperuser  # Optional Django admin

# Run server
python manage.py runserver

# Static files (for production)
python manage.py collectstatic

# Create migrations
python manage.py makemigrations products
python manage.py migrate
```

---

## 📦 Key Dependencies (`requirements.txt`)

```
Django>=6.0.5
psycopg[binary]>=3.3.4        # PostgreSQL driver
python-dotenv>=1.2.2          # .env loading
pillow>=12.2.0                # Image processing
requests>=2.33.0              # HTTP requests (Supabase upload)
whitenoise>=6.11.0            # Static file serving
gunicorn>=25.1.0              # WSGI server (production)
```

---

## 🎯 Important Implementation Details

### 1. Admin vs Regular User
- **Admin**: Session-based (`request.session['is_admin']`), credentials from `.env`
- **Regular User**: Django auth (`request.user.is_authenticated`), email as username
- Both can have carts; admin has access to `/admin-panel/`

### 2. Image Handling Priority
```python
@property
def display_image(self):
    if self.image_file:      # 1. Local upload (media/)
        return self.image_file.url
    elif self.image_url:     # 2. External URL
        return self.image_url
    return "..."             # 3. Fallback Unsplash image
```

### 3. Cart Persistence
- Stored in Django session (`request.session['cart']`)
- Survives login/logout for regular users
- Admin session separate from user session

### 4. Category Templates
Each category has its own template but uses the same `category_listing` view:
- Indoors → `listing.html`
- Outdoors → `outdoors.html`
- Parts → `parts.html`
- RF Sports → `rfsports.html`

### 5. Supabase Integration
- **Database**: PostgreSQL via `DATABASE_URL`
- **Storage**: Product images uploaded to Supabase bucket `products`
- Uses `requests` library directly (no Supabase SDK)

---

## 🐛 Known Issues / TODOs

1. **Hardcoded sales data** in `admin_dashboard` view
2. **No password reset** flow for regular users
3. **No email verification** for signup
4. **No order/checkout** system (cart only)
5. **No product search/filter** functionality
6. **Admin panel** uses custom session auth, not Django admin
7. **SECRET_KEY** is hardcoded in settings (should use env var in production)
8. **No tests** in `products/tests.py`
9. **Stock validation** only on cart add/update, not on checkout (no checkout)

---

## 🔍 Quick Reference: Adding a New Feature

### New Category
1. Add to `CATEGORY_CHOICES` in `models.py`
2. Create template `products/newcategory.html`
3. Add view in `views.py` (or use `category_listing`)
4. Add URL in `products/urls.py`
5. Add nav link in `base.html`

### New Product Field
1. Add field to `Product` model
2. Run `makemigrations` + `migrate`
3. Update `add_product` view to handle new field
4. Update templates to display field

### New Page
1. Create template in `frontend/templates/products/`
2. Add view function in `views.py`
3. Add URL pattern in `products/urls.py`
4. Extend `base.html` and use design system classes

---

## 📝 Recent Commits Context

| Commit | Description |
|--------|-------------|
| `60cbc2f` | images |
| `3ce8731` | Merge PR #3 |
| `d1d5281` | photus |
| `b706ad8` | Merge PR #2 |
| `8c76064` | login-cart-view-details page |

---

## 📞 Support Contacts

- **Repository**: GitHub (origin)
- **Database**: Supabase project `raonllwzgumhalpjdmqe`
- **Deployment**: Vercel

---

*Generated on 2026-06-27. Update this document when significant changes are made to the codebase.*