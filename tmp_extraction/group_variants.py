"""
Script to group products with size/color variants under a parent product.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'little_fingers.settings')
import django
django.setup()

from products.models import Product

LOG_FILE = os.path.join(os.path.dirname(__file__), 'indoor', 'variant_grouping_report.txt')

# Clear log file
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("Variant Grouping Report\n")
    f.write("=" * 60 + "\n\n")

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# ============================================================
# VARIANT GROUP DEFINITIONS
# Each group: (parent_name, parent_description, [(sku, variant_label, price), ...])
# ============================================================

VARIANT_GROUPS = [
    {
        "name": "Rolling Carpet",
        "description": "A vibrant, durable rolling carpet perfect for classroom activity areas, reading corners, and play zones. The soft surface provides comfort and safety for children during floor activities. Available in multiple sizes.",
        "variants": [
            ("RC-S", "Size S", 1190.00),
            ("RC-M", "Size M", 1390.00),
            ("RC-L", "Size L", 1690.00),
            ("RC-XL", "Size XL", 1990.00),
        ],
    },
    {
        "name": "Folding Mat XPE",
        "description": "Durable XPE folding mat designed for children's play areas. Provides a soft, cushioned surface for safe play and exercise. Available in multiple sizes.",
        "variants": [
            ("XPE-L", "Size L", 1990.00),
            ("XPE-XL", "Size XL", 2490.00),
        ],
    },
    {
        "name": "EVA Mat 2ft x 2ft",
        "description": "Interlocking EVA foam mats, 2ft x 2ft per tile. Provides a soft, safe play surface. Set of 4 pieces. Available in multiple thicknesses and colours.",
        "variants": [
            ("EVA-2X2-12MM", "12mm Thickness", 1290.00),
            ("EVA-2X2-20MM", "20mm Thickness", 1990.00),
            ("EVA-2X2-BLUE", "Blue - 12mm", 1290.00),
            ("EVA-2X2-GREY", "Grey - 12mm", 1290.00),
            ("EVA-2X2-BLACK", "Black - 12mm", 1290.00),
        ],
    },
    {
        "name": "EVA Mat 1M x 1M",
        "description": "Large format EVA foam mat, 1M x 1M. Provides a soft, cushioned play surface for children. Available in multiple thicknesses.",
        "variants": [
            ("EVA-1M-25MM", "25mm Thickness", 1690.00),
            ("EVA-1M-20MM", "20mm Thickness", 1290.00),
        ],
    },
    {
        "name": "Plastic Balls",
        "description": "Colourful plastic balls perfect for ball pits, play zones, and sensory play. Designed for safe indoor use.",
        "variants": [
            ("LFT 200P", "200 pcs (6.5 cm)", 2299.00),
            ("LFT 100", "100 pcs (8.5 cm)", 1299.00),
        ],
    },
    {
        "name": "Trampoline",
        "description": "Indoor trampoline designed for safe, active fun. Sturdy frame with padded edges and secure jumping surface. Available in multiple sizes.",
        "variants": [
            ("LF 536", "36 inch", 4990.00),
            ("LF 545", "45 inch", 6490.00),
            ("LF 55", "55 inch", 11990.00),
            ("LF 72", "72 inch", 20990.00),
            ("LF 96", "96 inch", 24990.00),
            ("LF 120", "120 inch", 31990.00),
            ("LF 144T", "144 inch", 39990.00),
            ("LF 168", "168 inch", 43990.00),
        ],
    },
    {
        "name": "Plastic Chair",
        "description": "Durable plastic chair designed for classroom use. Lightweight, stackable, and easy to clean. Available in multiple height options.",
        "variants": [
            ("LF 106", "24 cm Height", 390.00),
            ("LF 116", "26 cm Height", 590.00),
            ("LF 186", "26-30 cm (Adjustable)", 1090.00),
            ("LF 146", "28 cm (with Handle)", 990.00),
            ("LF 176", "30 cm (Metal)", 1790.00),
            ("LF 126", "31 cm Height", 690.00),
            ("LF 127", "35 cm Height", 890.00),
            ("LF 156", "35 cm (Metal Handle)", 1890.00),
            ("LF 166", "36 cm (Metal Handle)", 2090.00),
            ("LF 128", "40 cm Height", 1290.00),
            ("LF 129", "45 cm Height", 1590.00),
        ],
    },
    {
        "name": "Play Junction Fence",
        "description": "Set of 4 interlocking play junction fence panels (105x75 CM each). Creates a safe play enclosure. Available in multiple colours.",
        "variants": [
            ("LF 135", "Red", 9990.00),
            ("LF 135B", "Blue", 9990.00),
            ("LF 135W", "White", 9990.00),
        ],
    },
    {
        "name": "Colorful Play Umbrella",
        "description": "A vibrant multi-color play parachute for group activities, teamwork games, and cooperative play.",
        "variants": [
            ("LF 62", "9 ft Diameter", 1990.00),
            ("LF 62S", "6.5 ft Diameter", 1190.00),
        ],
    },
    {
        "name": "Bowling Set",
        "description": "Fun bowling set for active indoor play. Encourages hand-eye coordination and friendly competition.",
        "variants": [
            ("LFT 98", "Jumbo", 499.00),
            ("LFT 99", "Standard", 699.00),
        ],
    },
    {
        "name": "Xylophone",
        "description": "Colourful xylophone musical toy for children. Develops musical awareness and fine motor skills.",
        "variants": [
            ("LFT 1152", "Large", 899.00),
            ("LFT 1151", "Standard", 599.00),
        ],
    },
    {
        "name": "Tray",
        "description": "Durable plastic tray for classroom organization, art projects, and storage. Easy to clean and stack.",
        "variants": [
            ("LF 13-6", "Small (26x35x11 cm)", 299.00),
            ("LF 13-5", "Large (31x42x10 cm)", 349.00),
        ],
    },
    {
        "name": "Building Blocks",
        "description": "Colourful plastic building blocks for creative construction. Develops fine motor skills and creativity.",
        "variants": [
            ("LFT 3992D", "16 Pieces", 1399.00),
            ("LFT 3994P", "32 Pieces", 2599.00),
        ],
    },
    {
        "name": "Divider",
        "description": "Sports divider markers for training and games. Perfect for marking boundaries and activity areas.",
        "variants": [
            ("LF 52", "10 Pieces", 1190.00),
            ("LF 53", "25 Pieces", 750.00),
        ],
    },
    {
        "name": "Ring",
        "description": "Durable plastic ring for sports activities, games, and skill-building exercises.",
        "variants": [
            ("LF 56", "40 cm Diameter", 990.00),
            ("LF 57", "50 cm Diameter", 1190.00),
        ],
    },
    {
        "name": "Premium Display Shelf",
        "description": "Premium wooden display shelf for classroom organization and display. Elegant design for preschool environments.",
        "variants": [
            ("LF 1501", "Regular Style", 9990.00),
            ("LF 1503", "Style 2", 9990.00),
            ("LF 1502", "Style 3", 9990.00),
            ("LF 1504", "Tall", 9990.00),
        ],
    },
    {
        "name": "Horse Rideon",
        "description": "Fun horse-shaped ride-on toy for children. Encourages active play and imaginative adventures. Available in multiple colours.",
        "variants": [
            ("LF 927C", "Brown", 2290.00),
            ("LF 927E", "Grey", 2290.00),
        ],
    },
]


def group_variants():
    """Run the variant grouping."""
    total_groups = len(VARIANT_GROUPS)
    products_updated = 0
    products_skipped = 0

    log(f"Processing {total_groups} variant groups...")
    log("=" * 60)

    for group in VARIANT_GROUPS:
        group_name = group["name"]
        group_desc = group["description"]
        variants = group["variants"]

        log(f"\n--- {group_name} ({len(variants)} variants) ---")

        # Find all existing products by SKU
        variant_skus = [v[0] for v in variants]
        existing_products = list(Product.objects.filter(sku__in=variant_skus, category='INDOORS'))

        if not existing_products:
            log(f"  WARNING: No existing products found for {group_name}. Skipping.")
            products_skipped += 1
            continue

        # Sort to maintain variant order
        sku_map = {p.sku: p for p in existing_products}
        existing_products_sorted = []
        for sku in variant_skus:
            if sku in sku_map:
                existing_products_sorted.append(sku_map[sku])

        if not existing_products_sorted:
            continue

        # Use the first product as the parent
        parent = existing_products_sorted[0]
        old_name = parent.name

        # Update parent product
        parent.name = group_name
        parent.sku = None  # Clear SKU for parent
        parent.description = group_desc
        parent.save()
        log(f"  PARENT: '{old_name}' -> '{group_name}' (ID={parent.id})")

        # Link remaining products as children
        for child_prod in existing_products_sorted[1:]:
            variant_sku = child_prod.sku
            variant_label = ""
            for sku, label, price in variants:
                if sku == variant_sku:
                    variant_label = label
                    break

            old_child_name = child_prod.name
            child_prod.parent_product = parent
            if variant_label:
                new_name = f"{group_name} - {variant_label}"
            else:
                new_name = group_name
            child_prod.name = new_name
            child_prod.save()
            log(f"  CHILD: '{old_child_name}' -> '{new_name}' (ID={child_prod.id}, SKU={variant_sku})")
            products_updated += 1

    log("\n" + "=" * 60)
    log("SUMMARY:")
    log(f"  Groups processed:       {total_groups}")
    log(f"  Products linked as children: {products_updated}")
    log(f"  Products skipped:       {products_skipped}")

    return total_groups, products_updated, products_skipped


if __name__ == "__main__":
    group_variants()
