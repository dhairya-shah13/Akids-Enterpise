# Akids-Enterprise Project Context

## Overview
Akids-Enterprise is a web application structured with a Django backend. Based on the data models, it appears to be an e-commerce platform focused on children's products (indoor/outdoor toys, sports, parts).

## Architecture

### Backend (`/backend`)
- Framework: Django (with Postgres, Pillow, Whitenoise, Gunicorn).
- Apps:
  - `little_fingers`: Main Django project configuration folder.
  - `products`: App handling product data. Includes a `Product` model with fields for name, category (Indoors, Outdoors, Parts, RF Sports), price, discount price, description, images, sku, and stock.

### Frontend (`/frontend`)
- Appears to use Django's built-in templating system.
- Organized into `media`, `static`, and `templates` directories.

## Running the Application
Currently, a Django development server is typically run via:
```bash
cd backend
python manage.py runserver
```

## Deployment
- The presence of `vercel.json` and `whitenoise` in `requirements.txt` suggests that this app may be configured for deployment on Vercel, with Whitenoise managing static files.
