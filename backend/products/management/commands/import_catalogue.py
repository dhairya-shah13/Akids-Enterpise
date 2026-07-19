import os
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from products.models import Product
from pypdf import PdfReader

class Command(BaseCommand):
    help = 'Import products from the 4 PDF catalogues located in the assets folder.'

    def handle(self, *args, **options):
        # Locate the assets directory (c:\Users\REEVA\OneDrive\Desktop\AKids\assets)
        assets_dir = r"c:\Users\REEVA\OneDrive\Desktop\AKids\assets"
        
        if not os.path.exists(assets_dir):
            self.stdout.write(self.style.ERROR(f"Assets directory not found at: {assets_dir}"))
            return

        catalogues = [
            {
                "name": "Indoor Catalogue March 2026-.pdf",
                "category": "INDOORS",
                "parser": self.parse_indoor
            },
            {
                "name": "Outdoor Catalogue March 2026-.pdf",
                "category": "OUTDOORS",
                "parser": self.parse_outdoor
            },
            {
                "name": "new Outdoor & Soft Play Components March 2026-.pdf",
                "category": "PARTS",
                "parser": self.parse_softplay
            },
            {
                "name": "Little Woods Catalogue 2025-26.pdf",
                "category": "INDOORS",
                "parser": self.parse_littlewoods
            }
        ]

        for cat in catalogues:
            filepath = os.path.join(assets_dir, cat["name"])
            self.stdout.write(self.style.SUCCESS(f"Starting import of: {cat['name']}"))
            if not os.path.exists(filepath):
                self.stdout.write(self.style.WARNING(f"File not found: {filepath}"))
                continue
                
            try:
                reader = PdfReader(filepath)
                cat["parser"](reader, cat["category"])
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading {cat['name']}: {e}"))

        self.stdout.write(self.style.SUCCESS("Catalogue import complete!"))

    def clean_price(self, price_str):
        # Remove commas, Rs., MRP, spaces, and parse as Decimal
        cleaned = re.sub(r'[^\d.]', '', price_str)
        if not cleaned:
            return Decimal('0.00')
        try:
            return Decimal(cleaned)
        except Exception:
            return Decimal('0.00')

    def parse_indoor(self, reader, category):
        # Handles Indoor Catalogue (SKUs like LF 7021, name, price, dimensions)
        imported_count = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
            
            # Look for SKU of pattern LF 7021
            sku_match = re.search(r'(LF\s*\d{4})', text)
            if not sku_match:
                continue
                
            sku = sku_match.group(1).replace(" ", "")
            
            # Find lines
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            # Identify name: usually the line after the SKU line, or contains it
            name = f"Indoor Item {sku}"
            for idx, line in enumerate(lines):
                if sku_match.group(1) in line:
                    # check next line
                    if idx + 1 < len(lines):
                        next_line = lines[idx+1]
                        if "Dimensions" not in next_line and "Page" not in next_line and "MRP" not in next_line:
                            name = next_line
                    break
            
            # Find Price
            price = Decimal('0.00')
            price_match = re.search(r'MRP\s*:\s*([\d,.]+)', text, re.IGNORECASE)
            if price_match:
                price = self.clean_price(price_match.group(1))
            
            # Description: full page text
            desc = text.replace(sku_match.group(1), "").strip()
            desc = re.sub(r'Page\s*\d+', '', desc)
            desc = re.sub(r'www\.li\s*leﬁngers\.in', '', desc, flags=re.IGNORECASE)
            desc = desc.strip()
            
            if not Product.objects.filter(sku=sku).exists():
                Product.objects.create(
                    name=name,
                    sku=sku,
                    price=price,
                    description=desc if desc else f"Premium kids indoor play unit (SKU: {sku}).",
                    category=category,
                    source='catalogue',
                    needs_image=True,
                    stock=10
                )
                imported_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Imported {imported_count} products from Indoor Catalogue."))

    def parse_outdoor(self, reader, category):
        # Handles Outdoor Catalogue (SKUs like LFO-MPS-01, sizes, prices, details)
        imported_count = 0
        sku_types = {
            'LFO-MPS': 'Multiplay Station',
            'LFO-JPS': 'Junior Play Station',
            'LFO-WSC': 'Web Scrambler',
            'LFO-SW': 'Outdoor Swing',
            'LFO-SD': 'Outdoor Slide',
            'LFO-SS': 'Outdoor See Saw',
            'LFO-MGR': 'Merry Go Round',
            'LFO-CL': 'Play Climber',
            'LFO-TR': 'Trampoline',
            'LFO-SR': 'Spring Rider',
            'LFO-FN': 'Outdoor Fitness Gym',
            'LFO-DB': 'Dustbin'
        }
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
                
            # Scan for SKUs matching LFO-[A-Z]+-\d+[A-Z]?
            skus_found = re.findall(r'(LFO-[A-Z]+-\d+[A-Z]?)', text)
            if not skus_found:
                # Try fallback for slide styles like LFO-SD-04 or LFO-FN
                skus_found = re.findall(r'(LFO-[A-Z]+-\d+)', text)
                
            if not skus_found:
                continue
                
            # For each SKU found on the page, try to extract its price and description
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            for sku in set(skus_found):
                sku_clean = sku.replace(" ", "")
                
                # Determine Name based on SKU prefix
                prefix = '-'.join(sku_clean.split('-')[:2])
                product_type = sku_types.get(prefix, "Outdoor Play Equipment")
                name = f"{product_type} {sku_clean}"
                
                # Find specific line containing this SKU to parse its details
                detail_line = ""
                for line in lines:
                    if sku in line:
                        detail_line = line
                        break
                
                # Price extraction
                price = Decimal('0.00')
                # Try finding price inside detail_line or surrounding
                price_match = re.search(r'(\d+,\d{2,3},\d{3}|\d+,\d{3})', detail_line)
                if not price_match:
                    price_match = re.search(r'MRP\s*:\s*([\d,.]+)', text, re.IGNORECASE)
                if not price_match:
                    # Generic search on the page for prices
                    prices_on_page = re.findall(r'(\d+,\d{3})', text)
                    if prices_on_page:
                        # Take the first one or try matching
                        price = self.clean_price(prices_on_page[0])
                else:
                    price = self.clean_price(price_match.group(1))
                
                # If price is still 0, check for things like 1,19,990 on the page
                if price == 0:
                    large_price_match = re.search(r'(\d+,\d+,\d{3})', text)
                    if large_price_match:
                        price = self.clean_price(large_price_match.group(1))
                
                # Description
                # Combine size and features
                desc_parts = []
                if detail_line:
                    desc_parts.append(detail_line)
                
                # Look for bullet features below it in the text (like Gathering, Staircase, Sliding, etc.)
                features = ["Gathering", "Staircase", "Sliding", "Climbing", "Swinging", "Bridge", "Roof"]
                found_feats = [f for f in features if f.lower() in text.lower()]
                if found_feats:
                    desc_parts.append("Features: " + ", ".join(found_feats))
                
                desc = " | ".join(desc_parts)
                desc = re.sub(r'Page\s*\d+', '', desc)
                desc = re.sub(r'www\.littlefingers\.in', '', desc, flags=re.IGNORECASE)
                
                if not Product.objects.filter(sku=sku_clean).exists():
                    Product.objects.create(
                        name=name,
                        sku=sku_clean,
                        price=price,
                        description=desc if desc else f"Heavy duty outdoor playground unit (SKU: {sku_clean}).",
                        category=category,
                        source='catalogue',
                        needs_image=True,
                        stock=5
                    )
                    imported_count += 1
                    
        self.stdout.write(self.style.SUCCESS(f"Imported {imported_count} products from Outdoor Catalogue."))

    def parse_softplay(self, reader, category):
        # Handles new Outdoor & Soft Play components
        imported_count = 0
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text:
                continue
                
            # Format often looks like:
            # Single Straight Slide (90cm)
            # Rs. 10,000
            # Let's split by lines and look for Rs. values
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            for idx, line in enumerate(lines):
                if 'Rs.' in line or 'Rs ' in line:
                    price_match = re.search(r'(?:Rs\.?|Rs)\s*([\d,.]+)', line)
                    if price_match:
                        price = self.clean_price(price_match.group(1))
                        
                        # The product name is usually the line before
                        name = "Soft Play / Component"
                        if idx > 0:
                            name = lines[idx-1]
                        
                        # Create a SKU based on page and index to be unique
                        sku = f"SP-P{i+1}-{idx}"
                        
                        # Clean name
                        name_cleaned = re.sub(r'\(\d+cm\).*', '', name).strip()
                        if not name_cleaned or len(name_cleaned) < 4:
                            name_cleaned = name
                            
                        if not Product.objects.filter(sku=sku).exists():
                            Product.objects.create(
                                name=name_cleaned,
                                sku=sku,
                                price=price,
                                description=f"Soft play component / accessory: {name}. Dimensions/specs listed in catalogue.",
                                category=category,
                                source='catalogue',
                                needs_image=True,
                                stock=15
                            )
                            imported_count += 1
                            
        self.stdout.write(self.style.SUCCESS(f"Imported {imported_count} products from Soft Play Components Catalogue."))

    def parse_littlewoods(self, reader, category):
        # Handles Little Woods Catalogue (codes like AL 01, AL 02, etc.)
        imported_count = 0
        
        # Categorized lists based on page contents
        sections = {
            'AL': 'Alphabet & Numbers Puzzle',
            'WA': 'Wooden Alphabet blocks',
            'SC': 'Shape & Color sorter',
            'BB': 'Building Blocks Set',
            'HE': 'Hand Eye Coordination toy',
            'WT': 'Wheel Toy',
            'PN': 'Wooden Jigsaw Puzzle (Natural)',
            'PC': 'Wooden Jigsaw Puzzle (Coloured)',
            'PB': 'Parts of Body Puzzle',
            'SS': 'Size & Seriation puzzle',
            'LTS': 'Liftout Puzzle (Small)',
            'LTM': 'Liftout Puzzle (Medium)',
            'LTL': 'Liftout Puzzle (Large)',
            'SP': 'Single Piece Puzzle',
            'LG': 'Educational Puzzle',
            'LFM': 'Montessori Educational Puzzle',
            'H': 'Spiral Beads & Maze Chase',
            'TB': 'Tracing Board',
            'LF': 'Preschool Classroom Furniture',
        }

        for i, page in enumerate(reader.pages):
            if i < 2:  # Skip cover and index
                continue
            text = page.extract_text()
            if not text:
                continue
                
            # Scan for code blocks like "AL 01" or "TB 05"
            codes = re.findall(r'\b([A-Z]{1,3})\s*\n?\s*(\d{2})\b', text)
            if not codes:
                continue
                
            for prefix, num in codes:
                sku = f"LW-{prefix}-{num}"
                
                # Determine Name based on code
                type_name = sections.get(prefix, "Wooden Educational Toy")
                name = f"Little Woods {type_name} ({sku})"
                
                # Extract sizes if present in page (e.g. 9"X12", 12"X15")
                sizes = re.findall(r'(\d+"X\d+")', text)
                size_desc = f"Size: {sizes[0]}" if sizes else "Standard Size"
                
                if not Product.objects.filter(sku=sku).exists():
                    Product.objects.create(
                        name=name,
                        sku=sku,
                        price=Decimal('0.00'),
                        description=f"Premium wooden educational play material. {size_desc}. Designed for Montessori, nursery, and preschool classrooms.",
                        category=category,
                        source='catalogue',
                        needs_image=True,
                        stock=20
                    )
                    imported_count += 1
                    
        self.stdout.write(self.style.SUCCESS(f"Imported {imported_count} products from Little Woods Catalogue."))
