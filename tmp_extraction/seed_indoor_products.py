"""
Seed Indoor Catalogue products into the Django database.
Parses extracted text from the Indoor Catalogue PDF, identifies products,
extracts images, and creates Product records.
"""
import json
import os
import sys
import re
import shutil
from pathlib import Path

# Output to file to avoid console encoding issues
OUTPUT_FILE = Path(__file__).parent / "indoor" / "seeding_report.txt"

# Django setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'little_fingers.settings')
import django
django.setup()

from django.conf import settings
from products.models import Product

# Paths
BASE_DIR = Path(__file__).parent.parent
EXTRACTED_JSON = BASE_DIR / "tmp_extraction" / "indoor" / "extracted_text.json"
IMAGES_DIR = BASE_DIR / "tmp_extraction" / "indoor" / "images"
MEDIA_PRODUCTS_DIR = BASE_DIR / "frontend" / "media" / "products"
MEDIA_PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    """Write to both stdout and log file."""
    print(msg, flush=True)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear output file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Indoor Catalogue Seeding Report\n")
    f.write("=" * 60 + "\n\n")

# Load extracted text
with open(EXTRACTED_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data["pages"]

def get_page_images(page_num):
    """Get all images for a given page number, sorted by file size (largest first)."""
    pattern = f"page{page_num:03d}_img"
    images = []
    for fname in os.listdir(IMAGES_DIR):
        if fname.startswith(pattern):
            fpath = os.path.join(IMAGES_DIR, fname)
            size = os.path.getsize(fpath)
            images.append((fpath, size))
    images.sort(key=lambda x: x[1], reverse=True)
    return [img[0] for img in images]

def copy_image_to_media(src_path, sku_slug):
    """Copy image to media/products/ directory."""
    ext = os.path.splitext(src_path)[1] or '.jpg'
    dest_name = f"indoor_{sku_slug}{ext}"
    dest_path = MEDIA_PRODUCTS_DIR / dest_name
    counter = 1
    while dest_path.exists():
        dest_name = f"indoor_{sku_slug}_{counter}{ext}"
        dest_path = MEDIA_PRODUCTS_DIR / dest_name
        counter += 1
    shutil.copy2(src_path, dest_path)
    return f"products/{dest_name}"

# ============================================================
# PRODUCT DATA
# ============================================================
products_data = []

def add_product(name, sku, description, price, page_num, category="INDOORS", discount_price=None):
    products_data.append({
        "name": name,
        "sku": sku,
        "description": description,
        "price": price,
        "discount_price": discount_price,
        "category": category,
        "page_num": page_num,
    })

# ============================================================
# PAGE 4: ARC Shape Table
# ============================================================
add_product("ARC Shape Table", "LF 7021",
    "Premium arc-shaped table with chair. Dimensions: L132 x W60 x H59-90 cm (Desk), L43 x W45 x H43 cm (Chair). Premium quality. Suitable for classroom use.",
    18990.00, 4)

# ============================================================
# PAGE 5: Rectangular Shape Table
# ============================================================
add_product("Rectangular Shape Table", "LF 7022",
    "Premium rectangular-shaped table with chair. Dimensions: L80 x W60 x H59-90 cm (Desk), L43 x W45 x H43 cm (Chair). Premium quality.",
    13990.00, 5)

# ============================================================
# PAGE 6: Triangle Shape Table
# ============================================================
add_product("Triangle Shape Table", "LF 7023",
    "Premium triangle-shaped table with chair. Dimensions: L132 x W60 x H59-90 cm (Desk), L43 x W45 x H43 cm (Chair). Premium quality.",
    13990.00, 6)

# ============================================================
# PAGE 7: Dual Seating Desk LF 0431
# ============================================================
add_product("Dual Seating Desk (Wooden Storage)", "LF 0431",
    "Dual seating desk with wooden storage. Suitable for Primary, Middle and High Classes. Dimensions: L110 x W40 x H64/70/75 cm (Desk), L110 x W30 x H38/42/44 cm (Chair). Top: MDF 18mm Melamine Finish with PVC Edge Banding. Also available as LF 0431P (Primary) and LF 0431M (Middle).",
    9990.00, 7)

# ============================================================
# PAGE 8: Dual Seating Desk LF 0447 (Wire Storage)
# ============================================================
add_product("Dual Seating Desk (Wire Storage)", "LF 0447",
    "Dual seating desk with wire storage. Suitable for Primary, Middle and High Classes. Dimensions: L110 x W40 x H64-76 cm (Desk), L43 x W43 x H38-46 cm (Chair). Also available as LF 0447P (Primary).",
    10990.00, 8)

# ============================================================
# PAGE 9: Single Seating Desk LF 0448 (Wire Storage)
# ============================================================
add_product("Single Seating Desk (Wire Storage)", "LF 0448",
    "Single seating desk with wire storage. Suitable for Primary, Middle and High Classes. Dimensions: L60 x W40 x H64-76 cm (Desk), L43 x W43 x H38-46 cm (Chair). Also available as LF 0448P (Primary).",
    6490.00, 9)

# ============================================================
# PAGE 10: Two products
# ============================================================
add_product("Dual Seater Desk (Wire Storage and Cantilever Frame)", "LF 0429",
    "Dual seater desk with wire storage and cantilever frame. Suitable for Middle and High Classes (9th-12th, ages 14-18). Dimensions: L120 x W50 x H76 cm (Desk), L38 x W40 x H46 cm (Chair). High-quality wooden top and metal frame. Heavy-duty metal structure with plastic bushes for floor protection.",
    16990.00, 10)

add_product("Single Desk (Wire Storage and Cantilever Frame)", "LF 0235",
    "Single-seater desk with wire storage and cantilever frame. Suitable for Middle and High Classes (9th-12th, ages 14-18). Dimensions: L60 x W40 x H76 cm (Desk), L38 x W40 x H46 cm (Chair). High-quality wooden top and metal frame. Heavy-duty metal structure with plastic bushes for floor protection.",
    8490.00, 10)

# ============================================================
# PAGE 11: Two products - LF 0405 and LF 0406
# ============================================================
add_product("Dual Seating Desk (Adjustable, Twin Storage) - LF 0405", "LF 0405",
    "Adjustable dual seating desk with twin storage compartments. Suitable for Middle and High Classes. Dimensions: L110 x W40 x H60-76 cm (Desk), L36 x W40 x H36-42 cm (Chair). Height adjustable in multiple positions. Heavy-duty metal frame with plastic bushes for floor protection.",
    9490.00, 11)

add_product("Dual Seating Desk (Adjustable, Twin Storage) Large - LF 0406", "LF 0406",
    "Adjustable dual seating desk with twin storage compartments, larger version. Dimensions: L120 x W45 x H60-78 cm (Desk), L36 x W38 x H36-42 cm (Chair). Suitable for Middle and High Classes. Heavy-duty metal frame with plastic bushes for floor protection.",
    9490.00, 11)

# ============================================================
# PAGE 13: LF 0407
# ============================================================
add_product("Dual Seating Desk (Adjustable, Wooden Top)", "LF 0407",
    "Adjustable dual seating desk with wooden top and twin storage compartments. Dimensions: L110 x W40 x H60-75 cm (Desk), L36 x W36 x H34-44 cm (Chair). Wooden seat and backrest. Suitable for Middle and High Classes. Heavy-duty metal frame with plastic bushes for floor protection.",
    11990.00, 13)

# ============================================================
# PAGE 14: LF 081 and LF 082
# ============================================================
add_product("Dual Seating Desk (Adjustable, Storage Compartment) - LF 081", "LF 081",
    "Adjustable dual seating desk with storage compartment. Suitable for Middle and High Classes (ages 11-18). Dimensions: L120 x W42 x H64-79 cm (Desk), L79 x W43 x H45 cm (Chair). High-quality plastic. Heavy-duty metal frame with plastic bushes for floor protection.",
    15990.00, 14)

add_product("Single Seater Desk (Adjustable, Storage Compartment) - LF 082", "LF 082",
    "Adjustable single seater desk with twin storage compartments. Suitable for Middle and High Classes (ages 11-18). Dimensions: L60 x W42 x H64-79 cm (Desk), L79 x W43 x H45 cm (Chair). High-quality plastic. Heavy-duty metal frame.",
    8990.00, 14)

# ============================================================
# PAGE 15: LF 029 Pentagon Study Desk
# ============================================================
add_product("Pentagon Study Desk", "LF 029",
    "Pentagon-shaped study desk. Suitable for Middle and High Classes (9th-12th, ages 14-18). Dimensions: L60 x W40 x H76 cm (Desk), L38 x W40 x H76 cm (Chair). High-quality wooden top with plastic seat and backrest. Heavy-duty metal frame with plastic bushes for floor protection.",
    7990.00, 15)

# ============================================================
# PAGE 16: LF 028 Single Seater Desk (Metal Storage)
# ============================================================
add_product("Single Seater Desk (Metal Storage)", "LF 028",
    "Single seater desk with metal storage compartments. Suitable for Middle and High Classes (ages 11-18). Dimensions: L46 x W60 x H63-78 cm (Desk), L79 x W43 x H45 cm (Chair). High-quality plastic top and metal frame. Height adjustable in multiple positions.",
    7990.00, 16)

# ============================================================
# PAGE 17: LF 0331
# ============================================================
add_product("Single Seater Desk (Adjustable, Metal Storage Box)", "LF 0331",
    "Adjustable single seater desk with metal frame storage box. Suitable for Middle and High Classes (ages 11-18). Dimensions: L60 x W40 x H60-75 cm (Desk), L38 x W40 x H34-44 cm (Chair). High-quality wooden top and metal frame. Height adjustable.",
    6490.00, 17)

# ============================================================
# PAGE 18: LF 035 Dual Seater Desk
# ============================================================
add_product("Dual Seater Desk (Wire Book Rack + Cantilever Frame)", "LF 035",
    "Dual seater desk with wire book rack and cantilever frame. Suitable for Middle Classes (6th-8th, ages 11-14). Dimensions: L120 x W45 x H73 cm (Desk), L79 x W43 x H45 cm (Chair). High-quality wooden top and metal frame. Heavy-duty metal structure with plastic bushes.",
    16990.00, 18)

# ============================================================
# PAGE 19: LF 025 Single Seater Desk
# ============================================================
add_product("Single Seater Desk (Wire Book Rack + Cantilever Frame) - LF 025", "LF 025",
    "Single seater desk with wire book rack and cantilever frame. Suitable for Middle Classes (6th-8th, ages 11-14). Dimensions: L60 x W45 x H73 cm (Desk), L79 x W43 x H45 cm (Chair). High-quality wooden top and metal frame.",
    8990.00, 19)

# ============================================================
# PAGE 20: LF 155 (Primary)
# ============================================================
add_product("Dual Seating Desk (Adjustable, Twin Storage) - Primary", "LF 155",
    "Adjustable dual seating desk with twin storage compartments for Primary Classes (1st-5th, ages 6-11). Dimensions: L90 x W38 x H55-70 cm (Desk), L70 x W41 x H35 cm (Chair). High-quality plastic top and metal frame.",
    9490.00, 20)

# ============================================================
# PAGE 21: LF 157 and LF 158
# ============================================================
add_product("Dual Seater Desk (Twin Plastic Storage) - Primary", "LF 157",
    "Dual seater desk with twin plastic storage compartments for Primary Classes. Dimensions: L96 x W36 x H61 cm (Desk), L70 x W41 x H35 cm (Chair). High-quality plastic. Suitable for ages 6-14.",
    7490.00, 21)

add_product("Dual Seating Desk (Adjustable, Twin Storage) - Primary", "LF 158",
    "Adjustable dual seating desk with twin storage compartments for Primary Classes (1st-5th, ages 6-11). Dimensions: L95 x W47 x H51-63 cm (Desk), L70 x W41 x H35 cm (Chair). High-quality plastic top and metal frame.",
    11990.00, 21)

# ============================================================
# PAGE 22: LF 159
# ============================================================
add_product("Dual Seating Desk (Adjustable, Twin Plastic Storage) - Primary Large", "LF 159",
    "Large adjustable dual seating desk with twin plastic storage compartments for Primary Classes (1st-5th, ages 6-11). Dimensions: L120 x W42 x H68-80 cm (Desk), L70 x W41 x H35 cm (Chair). High-quality plastic top and metal frame.",
    11990.00, 22)

# ============================================================
# PAGE 23: LF 0504 (Pre Classes)
# ============================================================
add_product("Rectangular Dual-Seater Desk (Twin Metal Storage) - Pre", "LF 0504",
    "Rectangular dual-seater desk with twin metal storage compartments for Pre Classes (Play-UKG, ages 2-6). Dimensions: L90 x W38 x H55 cm (Desk - wooden top), L27 x W27 x H30 cm (Chair - wooden). Heavy-duty metal frame.",
    8990.00, 23)

# ============================================================
# PAGE 24: LF 0512
# ============================================================
add_product("Trapezium Shaped Desk (Wire Storage + Cantilever Frame) - Pre", "LF 0512",
    "Trapezium shaped desk with wire storage and cantilever frame for Pre Classes (Play-UKG, ages 2-6). Dimensions: L58 x W30 x H58 cm (Desk - wooden top), L30 x W30 x H34 cm (Chair - wooden). Heavy-duty metal frame.",
    4290.00, 24)

# ============================================================
# PAGE 25: LF 0513
# ============================================================
add_product("Desk and Chair (Adjustable) Set - Pre", "LF 0513",
    "Adjustable desk and chair set for Pre Classes (Play-UKG, ages 2-6). Set of 1 Table and 2 Chairs. Dimensions: L60 x W60 x H48-60 cm (Desk - wooden top), L30 x W28 x H53-56 cm (Chair - plastic).",
    7990.00, 25)

# ============================================================
# PAGE 26-27: Tables (LF 311, 314, 315)
# ============================================================
add_product("Moon Table (Adjustable) - Pre", "LF 311",
    "Adjustable moon-shaped table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L180 x W90 cm, height adjustable from 40-63 cm. Without chairs.",
    9990.00, 26)

add_product("Round Table (Adjustable) - Pre", "LF 314",
    "Adjustable round table for Pre Classes (Play-UKG, ages 2-6). Diameter: 110 cm, height adjustable from 40-63 cm. Without chairs.",
    9990.00, 26)

add_product("Rectangle Table (Adjustable) - Pre", "LF 315",
    "Adjustable rectangle table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L110 x W100 x H63 cm, height adjustable. Without chairs.",
    7990.00, 27)

# ============================================================
# PAGE 28-30: More Pre Tables
# ============================================================
add_product("Moon Table (Adjustable) - Pre Premium", "LF 211",
    "Premium adjustable moon-shaped table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L180 x W90 cm, height adjustable from 40-63 cm. Without chairs.",
    9990.00, 28)

add_product("Round Table (Adjustable) - Pre Premium", "LF 214",
    "Premium adjustable round table for Pre Classes (Play-UKG, ages 2-6). Diameter: 110 cm, height adjustable from 40-63 cm. Without chairs.",
    9990.00, 29)

add_product("Rectangle Table (Adjustable) - Pre Premium", "LF 215",
    "Premium adjustable rectangle table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L112 x W60 x H58 cm, height adjustable. Without chairs.",
    7990.00, 29)

add_product("Rectangle Table - Pre", "LF 110",
    "Rectangle table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L155 x W76 x H48 cm. Without chairs.",
    7990.00, 30)

# ============================================================
# PAGE 31-33: More Pre Tables
# ============================================================
add_product("Moon Table - Pre", "LF 111",
    "Moon-shaped table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L155 x W84 x H51 cm. Without chairs.",
    6990.00, 31)

add_product("Square Table - Pre", "LF 113",
    "Square table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L61 x W61 x H51 cm. Without chairs.",
    3990.00, 31)

add_product("Round Table - Pre", "LF 114",
    "Round table for Pre Classes (Play-UKG, ages 2-6). Diameter: 115 cm, Height: 51 cm. Without chairs.",
    6990.00, 32)

add_product("Round Table Small - Pre", "LF 114S",
    "Small round table for Pre Classes (Play-UKG, ages 2-6). Diameter: 90 cm, Height: 51 cm. Without chairs.",
    5990.00, 32)

add_product("Rectangle Table - Pre Medium", "LF 115",
    "Rectangle table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L122 x W61 x H51 cm. Without chairs.",
    5490.00, 33)

add_product("Rectangle Table Small - Pre", "LF 115S",
    "Small rectangle table for Pre Classes (Play-UKG, ages 2-6). Dimensions: L92 x W46 x H51 cm. Without chairs.",
    3490.00, 33)

# ============================================================
# PAGE 34: Premium Furniture
# ============================================================
add_product("Premium Activity Table with Chairs", "LF 207",
    "Premium activity table set. Size: L120xW105xH50 CM. Without chairs. PREMIUM quality.",
    4990.00, 34)

add_product("Premium Round Table H56", "LF 202",
    "Premium round table. Size: H56 CM. Without chairs. PREMIUM quality.",
    14990.00, 34)

add_product("Premium Round Table Large", "LF 206",
    "Premium large round table. Size: Dia x H53 CM. Without chairs. PREMIUM quality.",
    17990.00, 34)

add_product("Premium Rectangle Table Large", "LF 205",
    "Premium rectangle table. Size: L120xW60xH53 CM. Without chairs. PREMIUM quality.",
    24990.00, 34)

add_product("Premium Small Table H27", "LF 201",
    "Premium small table. Size: H27 CM. Without chairs. PREMIUM quality.",
    4990.00, 34)

# ============================================================
# PAGE 35: Premium Furniture (LF 1421-1425)
# ============================================================
add_product("Premium Bookshelf 1", "LF 1421",
    "Premium bookshelf. Size: L44xW35xH50 CM. PREMIUM quality.",
    15990.00, 35)

add_product("Premium Bookshelf 2", "LF 1422",
    "Premium bookshelf. Size: L44xW35xH50 CM. PREMIUM quality.",
    15990.00, 35)

add_product("Premium Bookshelf 3", "LF 1423",
    "Premium bookshelf. Size: L44xW35xH50 CM. PREMIUM quality.",
    15990.00, 35)

add_product("Premium Small Cabinet", "LF 1424",
    "Premium small cabinet. Size: L36xW27.8xH25 CM. PREMIUM quality.",
    21990.00, 35)

add_product("Premium Tall Cabinet", "LF 1425",
    "Premium tall cabinet. Size: L44xW35xH82 CM. PREMIUM quality.",
    9990.00, 35)

# ============================================================
# PAGE 36: Play Kitchen & Workbench
# ============================================================
add_product("Premium Play Kitchen with Accessories", "LF 1426",
    "A modern pretend play kitchen with stove, oven, sink, washing machine, shelves, and hanging utensils. Encourages creativity and role play while building motor skills. Durable and child-safe design. Size: L120xW29.5xH98 CM.",
    16990.00, 36)

add_product("Creative Wooden Workbench", "LF 1428",
    "A fun and educational wooden workbench designed to inspire creativity and hands-on learning. Features colorful gears, tools, bolts, and storage space. Helps kids develop motor skills, problem-solving, and imaginative play. Size: L68xW30xH88 CM.",
    24990.00, 36)

add_product("Premium Modern Play Kitchen", "LF 1427",
    "A stylish and durable wooden play kitchen with realistic fridge, stove, sink, microwave, washing machine, and storage space. Features turning knobs, hanging utensils, and modern design. Size: L122xW30xH109.5 CM.",
    14990.00, 36)

# ============================================================
# PAGE 37: (Missing prices - create with price=0)
# ============================================================
add_product("Premium Wall Shelf Unit", "LF 1451",
    "Premium wall shelf unit. Size: L120xW30xH80 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

add_product("Premium Wall Shelf Unit Double", "LF 1452",
    "Premium wall shelf unit double. Size: L120xW30xH80 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

add_product("Premium Storage Cabinet Small", "LF 1453",
    "Premium storage cabinet. Size: L80xW40xH67 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

add_product("Premium Storage Cabinet Small Double", "LF 1454",
    "Premium storage cabinet double. Size: L80xW40xH67 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

add_product("Premium Shelf Unit Wide", "LF 1455",
    "Premium wide shelf unit. Size: L104xW30xH80 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

add_product("Premium Shelf Unit Narrow", "LF 1456",
    "Premium narrow shelf unit. Size: L84xW30xH80 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 37)

# ============================================================
# PAGE 38: Shelves
# ============================================================
add_product("Premium Display Shelf", "LF 1501",
    "Premium display shelf. Size: L90xW20xH58 CM. PREMIUM quality.",
    9990.00, 38)

add_product("Premium Display Shelf Style 2", "LF 1503",
    "Premium display shelf style 2. Size: L90xW20xH58 CM. PREMIUM quality.",
    9990.00, 38)

add_product("Premium Display Shelf Style 3", "LF 1502",
    "Premium display shelf style 3. Size: L90xW20xH58 CM. PREMIUM quality.",
    9990.00, 38)

add_product("Premium Tall Display Shelf", "LF 1504",
    "Premium tall display shelf. Size: L90xW20xH92 CM. PREMIUM quality.",
    9990.00, 38)

add_product("Premium Storage Unit", "LF 1458",
    "Premium storage unit. Size: L124xW40xH50 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 38)

add_product("Premium Extra Long Shelf", "LF 1459",
    "Premium extra long shelf unit. Size: L298xW30xH116 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 38)

add_product("Premium Shelf Unit Standard", "LF 1457",
    "Premium shelf unit. Size: L124xW30xH80 CM. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 38)

# ============================================================
# PAGE 39: Activity Carpets
# ============================================================
add_product("Sports Activity Carpet", "LF 0701",
    "Sports-themed activity carpet. Size: L220xW180 CM. Premium quality. Perfect for preschool and classroom activity areas.",
    24990.00, 39)

add_product("Alphabet Activity Carpet", "LF 0702",
    "Alphabet-themed activity carpet. Size: L220xW180 CM. Premium quality. Educational design for early learning.",
    24990.00, 39)

add_product("Space Activity Carpet", "LF 0703",
    "Space-themed activity carpet. Size: L200xW200 CM. Premium quality.",
    24990.00, 39)

add_product("Numbers Activity Carpet", "LF 0704",
    "Numbers-themed activity carpet. Size: L200xW200 CM. Premium quality. Educational design for early learning.",
    24990.00, 39)

add_product("Shapes Activity Carpet", "LF 0705",
    "Shapes-themed activity carpet. Size: L230xW160 CM. Premium quality. Educational design for early learning.",
    24990.00, 39)

# ============================================================
# PAGE 40-41: Animal Desks
# ============================================================
add_product("Single Seater Dolphin Desk", "LF 401",
    "Single seater dolphin-shaped desk. Suitable for Pre Classes (Play-UKG, ages 2-6). Dimensions: L74 x W40 x H60 cm. Fun animal theme for engaging learning.",
    3790.00, 40)

add_product("Single Seater Giraffe Desk", "LF 402",
    "Single seater giraffe-shaped desk. Suitable for Pre Classes (Play-UKG, ages 2-6). Dimensions: L74 x W40 x H60 cm. Fun animal theme for engaging learning.",
    3790.00, 40)

add_product("Double Seater Dolphin Desk", "LF 411",
    "Double seater dolphin-shaped desk. Suitable for Pre Classes (Play-UKG, ages 2-6). Dimensions: L74 x W74 x H60 cm. Fun animal theme.",
    5990.00, 41)

add_product("Double Seater Giraffe Desk", "LF 412",
    "Double seater giraffe-shaped desk. Suitable for Pre Classes (Play-UKG, ages 2-6). Dimensions: L74 x W74 x H60 cm. Fun animal theme.",
    5990.00, 41)

# ============================================================
# PAGE 42: Soft Seating (missing prices)
# ============================================================
add_product("Soft Seating Rectangle", "LF 1481",
    "Premium soft seating. Size: L120 x W60 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

add_product("Soft Seating Square Small", "LF 1482",
    "Premium soft seating square. Size: L60 x W51 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

add_product("Soft Seating Square Medium", "LF 1483",
    "Premium soft seating square. Size: L60 x W60 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

add_product("Soft Seating Square Medium Style 2", "LF 1484",
    "Premium soft seating square. Size: L60 x W60 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

add_product("Soft Seating Square Large", "LF 1485",
    "Premium soft seating square. Size: L60 x W60 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

add_product("Soft Seating Rectangle Large", "LF 1486",
    "Premium soft seating large rectangle. Size: L120 x W90 cm. PREMIUM quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 42)

# ============================================================
# PAGE 43: Play Animal Seating
# ============================================================
add_product("Play Animal Seating", "LF 0421",
    "Fun play animal seating. Size: L242xW44xH50 CM. Premium soft play seating. Perfect for preschool reading corners and play areas.",
    24990.00, 43)

add_product("Play Crocodile Seating", "LF 0422",
    "Fun play crocodile seating. Size: L260xW44xH52 CM. Premium soft play seating. Perfect for preschool reading corners.",
    79990.00, 43)

add_product("Play Shark Seating", "LF 0423",
    "Fun play shark-themed seating. Size: L100xW22xH27 CM. Premium soft play seating.",
    24990.00, 43)

# ============================================================
# PAGE 44-45: Bench, Bed
# ============================================================
add_product("Y-Connect Seat", "LF 960",
    "Y-Connect bench seat. Dimensions: L72.5xW83xH39.5 CM. Per piece pricing.",
    6990.00, 44)

add_product("Plastic Bench", "LF 136",
    "Plastic bench for Pre Classes (Play-UKG, ages 2-6). Dimensions: L80 x W48 x H60 cm.",
    4190.00, 45)

add_product("Children Bed", "LF 507",
    "Children bed suitable for Pre Classes (Play-UKG, ages 2-6). Dimensions: L138 x W58 x H28 cm.",
    3490.00, 45)

# ============================================================
# PAGE 46: Chairs (12 variants)
# ============================================================
add_product("Plastic Chair 24cm", "LF 106",
    "Plastic chair, height 24 cm. Suitable for Pre classes.",
    390.00, 46)

add_product("Plastic Chair 26cm", "LF 116",
    "Plastic chair, height 26 cm. Suitable for Pre/Primary classes.",
    590.00, 46)

add_product("Adjustable Plastic Chair 26-30cm", "LF 186",
    "Adjustable plastic chair, height 26/28/30 cm. Suitable for Pre/Primary classes.",
    1090.00, 46)

add_product("Plastic Handle Chair 28cm", "LF 146",
    "Plastic chair with handle, height 28 cm. Suitable for Pre classes.",
    990.00, 46)

add_product("Metal Chair 30cm", "LF 176",
    "Metal chair, height 30 cm. Suitable for Primary classes.",
    1790.00, 46)

add_product("Plastic Chair 31cm", "LF 126",
    "Plastic chair, height 31 cm. Suitable for Primary classes.",
    690.00, 46)

add_product("Plastic Chair 35cm", "LF 127",
    "Plastic chair, height 35 cm. Suitable for Middle classes.",
    890.00, 46)

add_product("Metal Handle Chair 35cm", "LF 156",
    "Metal chair with handle, height 35 cm. Suitable for Middle classes.",
    1890.00, 46)

add_product("Metal Handle Chair 36cm", "LF 166",
    "Metal chair with handle, height 36 cm. Suitable for Middle/High classes.",
    2090.00, 46)

add_product("Plastic Chair 45cm", "LF 129",
    "Plastic chair, height 45 cm. Suitable for High classes.",
    1590.00, 46)

add_product("Plastic Chair 40cm", "LF 128",
    "Plastic chair, height 40 cm. Suitable for Middle/High classes.",
    1290.00, 46)

# ============================================================
# PAGE 47-49: Playhouses & Cottages
# ============================================================
add_product("Mini Home and Kitchen Playhouse", "LF 801",
    "Mini home and kitchen playhouse. Size: L99 x W92.9 x H140 CM. Premium quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 47)

add_product("Junior Living House", "LF 802",
    "Junior living house playhouse. Size: L124 x W172.5 x H163 CM. Premium quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 47)

add_product("Chocolate Playhouse", "LF 901",
    "Chocolate-themed playhouse. Size: L125xW135xH143 CM. Fun play equipment for indoor use.",
    49990.00, 48)

add_product("Playhouse Classic", "LF 902",
    "Classic playhouse. Size: L103xW109xH131 CM. Fun play equipment for indoor use.",
    29990.00, 48)

add_product("Royal Cottage", "LF 903",
    "Royal cottage playhouse. Size: L134.6xW81.3xH124.5 CM. Premium quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 49)

add_product("Classic Cottage", "LF 904",
    "Classic cottage playhouse. Size: L97.5xW64.3xH94.4 CM. Premium quality. PRICE NOT LISTED IN CATALOGUE - contact for pricing.",
    0.00, 49)

# ============================================================
# PAGE 50-56: Slides & Swings
# ============================================================
add_product("Slide Large - LF 102", "LF 102",
    "Large slide for indoor play. Size: L204xW220xH180 CM.",
    39990.00, 50)

add_product("Slide Medium - LF 103", "LF 103",
    "Medium slide for indoor play. Size: L274xW116xH134 CM.",
    29990.00, 50)

add_product("Slide Extra Large - LF 105", "LF 105",
    "Extra large slide for indoor play. Size: L274xW213xH152 CM.",
    44990.00, 50)

add_product("Multi Colour Gambola", "LF 101MC",
    "Multi-colour Gambola play structure. Size: L308xW175xH170 CM. Large indoor play equipment.",
    79990.00, 51)

add_product("Chocolate Colour Gambola", "LF 101CC",
    "Chocolate colour Gambola play structure. Size: L308xW175xH170 CM. Large indoor play equipment.",
    79990.00, 51)

add_product("Rabbit Slide", "LF 912",
    "Small rabbit-themed slide for toddlers. Size: L110xW50xH70 CM.",
    2790.00, 52)

add_product("Junior Slide", "LF 911",
    "Junior slide for toddlers. Size: L110xW70xH80 CM.",
    2990.00, 52)

add_product("Rabbit Slide Big", "LF 912A",
    "Large rabbit-themed slide. Size: L176xW74xH84 CM.",
    4790.00, 52)

add_product("Castle Slide", "LF 915",
    "Castle-themed slide. Size: L150xW76xH94 CM.",
    5990.00, 53)

add_product("Space Slide", "LF 917",
    "Space-themed slide. Size: L150xW76xH94 CM.",
    5990.00, 53)

add_product("Dolphin Slide", "LF 916",
    "Dolphin-themed slide. Size: L150xW76xH94 CM.",
    5990.00, 53)

add_product("Space Slide with Swing", "LF 924",
    "Space-themed slide with swing combination. Size: L177xW156xH113 CM.",
    11990.00, 54)

add_product("Castle Slide with Swing", "LF 922",
    "Castle-themed slide with swing combination. Size: L177xW156xH113 CM.",
    11990.00, 54)

add_product("Space Swing", "LF 921",
    "Space-themed swing. Size: L78xW94xH113 CM.",
    6490.00, 54)

add_product("Castle Swing", "LF 919",
    "Castle-themed swing. Size: L78xW94xH113 CM.",
    6490.00, 54)

add_product("Dolphin Swing", "LF 920",
    "Dolphin-themed swing. Size: L78xW94xH113 CM.",
    6490.00, 54)

add_product("Dolphin Slide with Swing", "LF 923",
    "Dolphin-themed slide with swing combination. Size: L177xW156xH113 CM.",
    11990.00, 54)

add_product("Slide Standard - LF 990", "LF 990",
    "Standard slide. Size: L162xW73xH96 CM.",
    9990.00, 55)

add_product("Slide Medium Curve - LF 972", "LF 972",
    "Medium curved slide. Size: L160xW85xH110 CM.",
    8990.00, 55)

add_product("Bear Slide", "LF 971",
    "Bear-themed slide. Size: L168xW86xH114 CM.",
    9990.00, 55)

add_product("Elephant Slide", "LF 970",
    "Elephant-themed slide. Size: L168xW86xH108 CM.",
    8990.00, 55)

add_product("Elephant Slide with Swing", "LF 976",
    "Elephant-themed slide with swing. Size: L160xW170xH114 CM.",
    16990.00, 56)

add_product("Elephant Swing", "LF 973",
    "Elephant-themed swing. Size: L90xW60xH123 CM.",
    9990.00, 56)

add_product("Multicolour Swing", "LF 975",
    "Multicolour swing. Size: L90xW60xH123 CM.",
    8990.00, 56)

add_product("Multicolour Slide with Swing", "LF 978",
    "Multicolour slide with swing combination. Size: L160xW170xH114 CM.",
    15990.00, 56)

add_product("Bear Slide with Swing", "LF 977",
    "Bear-themed slide with swing. Size: L160xW170xH114 CM.",
    16990.00, 56)

add_product("Bear Swing", "LF 974",
    "Bear-themed swing. Size: L90xW60xH123 CM.",
    9990.00, 56)

# ============================================================
# PAGE 57: Shelves & Dustbins
# ============================================================
add_product("Toy Shelf", "LF 934-A",
    "Toy shelf for classroom organization. Size: L91xW43xH81 CM.",
    6990.00, 57)

add_product("Book Shelf", "LF 9053-2",
    "Book shelf for classroom library. Size: L80xW39xH78 CM.",
    4490.00, 57)

add_product("Plastic Shoe Rack", "LF 9130-5",
    "Plastic shoe rack. Size: L120xW24xH40 CM. Per piece pricing.",
    6490.00, 57)

add_product("Dolphin Dustbin", "LF 998",
    "Dolphin-themed dustbin. Size: L52xW66xH87 CM. Fun design for classroom use.",
    2490.00, 57)

add_product("Pencil Dustbin", "LF 999",
    "Pencil-shaped dustbin. Size: L33xW33xH73 CM. Per piece pricing.",
    2990.00, 57)

add_product("Pencil Dustbin Tall", "LF 999B",
    "Tall pencil-shaped dustbin. Size: L30xW30xH101 CM. Per piece pricing.",
    6990.00, 57)

# ============================================================
# PAGE 58: Tunnels
# ============================================================
add_product("Multicolor Tunnel", "LF 932A",
    "Multicolor play tunnel. Size: L215xW100xH103 CM.",
    19990.00, 58)

add_product("Caterpillar Tunnel", "LF 932B",
    "Caterpillar-themed play tunnel. Size: L190xW110xH122 CM.",
    19990.00, 58)

add_product("Roller Coaster Rideon", "LF 450",
    "Roller coaster ride-on toy. Size: 310x76x35 CM.",
    14990.00, 58)

add_product("Bull Tunnel Set", "LF 9126",
    "Bull tunnel set of 4 pieces.",
    8490.00, 58)

add_product("Quarter Round", "LF 9052-A",
    "Quarter round play equipment. Size: 133x42 cm.",
    13990.00, 58)

# ============================================================
# PAGE 59: Rockers (9 items)
# ============================================================
add_product("Dolphin Rocker", "LF 925D",
    "Dolphin-shaped rocker toy. Size: L88xW29xH53 CM.",
    2690.00, 59)

add_product("Rocking Horse", "LF 629",
    "Classic rocking horse toy. Size: L85xW30.5xH44 CM.",
    1990.00, 59)

add_product("Fish Rocker", "LF 925B",
    "Fish-shaped rocker toy. Size: L75xW30xH48 CM.",
    2690.00, 59)

add_product("Elephant Rocker", "LF 925C",
    "Elephant-shaped rocker toy. Size: L75xW30xH44 CM.",
    1990.00, 59)

add_product("Hen Rocker", "LF 925A",
    "Hen-shaped rocker toy. Size: L78xW30xH44 CM.",
    1990.00, 59)

add_product("Smiley Wagon Rideon Rocker", "LF 628",
    "Smiley face wagon that works as rideon and rocker. Size: L75xW29xH55 CM.",
    1990.00, 59)

add_product("Horse Rideon Rocker", "LF 627",
    "Horse-shaped rideon and rocker. Size: L70xW34xH51 CM.",
    2390.00, 59)

add_product("Horse Rideon Rocker with Handle", "LF 627A",
    "Horse-shaped rideon and rocker with handle. Size: L70xW34xH48 CM.",
    2390.00, 59)

add_product("Pony Rocking Rideon", "LF 624",
    "Pony rocking ride-on toy. Size: L70xW34xH106 CM.",
    2790.00, 59)

# ============================================================
# PAGE 60: Rockers & See-Saws
# ============================================================
add_product("Crab See-Saw", "LF 108B",
    "Crab-shaped see-saw. Size: L110xW39xH45 CM. Per piece pricing.",
    4290.00, 60)

add_product("Fish Rocker Tall", "LF 9122-3",
    "Tall fish-shaped rocker. Size: L91xW27xH89 CM. Per piece pricing.",
    4990.00, 60)

add_product("Pony 3 Way Rocker", "LF 417",
    "Pony 3-way rocker. Size: L106xW11xH42 CM.",
    3990.00, 60)

add_product("Dolphin 3 Way Rocker", "LF 416",
    "Dolphin 3-way rocker. Size: L149xW49xH40 CM.",
    3990.00, 60)

add_product("See-Saw", "LF 419",
    "Classic see-saw. Size: L150xW32xH60 CM. Per piece pricing.",
    5990.00, 60)

# ============================================================
# PAGE 61: Rideon Vehicles
# ============================================================
add_product("Coupe Car", "LF 418",
    "Coupe car ride-on toy. Size: L76xW48xH89 CM. Per piece pricing.",
    9490.00, 61)

add_product("Motorcycle Rideon", "LF 928B",
    "Motorcycle ride-on toy.",
    2690.00, 61)

add_product("Swing Car", "LF 926A",
    "Swing car ride-on toy.",
    2690.00, 61)

add_product("Police Car", "LF 830",
    "Police car ride-on toy. Size: L90xW50xH95 CM. Per piece pricing.",
    9490.00, 61)

add_product("Car Rideon", "LF 440",
    "Car ride-on toy. Size: L86xW50xH50 CM.",
    6490.00, 61)

# ============================================================
# PAGE 62: Rideons & Tricycles (8 items)
# ============================================================
add_product("Tricycle", "LF 929A",
    "Children's tricycle. Size: L55xW32xH45 CM.",
    3190.00, 62)

add_product("Horse Rideon Brown", "LF 927C",
    "Horse ride-on toy, brown. Size: L52xW26xH51 CM.",
    2290.00, 62)

add_product("Horse Rideon Grey", "LF 927E",
    "Horse ride-on toy, grey. Size: L58xW40xH37 CM.",
    2290.00, 62)

add_product("Smiley Wagon Rideon", "LF 927F",
    "Smiley face wagon ride-on toy. Size: L57xW29xH46 CM.",
    1790.00, 62)

add_product("Plane Rideon", "LF 927-D",
    "Plane-shaped ride-on toy. Size: L58xW26xH41 CM.",
    3190.00, 62)

add_product("Tricycle Large", "LF 929B",
    "Large children's tricycle. Size: L62xW34xH42 CM.",
    2690.00, 62)

add_product("Tricycle Extra Large", "LF 929C",
    "Extra large children's tricycle. Size: L66xW36xH45 CM.",
    2290.00, 62)

add_product("Dog Rideon", "LF 927B",
    "Dog-shaped ride-on toy. Size: L56xW34xH45 CM.",
    1790.00, 62)

# ============================================================
# PAGE 63: Balls & Rideons
# ============================================================
add_product("Plastic Balls (200 pcs)", "LFT 200P",
    "Plastic ball set of 200 pieces, 6.5 CM size. Perfect for ball pits.",
    2299.00, 63)

add_product("Plastic Balls (100 pcs)", "LFT 100",
    "Plastic ball set of 100 pieces, 8.5 CM size. Perfect for ball pits.",
    1299.00, 63)

add_product("Horse Rideon - LFT", "LFT 444",
    "Horse ride-on toy. Per piece pricing. Master CTN: 9 pcs.",
    1499.00, 63)

add_product("Elephant Rideon - LFT", "LFT 344",
    "Elephant ride-on toy. Per piece pricing. Master CTN: 12 pcs.",
    1799.00, 63)

add_product("Kitten Rideon", "LFT 333",
    "Kitten ride-on toy. Per piece pricing. Master CTN: 9 pcs.",
    1499.00, 63)

add_product("Sport Tricycle", "LF 933",
    "Sport-style children's tricycle. Size: L67xW38xH53 CM.",
    3790.00, 63)

# ============================================================
# PAGE 64: Ball Pools
# ============================================================
add_product("Ball Pool 5 Pcs Set", "LF 961A",
    "Ball pool set of 5 pieces (without balls). Size: 128x128x78 CM.",
    9490.00, 64)

add_product("Ball Pool 6 Pcs Set", "LF 101-5",
    "Ball pool set of 6 pieces (without balls). Size: 80x60x2.5 CM.",
    5990.00, 64)

add_product("Ball Pool 6 Pcs Round", "LF 962",
    "Round ball pool set of 6 pieces (without balls). Diameter 6.5ft x Height 61cm.",
    9990.00, 64)

add_product("Ball Pool 2.7m2", "LF 963",
    "Large ball pool cover area 2.7 m2.",
    17990.00, 64)

add_product("Ball Pool 4.64m2", "LF 964",
    "Extra large ball pool cover area 4.64 m2.",
    21990.00, 64)

# ============================================================
# PAGE 65: Play Junction Fence
# ============================================================
add_product("Play Junction Fence Red", "LF 135",
    "Play junction fence panels, set of 4 pcs. Size: 105x75 CM (each). Red.",
    9990.00, 65)

add_product("Play Junction Fence Blue", "LF 135B",
    "Play junction fence panels, set of 4 pcs. Size: 105x75 CM (each). Blue.",
    9990.00, 65)

add_product("Play Junction Fence White", "LF 135W",
    "Play junction fence panels, set of 4 pcs. Size: 105x75 CM (each). White.",
    9990.00, 65)

# ============================================================
# PAGE 66: Sandpits
# ============================================================
add_product("Crab Sandpit", "LF 377",
    "Crab-shaped sandpit. Size: L81xW94xH30 CM.",
    8490.00, 66)

add_product("Pumpkin Sandpit", "LF 378",
    "Pumpkin-shaped sandpit. Size: L96xW96xH30 CM.",
    7990.00, 66)

add_product("Frog Sandpit", "LF 380",
    "Frog-shaped sandpit. Size: L104xW110xH35 CM.",
    7990.00, 66)

add_product("Turtle Sandpit Large", "LF 379",
    "Large turtle-shaped sandpit. Size: L101xW101xH30 CM.",
    6990.00, 66)

add_product("Turtle Sandpit Small", "LF 376",
    "Small turtle-shaped sandpit. Size: L92xW70xH17 CM.",
    4490.00, 66)

add_product("Water Sand Deluxe Set", "LF 375",
    "Water and sand deluxe play set. Size: L76xW66xH43 CM.",
    4490.00, 66)

# ============================================================
# PAGE 67: Play Equipment
# ============================================================
add_product("Wall Basketball - LF 930C", "LF 930C",
    "Wall-mounted basketball hoop.",
    1990.00, 67)

add_product("Wall Basketball Premium - LF 930D", "LF 930D",
    "Premium wall-mounted basketball hoop. Per piece pricing.",
    899.00, 67)

add_product("Toy Trolly", "LF 9126-6",
    "Toy trolly for storage. Size: L90xW34xH40 CM. Per piece pricing.",
    2690.00, 67)

add_product("Balancing Bridge Set", "LF 142",
    "Balancing bridge set of 4 pieces. Size: L22.5xW12xH39.5 CM (each).",
    5490.00, 67)

add_product("Elephant Ring Toss", "LF 549",
    "Elephant-themed ring toss game.",
    4490.00, 67)

add_product("Hit Me (2 in 1) Game", "LF 141",
    "2-in-1 hit me game. Size: L33.5 x H107 CM. Per piece pricing.",
    2490.00, 67)

# ============================================================
# PAGE 68: Building Blocks
# ============================================================
add_product("Plastic Building Blocks (45 Pcs)", "LF 9177-2",
    "Plastic building blocks set of 45 pieces.",
    7990.00, 68)

add_product("Plastic Blocks (50 Pcs)", "LF 118-2",
    "Plastic blocks set of 50 pieces.",
    3490.00, 68)

# ============================================================
# PAGE 69: Various Play Equipment
# ============================================================
add_product("Basketball Stand", "LF 930",
    "Children's basketball stand. Size: D20 x W10 x H70 cm.",
    3190.00, 69)

add_product("Big Basketball Stand", "LF 930B",
    "Large children's basketball stand. Size: L70 x W58 x H159-215cm.",
    4990.00, 69)

add_product("3-in-1 Magnetic Easel", "LF 931",
    "3-in-1 magnetic easel for drawing and learning. Size: L55xW68xH107 CM.",
    4990.00, 69)

add_product("Small Tray", "LF 13-6",
    "Small plastic tray. Size: L26xW35xH11 CM. Per piece pricing.",
    299.00, 69)

add_product("Large Tray", "LF 13-5",
    "Large plastic tray. Size: L31xW42xH10 CM. Per piece pricing.",
    349.00, 69)

add_product("Blocks 16 Pcs", "LFT 3992D",
    "Building blocks set of 16 pieces.",
    1399.00, 69)

add_product("Blocks 32 Pcs", "LFT 3994P",
    "Building blocks set of 32 pieces.",
    2599.00, 69)

# ============================================================
# PAGE 70: Trampolines
# ============================================================
add_product("Trampoline 36 inch", "LF 536",
    "Indoor trampoline, 36 inch diameter.",
    4990.00, 70)

add_product("Trampoline 45 inch", "LF 545",
    "Indoor trampoline, 45 inch diameter.",
    6490.00, 70)

add_product("Trampoline 55 inch", "LF 55",
    "Indoor trampoline, 55 inch diameter.",
    11990.00, 70)

add_product("Trampoline 72 inch", "LF 72",
    "Indoor trampoline, 72 inch diameter.",
    20990.00, 70)

add_product("Trampoline 96 inch", "LF 96",
    "Indoor trampoline, 96 inch diameter.",
    24990.00, 70)

add_product("Trampoline 120 inch", "LF 120",
    "Indoor trampoline, 120 inch diameter.",
    31990.00, 70)

add_product("Trampoline 144 inch", "LF 144T",
    "Large indoor trampoline, 144 inch diameter.",
    39990.00, 70)

add_product("Trampoline 168 inch", "LF 168",
    "Extra large indoor trampoline, 168 inch diameter.",
    43990.00, 70)

# ============================================================
# PAGE 71: Gym Equipment
# ============================================================
add_product("Twister Exercise Machine", "LF 605",
    "Children's twister exercise machine. Size: L43xW30xH99 CM.",
    14990.00, 71)

add_product("Treadmill Exercise Machine", "LF 604",
    "Children's treadmill exercise machine. Size: L86xW35xH99 CM.",
    11990.00, 71)

add_product("Cycling Exercise Machine", "LF 606",
    "Children's cycling exercise machine. Size: L48xW35xH71 CM.",
    11990.00, 71)

add_product("Balancer Exercise Machine", "LF 601",
    "Children's balancer exercise machine. Size: L66xW43xH86 CM.",
    11990.00, 71)

add_product("Flexer Exercise Machine", "LF 602",
    "Children's flexer exercise machine. Size: L78xW38xH99 CM.",
    8490.00, 71)

add_product("Rowing Exercise Machine", "LF 603",
    "Children's rowing exercise machine. Size: L86xW33xH45 CM.",
    11490.00, 71)

# ============================================================
# PAGE 72: Toy Shelves
# ============================================================
add_product("Toy Shelf 3 Tier", "LF 935",
    "3-tier toy shelf. Size: L119xW43xH81 CM.",
    8990.00, 72)

add_product("Toy Shelf 3 Tier Narrow", "LF 936",
    "Narrow 3-tier toy shelf. Size: L98xW35xH81 CM.",
    8990.00, 72)

add_product("Toy Shelf 4 Tier", "LF 937",
    "4-tier toy shelf. Size: L142xW35xH81 CM.",
    12990.00, 72)

# ============================================================
# PAGE 73: Tent Houses
# ============================================================
add_product("Tent House", "LF 5532",
    "Tent house for indoor play. Size: L91.5 x W91.5 x H109.22 CM.",
    2490.00, 73)

add_product("Tunnel Tent House", "LFT 1104C",
    "Tunnel tent house. Size: L248.92 x W72.39 x H90.17 CM.",
    5990.00, 73)

add_product("Large Play Tent", "LF 5052",
    "Large play tent. Size: L176xW89xH89 CM.",
    2990.00, 73)

add_product("Play Tunnel", "LF 5012",
    "Play tunnel. Size: L45xW45xH105 CM.",
    1490.00, 73)

add_product("Tunnel Tent", "LF 1101C",
    "Tunnel tent. Size: L142 x Dia 45 cm.",
    1990.00, 73)

add_product("Pop-Up Tent", "LF 1103C",
    "Pop-up tent. Size: L114 x W71 x H68 cm.",
    2790.00, 73)

# ============================================================
# PAGE 74: Sports Equipment
# ============================================================
add_product("Divider 10 Pcs", "LF 52",
    "Sports divider set of 10 pieces.",
    1190.00, 74)

add_product("Divider 25 Pcs", "LF 53",
    "Sports divider set of 25 pieces.",
    750.00, 74)

add_product("Agility Ladder", "LF 58",
    "Agility ladder for sports training.",
    1790.00, 74)

add_product("Swing Ring", "LF 414A",
    "Swing accessory ring.",
    990.00, 74)

add_product("Ring 40cm", "LF 56",
    "Ring 40cm diameter for sports activities.",
    990.00, 74)

add_product("Ring 50cm", "LF 57",
    "Ring 50cm diameter for sports activities.",
    1190.00, 74)

add_product("Hurdle", "LF 51",
    "Sports hurdle.",
    290.00, 74)

add_product("Rope Ladder", "F-3",
    "Rope ladder for climbing and sports.",
    1790.00, 74)

# ============================================================
# PAGE 75-86: Balance & Sensory Equipment
# ============================================================
add_product("Balancer 6 Pcs", "LF 144B",
    "Colorful interlocking balance beams designed to improve children's balance, coordination, and motor skills. Features anti-slip tactile surface for safe play. Size: L50.8xW15.2xH8.8 CM. Set of 6 pieces.",
    4490.00, 75)

add_product("Balancer 8 Pcs", "LF 143",
    "Fun and engaging balance stones designed to improve children's coordination, balance, and motor skills. Made with anti-slip textured surfaces. Set of 8 pieces.",
    4490.00, 75)

add_product("Balance Path Set", "LF 145",
    "Children identify each textured piece by touch and match it to the correct spot. Encourages tactile recognition, problem-solving skills, and hand-eye coordination. 12pcs and 1 Blindfold. Diameter 27cm and 10cm.",
    5990.00, 76)

add_product("Whale Riverstone Play Set", "LF 147",
    "A fun sensory play set featuring whale-shaped tactile stones. Helps develop tactile recognition, problem-solving skills, and hand-eye coordination. L32xW22xH10.5cm. 12pcs and 1 Blindfold.",
    5990.00, 77)

add_product("Textured Stepping Stones Set", "LF 148",
    "A set of colorful, textured stepping pods designed to develop children's balance, coordination, and sensory exploration. Each pod features unique surface patterns. Large Dia 40cm, Medium 35.5cm, Small Dia 27.8cm.",
    13990.00, 78)

add_product("Balance Path Stepping Stones", "LF 149",
    "A fun and colourful set of balance stepping stones. Kids can hop, step, and create their own obstacle paths. Sizes: Large L35.5xW30.3xH23 cm, Medium L30.9xW26.4xH21.1 cm, Small L12.2xW7.9xH5.1 cm.",
    4490.00, 79)

add_product("Makarci Stepping Balance Stones", "LF 150",
    "A fun and colorful set of balance stepping stones to improve children's coordination, stability, and gross motor skills. Sizes: Large 28x25cm Green, Extra Large 35x26.5cm Blue, Medium 28x21cm Dark Green, Small 16.5x15.5cm Yellow.",
    2990.00, 80)

add_product("Balance Wave (8-Bend Walkway)", "LF 151",
    "Designed to mimic gentle undulations of natural waves, this balance board offers a realistic balance-training experience. 52x14x10cm, 8 pieces.",
    10990.00, 81)

add_product("FunStep Balance Builder", "LF 152",
    "A modular balance set featuring interlocking beams and textured, anti-slip stepping pods. Bridge Deck: 73x14x5cm, Circular Pier: 32x32x15cm. Includes 4 bridge decks + 5 circular piers.",
    14990.00, 82)

add_product("Balance Rocker", "LF 153",
    "A playful balance rocker with smooth curved shape encouraging balancing, rocking, sitting, and imaginative play. Helps improve coordination, core strength, and motor skills. 70x28cm.",
    1490.00, 83)

add_product("Hover Spin Seat", "LF 161",
    "A dynamic 360-degree swivel board that helps kids develop balance, coordination, and core strength. L54 x W43 x H28 cm. Per piece pricing.",
    4990.00, 84)

add_product("Fish Hover Spin Seat", "LF 162",
    "Fish-themed swivel board. A dynamic 360-degree swivel board that helps children build balance, coordination, and core strength. L54 x W58 x H27 cm. Per piece pricing.",
    4990.00, 84)

add_product("Kids Unity Stretch Band", "LF 164",
    "A colorful elastic play band for group activities that encourage teamwork, coordination, and active movement. 300 cm length, inner tube width: 8mm.",
    2990.00, 85)

add_product("Jump-Toss-Balance Activity Kit", "LF 165",
    "A fun active play set that helps children develop balance, coordination, and motor skills. Kids jump, toss bean bags, and aim for colorful buckets. Size: 15x12.5x15cm.",
    2990.00, 86)

# ============================================================
# PAGE 87: Various
# ============================================================
add_product("Single Layer Jump Bag", "LF 169",
    "Single layer jump bag for active play. Size: 50x70cm.",
    490.00, 87)

add_product("Wooden Traffic Sign Set", "LF 167",
    "Wooden traffic sign playset. 18 pieces/set. Perfect for educational role play.",
    17990.00, 87)

add_product("Flat Number Marker Plates", "LF 170",
    "Flat number marker plates, set of 10. High quality PVC. Size: 23 cm diameter.",
    2990.00, 87)

# ============================================================
# PAGE 88: Play Parachute
# ============================================================
add_product("Colorful Play Umbrella 9ft", "LF 62",
    "A vibrant multi-color play parachute for group activities and teamwork games. 9 ft diameter.",
    1990.00, 88)

add_product("Colorful Play Umbrella 6.5ft", "LF 62S",
    "A vibrant multi-color play parachute for group activities and teamwork games. 6.5 ft diameter.",
    1190.00, 88)

# ============================================================
# PAGES 89-90: Learning Toys
# ============================================================
for sku_num in range(21, 30):
    add_product(f"Learning Toy Set - LFT {sku_num}A", f"LFT {sku_num}A",
        f"Educational learning toy. MRP: 450.00.", 450.00, 89)

for sku_num in range(30, 41):
    price = 290.00 if sku_num in [37, 38, 39] else 450.00
    add_product(f"Learning Toy Set - LFT {sku_num}A", f"LFT {sku_num}A",
        f"Educational learning toy. MRP: {price:.2f}.", price, 90)

# ============================================================
# PAGE 91: Puppets
# ============================================================
add_product("Insect Puppet (Set of 6)", "LFP 10",
    "Insect puppet set of 6 pieces for imaginative play and storytelling.",
    2395.00, 91)

add_product("Family Puppet (Set of 6)", "LFP 11",
    "Family puppet set of 6 pieces for imaginative play and storytelling.",
    2795.00, 91)

add_product("Community Helpers Puppet (Set of 8)", "LFP 12",
    "Community helpers puppet set of 8 pieces for imaginative role play.",
    2395.00, 91)

add_product("Birds Puppet (Set of 6)", "LFP 9",
    "Birds puppet set of 6 pieces for imaginative play.",
    2395.00, 91)

add_product("Fruits-Vegetables Puppet (Set of 12)", "LFP 7",
    "Fruits and vegetables puppet set of 12 pieces for educational play.",
    2395.00, 91)

add_product("Finger Puppet (Set of 10)", "LFP 4",
    "Finger puppet set of 10 pieces for storytelling and imaginative play.",
    3995.00, 91)

add_product("Domestic Animals Puppet (Set of 10)", "LFP 5",
    "Domestic animals puppet set of 10 pieces for imaginative play.",
    795.00, 91)

add_product("Wild Animals Puppet (Set of 10)", "LFP 6",
    "Wild animals puppet set of 10 pieces for imaginative play.",
    3995.00, 91)

add_product("Water Animals Puppet (Set of 6)", "LFP 8",
    "Water animals puppet set of 6 pieces for imaginative play.",
    4795.00, 91)

# ============================================================
# PAGE 92: Role Play Costumes
# ============================================================
costume_items = [
    ("Pilot", "LFT 1213"), ("Construction Worker", "LFT 1212"),
    ("Military Forces", "LFT 1211"), ("Lawyer", "LFT 1214"),
    ("Doctor", "LFT 1215"), ("Lady Doctor", "LFT 1216"),
    ("Chef", "LFT 1217"), ("Nurse", "LFT 1218"),
    ("Firefighter", "LFT 1219"),
]
for name, sku in costume_items:
    add_product(f"{name} Role Play Costume", sku,
        f"{name} role play costume set for imaginative play.", 1990.00, 92)

# ============================================================
# PAGE 93: Toys
# ============================================================
add_product("Shape Sorter", "LFT 011",
    "Shape sorting toy for early learning.",
    699.00, 93)

add_product("Roll Ball", "LFT 013",
    "Roll ball toy for infants and toddlers.",
    499.00, 93)

add_product("Baby's First Blocks", "LFT 012",
    "Baby's first blocks set for early development.",
    599.00, 93)

add_product("Shape Sorting Baby Toy", "LFT 014",
    "Shape sorting baby toy for early learning.",
    899.00, 93)

add_product("Fun Inertia Animal Car Set (4 Pcs)", "LFT 016",
    "Fun inertia animal car set of 4 pieces (Horse, Zebra, Sheep, Lion).",
    1196.00, 93)

add_product("My First Car Set (4 Pcs)", "LFT 015",
    "My first car set of 4 pieces (Police, Ambulance, Taxi, Bus).",
    1196.00, 93)

# ============================================================
# PAGE 94: Flash Cards
# ============================================================
flash_cards = [
    ("Alphabet", "LFT 1251"), ("Numbers", "LFT 1252"),
    ("Vegetables", "LFT 1254"), ("Colours and Shapes", "LFT 1253"),
    ("Fruits", "LFT 1255"), ("Birds", "LFT 1256"),
    ("Parts of the Body", "LFT 1258"), ("Animals", "LFT 1257"),
    ("Vehicles", "LFT 1259"), ("Community Helpers", "LFT 1260"),
    ("Opposites", "LFT 1261"),
]
for name, sku in flash_cards:
    add_product(f"{name} Flash Cards", sku,
        f"{name} flash cards for early learning.", 299.00, 94)

# ============================================================
# PAGE 95: Puzzles
# ============================================================
add_product("Alphabet Puzzle", "PZ-ALPHA",
    "Alphabet puzzle for early learning.",
    305.00, 95)

add_product("Numbers Puzzle", "PZ-NUM",
    "Numbers puzzle for early learning.",
    305.00, 95)

add_product("Opposites Puzzle", "PZ-OPP",
    "Opposites puzzle for early learning.",
    305.00, 95)

add_product("Where Am I Puzzle", "PZ-WAI",
    "Where am I puzzle for early learning.",
    305.00, 95)

add_product("Size It Up Puzzle", "PZ-SIZE",
    "Size it up puzzle for early learning.",
    305.00, 95)

add_product("Things I Can Do Puzzle", "PZ-THINGS",
    "Things I can do puzzle for early learning.",
    305.00, 95)

add_product("What's Wrong Puzzle", "PZ-WRONG",
    "What's wrong puzzle for early learning.",
    305.00, 95)

add_product("Parts of the Body Puzzle", "PZ-BODY",
    "Parts of the body puzzle for early learning.",
    305.00, 95)

# ============================================================
# PAGE 96: Toys
# ============================================================
add_product("Sand Toys Set", "LFT 92",
    "Sand toys for outdoor and sensory play. Per piece pricing.",
    249.00, 96)

add_product("Fruits Cutting Toy", "LFT 1201",
    "Fruits cutting toy for pretend play.",
    299.00, 96)

add_product("Vegetables Cutting Toy", "LFT 1202",
    "Vegetables cutting toy for pretend play.",
    299.00, 96)

add_product("Fruits Cutting Play Set", "LFT 1203",
    "Fruits cutting play set for pretend play.",
    1395.00, 96)

add_product("Vegetables Cutting Play Set", "LFT 1204",
    "Vegetables cutting play set for pretend play.",
    995.00, 96)

add_product("Fun PU Balls Set", "PU6CM1",
    "Fun PU ball set for active play.",
    799.00, 96)

add_product("Football", "FB3CM1",
    "Football for active play.",
    549.00, 96)

add_product("Basketball", "BB3CM1",
    "Basketball for active play.",
    399.00, 96)

add_product("Fruits Play Set", "LFT 1209",
    "Fruits play set for pretend play.",
    499.00, 96)

add_product("Vegetables Play Set", "LFT 1210",
    "Vegetables play set for pretend play.",
    499.00, 96)

add_product("Bowling Set Jumbo", "LFT 98",
    "Jumbo bowling set for active play.",
    499.00, 96)

add_product("Bowling Set Standard", "LFT 99",
    "Standard bowling set for active play.",
    699.00, 96)

add_product("Stack-o-Barrel", "LFT 051",
    "Stack-o-Barrel stacking toy.",
    199.00, 96)

add_product("Stack-o-Cups", "LFT 053",
    "Stack-o-Cups stacking toy.",
    179.00, 96)

add_product("Stack-o-Egg", "LFT 052",
    "Stack-o-Egg stacking toy.",
    239.00, 96)

add_product("Stack-o-Cubes", "LFT 054",
    "Stack-o-Cubes stacking toy.",
    249.00, 96)

add_product("Toddler Ring Stacker", "LFT 97C",
    "Toddler ring stacking toy.",
    249.00, 96)

# ============================================================
# PAGE 97: More Toys
# ============================================================
add_product("Hopscotch Game", "LFT 90D",
    "Hopscotch game for active play.",
    1199.00, 97)

add_product("Digital Ice Lolly Toy", "LFT 1241",
    "Digital ice lolly toy for imaginative play.",
    1199.00, 97)

add_product("Wild Animal Set", "LFT 1221",
    "Wild animal figurine set.",
    499.00, 97)

add_product("Farm Animal Set", "LFT 1222",
    "Farm animal figurine set.",
    499.00, 97)

add_product("Ocean Animal Set", "LFT 1223",
    "Ocean animal figurine set.",
    599.00, 97)

add_product("Insects Set", "LFT 1224",
    "Insects figurine set.",
    499.00, 97)

add_product("Xylophone Big", "LFT 1152",
    "Large xylophone musical toy.",
    899.00, 97)

add_product("Xylophone", "LFT 1151",
    "Xylophone musical toy.",
    599.00, 97)

add_product("Bin Buddy", "LFT 1243",
    "Bin buddy sorting toy.",
    499.00, 97)

add_product("Doctor Set", "LFT 1231",
    "Doctor role play set.",
    899.00, 97)

add_product("Kitchen Set", "LFT 1232",
    "Kitchen role play set.",
    899.00, 97)

add_product("Tool Kit", "LFT 1233",
    "Tool kit role play set.",
    899.00, 97)

add_product("Beauty Set", "LFT 1234",
    "Beauty role play set.",
    899.00, 97)

# ============================================================
# PAGES 98-99: Mats
# ============================================================
add_product("EVA Mat Alphabet", "EVA-ALPHA",
    "EVA foam mat with alphabet design.",
    2490.00, 98)

add_product("EVA Mat Numbers", "EVA-NUM",
    "EVA foam mat with numbers design.",
    990.00, 98)

add_product("Rolling Carpet - Size S", "RC-S",
    "Rolling carpet small size.",
    1190.00, 98)

add_product("Rolling Carpet - Size M", "RC-M",
    "Rolling carpet medium size.",
    1390.00, 98)

add_product("Rolling Carpet - Size L", "RC-L",
    "Rolling carpet large size.",
    1690.00, 98)

add_product("Rolling Carpet - Size XL", "RC-XL",
    "Rolling carpet extra large size.",
    1990.00, 98)

add_product("Folding Mat XPE - Size L", "XPE-L",
    "Folding mat XPE material, large size.",
    1990.00, 98)

add_product("Folding Mat XPE - Size XL", "XPE-XL",
    "Folding mat XPE material, extra large size.",
    2490.00, 98)

add_product("EVA Mat 2ftx2ft 12mm", "EVA-2X2-12MM",
    "EVA foam mat 2ft x 2ft, 12mm thickness. Set of 4 pieces.",
    1290.00, 99)

add_product("EVA Mat 2ftx2ft 20mm", "EVA-2X2-20MM",
    "EVA foam mat 2ft x 2ft, 20mm thickness. Set of 4 pieces.",
    1990.00, 99)

add_product("EVA Mat 1Mx1M 25mm", "EVA-1M-25MM",
    "EVA foam mat 1Mx1M, 25mm thickness.",
    1690.00, 99)

add_product("EVA Mat 1Mx1M 20mm", "EVA-1M-20MM",
    "EVA foam mat 1Mx1M, 20mm thickness.",
    1290.00, 99)

add_product("EVA Mat 2ftx2ft Blue 12mm", "EVA-2X2-BLUE",
    "EVA foam mat 2ft x 2ft, blue colour, 12mm thickness. Set of 4 pieces.",
    1290.00, 99)

add_product("EVA Mat 2ftx2ft Grey 12mm", "EVA-2X2-GREY",
    "EVA foam mat 2ft x 2ft, grey colour, 12mm thickness. Set of 4 pieces.",
    1290.00, 99)

add_product("EVA Mat 2ftx2ft Black 12mm", "EVA-2X2-BLACK",
    "EVA foam mat 2ft x 2ft, black colour, 12mm thickness. Set of 4 pieces.",
    1290.00, 99)

# ============================================================
# SEED THE DATABASE
# ============================================================

log(f"Total products to process: {len(products_data)}")
log("=" * 60)

created_count = 0
skipped_count = 0
flagged_count = 0
flagged_items = []
image_copied_count = 0

for p in products_data:
    sku = p["sku"]
    name = p["name"]
    
    # Check for duplicates
    existing = None
    if sku:
        existing = Product.objects.filter(sku=sku).first()
    if not existing:
        existing = Product.objects.filter(name=name, category="INDOORS").first()
    
    if existing:
        log(f"  SKIP: {name} ({sku}) - already exists")
        skipped_count += 1
        continue
    
    # Find image for this product
    page_num = p["page_num"]
    page_images = get_page_images(page_num)
    
    image_path = None
    if page_images:
        src = page_images[0]
        sku_slug = re.sub(r'[^a-zA-Z0-9]', '_', sku) if sku else f"page{page_num:03d}"
        rel_path = copy_image_to_media(src, sku_slug)
        image_path = rel_path
        image_copied_count += 1
    
    # Create product
    try:
        product = Product.objects.create(
            name=name,
            category="INDOORS",
            price=p["price"],
            discount_price=p.get("discount_price"),
            description=p["description"],
            sku=sku if sku else None,
            stock=10,
            image_file=image_path,
        )
        
        if p["price"] == 0:
            flagged_count += 1
            flagged_items.append(f"  WARNING: Page {page_num}: {name} ({sku}) - PRICE NOT LISTED")
        
        created_count += 1
        status = "PRICE MISSING" if p["price"] == 0 else "OK"
        img = "IMG" if image_path else "NOIMG"
        log(f"  [{img}] CREATED: {name[:55]:55s} | SKU={str(sku or 'N/A'):15s} | Rs.{p['price']:>8.2f} | [{status}]")
    except Exception as e:
        log(f"  ERROR: {name} ({sku}) - {str(e)}")
        skipped_count += 1

# ============================================================
# FINAL REPORT
# ============================================================
log("\n" + "=" * 60)
log("FINAL REPORT - Indoor Catalogue Seeding")
log("=" * 60)
log(f"Total products parsed:    {len(products_data)}")
log(f"Created (seeded):         {created_count}")
log(f"Skipped (duplicates):     {skipped_count}")
log(f"Images assigned:          {image_copied_count}")
log(f"Flagged (price missing):  {flagged_count}")
log("-" * 60)

# Check what's in DB now
total_indoors = Product.objects.filter(category="INDOORS").count()
log(f"\nINDOORS products in DB now: {total_indoors}")
log(f"Total products in DB:       {Product.objects.count()}")

if flagged_items:
    log("\nFLAGGED ITEMS (missing prices - need manual review):")
    for item in flagged_items:
        log(item)

log("\nIndoor catalogue seeding complete!")
log(f"\nFull report saved to: {OUTPUT_FILE}")
