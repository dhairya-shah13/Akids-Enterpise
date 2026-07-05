"""Extract text and images from Indoor Catalogue March 2026 PDF."""
import fitz
import os
import sys
import json
from pathlib import Path

pdf_path = Path(__file__).parent.parent / "catalogues" / "Indoor Catalogue March 2026-.pdf"
output_dir = Path(__file__).parent / "indoor"
images_dir = output_dir / "images"
output_dir.mkdir(parents=True, exist_ok=True)
images_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(str(pdf_path))
print(f"Total pages: {doc.page_count}")

# Extract text from all pages
all_pages = []
for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text("text")
    # Clean up the text - remove excessive whitespace
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    page_text = '\n'.join(lines)
    
    all_pages.append({
        "page_num": i + 1,
        "text": page_text,
        "char_count": len(page_text)
    })
    
    # Extract images from each page
    image_list = page.get_images(full=True)
    for img_idx, img in enumerate(image_list):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        img_filename = f"page{i+1:03d}_img{img_idx+1}.{image_ext}"
        img_path = images_dir / img_filename
        with open(img_path, "wb") as f:
            f.write(image_bytes)
        print(f"  Extracted: {img_filename} ({len(image_bytes)} bytes)")

# Save text extraction to JSON
output_data = {
    "total_pages": doc.page_count,
    "pages": all_pages
}

with open(output_dir / "extracted_text.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"\nDone! Extracted {doc.page_count} pages")
print(f"Text saved to: {output_dir / 'extracted_text.json'}")
print(f"Images saved to: {images_dir}")
