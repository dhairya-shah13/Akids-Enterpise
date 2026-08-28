# A kids India — Kindergarten Furniture, Playground Equipment & Sports Gear

A kids India is a premier manufacturer and supplier of kindergarten furniture, educational play items, outdoor playground equipment, and sports gear. This repository contains the e-commerce platform and project portal built using Django.

## Technology Stack

- **Backend**: Django 6.x
- **Database**: PostgreSQL (Production) / SQLite (Local Dev)
- **Frontend**: Tailwind CSS (minified output served via staticfiles)
- **Styles Compilation**: PostCSS & Autoprefixer

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js (for compiling Tailwind CSS styles)
- `uv` (recommended fast Python package installer) or `pip`

### Python Environment Setup

1. **Install Python dependencies**:
   Using `uv`:
   ```bash
   uv pip install -r requirements.txt
   ```
   Or standard `pip`:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   Create a `.env` file inside the `backend/` directory (see `backend/.env` configuration details for database credentials and Django settings).

3. **Run database migrations**:
   ```bash
   python backend/manage.py migrate
   ```

4. **Start the local server**:
   ```bash
   python backend/manage.py runserver
   ```

### Frontend Assets Compilation

If you make modifications to the layout or classes using Tailwind CSS, rebuild the styles:

1. **Install dev dependencies**:
   ```bash
   npm install
   ```

2. **Compile Tailwind CSS styles**:
   ```bash
   npm run build:css
   ```

---

## Running Tests

Verify code correctness using Django's test runner:

```bash
python backend/manage.py test
```

Or run from the `backend/` directory:
```bash
cd backend
python manage.py test
```

> [!NOTE]
> Testing automatically uses an in-memory SQLite database (`:memory:`) to bypass connection limits and database creation restrictions present on remote production database poolers (e.g. Supabase).

---

## SEO & Accessibility (RankSynth Protocol)

This repository follows the autonomous SEO RankSynth manual:
- Semantic HTML landmarks must have exactly one H1 per page and logical heading nesting.
- Explicit bot policies must be maintained in `robots_txt` view in `views.py`.
- Correct reciprocity of hreflang tags (when multilingual) and schema-marked breadcrumbs.
- Structured data JSON-LD graph matching page templates on home, listing, static, and product detail views.
