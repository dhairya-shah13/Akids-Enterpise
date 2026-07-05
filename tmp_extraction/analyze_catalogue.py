"""Analyze the extracted indoor catalogue text to understand its structure.
Writes output to a file to avoid encoding issues in the console."""
import json
import sys
import os

data_path = os.path.join(os.path.dirname(__file__), "indoor", "extracted_text.json")
out_path = os.path.join(os.path.dirname(__file__), "indoor", "analysis_output.txt")

with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data["pages"]

with open(out_path, "w", encoding="utf-8") as out:
    # Summary first
    out.write(f"Total pages: {len(pages)}\n")
    out.write(f"Total images extracted: {len(os.listdir(os.path.join(os.path.dirname(__file__), 'indoor', 'images')))}\n\n")
    
    # Print first 30 pages in detail to understand structure
    for p in pages[:30]:
        page_num = p["page_num"]
        text = p["text"]
        char_count = p["char_count"]
        out.write(f"\n{'='*60}\n")
        out.write(f"=== PAGE {page_num} ({char_count} chars) ===\n")
        out.write(f"{'='*60}\n")
        # Print the full text
        out.write(text[:2000])
        if len(text) > 2000:
            out.write(f"\n... [truncated, total {len(text)} chars]")
        out.write("\n")

    # Also output pages with lots of text (product pages tend to have more content)
    out.write(f"\n\n{'='*60}\n")
    out.write("=== PAGES WITH MOST TEXT (likely product pages) ===\n")
    out.write(f"{'='*60}\n")
    sorted_pages = sorted(pages, key=lambda x: x["char_count"], reverse=True)
    for p in sorted_pages[:40]:
        out.write(f"  Page {p['page_num']}: {p['char_count']} chars - {p['text'][:80].strip()!r}\n")

print(f"Analysis written to: {out_path}")
print(f"Total pages: {len(pages)}")
