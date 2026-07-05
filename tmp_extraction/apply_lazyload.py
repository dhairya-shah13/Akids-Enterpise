"""
Apply lazy loading optimizations to remaining templates.
Adds loading="lazy" to all <img> tags and fade-in-card classes to product cards.
"""
import os
import re

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates', 'products')

def add_loading_lazy_to_imgs(html):
    """Add loading='lazy' to <img> tags that don't already have it."""
    def replace_img(match):
        tag = match.group(0)
        if 'loading=' in tag:
            return tag
        return tag.replace('<img', '<img loading="lazy"', 1)
    
    return re.sub(r'<img\s[^>]*>', replace_img, html)

def add_fade_classes(html):
    """Add fade-in-card to product card divs and stagger-children to their parents."""
    # Add fade-in-card to product card divs
    html = re.sub(
        r'(class="[^"]*rounded-2xl[^"]*border[^"]*hover:shadow-lg[^"]*group[^"]*flex-col[^"]*)',
        r'\1 fade-in-card',
        html
    )
    
    # Add stagger-children to grid parents of product cards
    html = re.sub(
        r'(class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8[^"]*")',
        r'\1 stagger-children',
        html
    )
    
    # Also for 4-col grids without exact match
    html = re.sub(
        r'(class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-16")',
        r'\1 stagger-children',
        html
    )
    
    return html

# Files to process
files = [
    'search_results.html',
    'cart.html',
    'checkout.html',
    'outdoors.html',
    'parts.html',
    'mrsports.html',
    'admin_dashboard.html',
]

print("=" * 60)
print("Applying lazy loading optimizations...")
print("=" * 60)

for filename in files:
    filepath = os.path.join(TEMPLATES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  SKIP: {filename} - not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()
    
    original = html
    
    # Apply optimizations
    html = add_loading_lazy_to_imgs(html)
    html = add_fade_classes(html)
    
    changes = []
    if html != original:
        changes_count = 0
        # Count changes
        original_imgs = original.count('<img')
        new_imgs = html.count('<img')
        if original_imgs == new_imgs:
            # Check if loading was added
            original_loading = original.count('loading="lazy"')
            new_loading = html.count('loading="lazy"')
            if new_loading > original_loading:
                changes.append(f"loading=lazy added to {new_loading - original_loading} img(s)")
        
        original_fade = original.count('fade-in-card')
        new_fade = html.count('fade-in-card')
        if new_fade > original_fade:
            changes.append(f"fade-in-card added to {new_fade - original_fade} card(s)")
        
        original_stagger = original.count('stagger-children')
        new_stagger = html.count('stagger-children')
        if new_stagger > original_stagger:
            changes.append(f"stagger-children added")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  OK:  {filename} - {', '.join(changes)}")
    else:
        print(f"  SAME: {filename} - no changes needed")

print()
print("Done!")
