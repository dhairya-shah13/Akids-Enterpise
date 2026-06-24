"""
Management command to seed products from data/*.js files into the database.

Usage:
    python manage.py seed_products
"""

import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.products.models import Category, Product


class Command(BaseCommand):
    help = 'Seed products from data/indoor.js, data/outdoor.js, and data/parts.js'

    # Map data files to their parent category
    DATA_FILES = [
        {
            'file': 'data/indoor.js',
            'parent_name': 'Indoor',
            'parent_slug': 'indoor',
            'label': 'indoor',
        },
        {
            'file': 'data/outdoor.js',
            'parent_name': 'Outdoor',
            'parent_slug': 'outdoor',
            'label': 'outdoor',
        },
        {
            'file': 'data/parts.js',
            'parent_name': 'Parts',
            'parent_slug': 'parts',
            'label': 'parts',
        },
    ]

    DEFAULT_STOCK = 50

    def parse_js_file(self, filepath):
        """Read a JS file, strip the variable wrapper, and parse as JSON array."""
        content = filepath.read_text(encoding='utf-8')

        # Strip: const VARIABLE_NAME = [...];
        # Find the array start and end
        match = re.search(r'=\s*(\[.*\])\s*;?\s*$', content, re.DOTALL)
        if not match:
            self.stderr.write(f"  Could not parse {filepath.name}")
            return []

        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.stderr.write(f"  JSON parse error in {filepath.name}: {e}")
            return []

    def handle(self, *args, **options):
        from django.conf import settings
        base_dir = settings.BASE_DIR

        total_created = 0
        total_skipped = 0

        for data_config in self.DATA_FILES:
            filepath = base_dir / data_config['file']
            if not filepath.exists():
                self.stderr.write(f"  File not found: {filepath}")
                continue

            self.stdout.write(f"Seeding {data_config['label']} products...")

            # Create or get the parent category
            parent_category, _ = Category.objects.get_or_create(
                slug=data_config['parent_slug'],
                defaults={
                    'name': data_config['parent_name'],
                    'is_active': True,
                }
            )

            products_data = self.parse_js_file(filepath)
            created = 0
            skipped = 0

            for item in products_data:
                sku = item.get('sku', '').strip()
                if not sku:
                    continue

                # Check if product already exists
                if Product.objects.filter(sku=sku).exists():
                    skipped += 1
                    continue

                # Find or create the sub-category
                cat_name = item.get('category', 'General').strip()
                cat_slug = slugify(cat_name)
                if not cat_slug:
                    cat_slug = slugify(f"{data_config['label']}-general")

                child_category, _ = Category.objects.get_or_create(
                    slug=cat_slug,
                    defaults={
                        'name': cat_name,
                        'parent': parent_category,
                        'is_active': True,
                    }
                )
                # Ensure parent is set even if category existed
                if child_category.parent is None:
                    child_category.parent = parent_category
                    child_category.save(update_fields=['parent'])

                # Build product name
                name = item.get('name', f'Product {sku}').strip()

                # Build slug — ensure uniqueness
                product_slug = slugify(name)
                if not product_slug:
                    product_slug = slugify(sku)

                # Handle duplicate slugs by appending sku
                if Product.objects.filter(slug=product_slug).exists():
                    product_slug = slugify(f"{name}-{sku}")
                if Product.objects.filter(slug=product_slug).exists():
                    product_slug = slugify(sku)
                # Final fallback
                counter = 1
                original_slug = product_slug
                while Product.objects.filter(slug=product_slug).exists():
                    product_slug = f"{original_slug}-{counter}"
                    counter += 1

                # Parse price
                price = item.get('price', 0)
                try:
                    price = float(price)
                except (TypeError, ValueError):
                    price = 0

                # Map badge
                badge_raw = item.get('badge', '') or ''
                badge_map = {
                    'popular': 'popular',
                    'new': 'new',
                    'sale': 'sale',
                    'best seller': 'best_seller',
                    'bestseller': 'best_seller',
                }
                badge = badge_map.get(badge_raw.lower().strip(), '')

                # Tags
                tags = item.get('tags', [])
                if not isinstance(tags, list):
                    tags = []

                # Specs
                specs = item.get('specs', {})
                if not isinstance(specs, dict):
                    specs = {}

                Product.objects.create(
                    name=name,
                    slug=product_slug,
                    sku=sku,
                    category=child_category,
                    description=item.get('description', ''),
                    specifications=specs,
                    price=price,
                    mrp=price if price > 0 else None,
                    stock=self.DEFAULT_STOCK,
                    is_active=True,
                    is_featured=(badge == 'popular'),
                    badge=badge,
                    tags=tags,
                )
                created += 1

            self.stdout.write(
                f"  Created: {created}, Skipped: {skipped}"
            )
            total_created += created
            total_skipped += skipped

        self.stdout.write("-" * 53)
        self.stdout.write(
            self.style.SUCCESS(
                f"Total: {total_created} products created. "
                f"{total_skipped} duplicates skipped."
            )
        )
        self.stdout.write(
            f"Default stock set to {self.DEFAULT_STOCK} units per product."
        )
        self.stdout.write(
            "Run 'python manage.py createsuperuser' to access /admin/"
        )
