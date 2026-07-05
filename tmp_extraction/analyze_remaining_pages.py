"""Analyze remaining pages (30-100) of the indoor catalogue."""
import json
import os

data_path = os.path.join(os.path.dirname(__file__), "indoor", "extracted_text.json")
out_path = os.path.join(os.path.dirname(__file__), "indoor", "analysis_pages_30_100.txt")

with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data["pages"]

with open(out_path, "w", encoding="utf-8") as out:
    for p in pages[29:]:  # pages 30-100 (0-indexed: 29-99)
        page_num = p["page_num"]
        text = p["text"]
        char_count = p["char_count"]
        out.write(f"\n{'='*60}\n")
        out.write(f"=== PAGE {page_num} ({char_count} chars) ===\n")
        out.write(f"{'='*60}\n")
        out.write(text[:2000])
        if len(text) > 2000:
            out.write(f"\n... [truncated, total {len(text)} chars]")
        out.write("\n")

print(f"Analysis written to: {out_path}")
