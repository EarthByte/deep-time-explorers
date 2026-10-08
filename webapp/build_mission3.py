#!/usr/bin/env python3
"""Assemble the final missions/03_Where_the_Ground_Shakes.html from:
  - mission3_template.html  (fixed tooltip JS/CSS, placeholders intact)
  - shared_head.html        (site-wide CSS/fonts, substituted for __SHARED_HEAD__)
  - basemap_pacific_0Ma.png (new Pacific-centered basemap, base64-embedded)
  - quakes_pacific.json     (corrected earthquake dot positions for that map)

Usage:
  python3 build_mission3.py /path/to/basemap_pacific_0Ma.png
Writes: mission3.html (in this directory)
"""
import base64
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

def main():
    if len(sys.argv) != 2:
        sys.exit("usage: build_mission3.py /path/to/basemap_pacific_0Ma.png")
    img_path = Path(sys.argv[1])
    if not img_path.exists():
        sys.exit(f"image not found: {img_path}")

    template = (HERE / "mission3_template.html").read_text()
    shared_head = (HERE / "shared_head.html").read_text()
    quakes_json = (HERE / "quakes_pacific.json").read_text().strip()

    img_bytes = img_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode("ascii")
    img_data_uri = f"data:image/png;base64,{img_b64}"

    out = template.replace("__SHARED_HEAD__", shared_head)
    out = out.replace("__IMG_BASE__", img_data_uri)
    out = out.replace("__QUAKES_DATA__", quakes_json)

    out_path = HERE / "mission3.html"
    out_path.write_text(out)
    print(f"wrote {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"embedded image: {img_path.name} ({len(img_bytes):,} bytes -> {len(img_b64):,} b64 chars)")

if __name__ == "__main__":
    main()
