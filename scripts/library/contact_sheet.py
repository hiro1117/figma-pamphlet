#!/usr/bin/env python3
"""docs/library/candidates/ の PNG を系統×描法の格子に並べたコンタクトシートを作る(採用案の比較用)。

  .venv/bin/python scripts/library/contact_sheet.py [--kind bg|person|vehicle|motif|all] [--out docs/library/candidates/_sheet-bg.png]
"""
import argparse
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
CAND = ROOT / "docs/library/candidates"
FAMS = ["aitoma", "nachikatsuura", "noboribetsu", "mitt"]
STYS = ["hand", "flat"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="bg")
    ap.add_argument("--out")
    ap.add_argument("--cell", type=int, default=520)
    ns = ap.parse_args()
    pat = re.compile(r"^(?P<fam>[a-z]+)-K2-(?P<sty>hand|flat|thin|noline)-(?P<kind>[a-z]+)-(?P<n>\d+)\.png$")
    files = []
    for p in sorted(CAND.glob("*.png")):
        if p.name.startswith("_"):
            continue
        m = pat.match(p.name)
        if m and (ns.kind == "all" or m["kind"] == ns.kind):
            files.append((m["fam"], m["sty"], m["kind"], m["n"], p))
    if not files:
        raise SystemExit("対象の候補画像がありません")
    cols = sorted({(s, k, n) for _, s, k, n, _ in files})
    W, H = ns.cell, ns.cell + 40
    sheet = Image.new("RGB", (len(cols) * W + 160, len(FAMS) * H + 40), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except Exception:
        font = ImageFont.load_default()
    for ci, (s, k, n) in enumerate(cols):
        d.text((160 + ci * W + 8, 8), f"{s}-{k}-{n}", fill=(40, 40, 40), font=font)
    for ri, fam in enumerate(FAMS):
        d.text((8, 40 + ri * H + H // 2), fam, fill=(40, 40, 40), font=font)
        for ci, (s, k, n) in enumerate(cols):
            match = [p for f, ss, kk, nn, p in files if f == fam and (ss, kk, nn) == (s, k, n)]
            if not match:
                continue
            im = Image.open(match[0]).convert("RGB")
            im.thumbnail((W - 16, H - 56))
            x = 160 + ci * W + (W - im.width) // 2
            y = 40 + ri * H + 8
            sheet.paste(im, (x, y))
            d.text((160 + ci * W + 8, 40 + ri * H + H - 44), match[0].name, fill=(80, 80, 80), font=font)
    out = Path(ns.out) if ns.out else CAND / f"_sheet-{ns.kind}.png"
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
