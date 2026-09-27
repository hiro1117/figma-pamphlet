#!/usr/bin/env python3
"""採用した素材を docs/library/final/ に揃える(背景はそのまま複製、前景・地域モチーフはキー抜き)。

  .venv/bin/python scripts/library/finalize.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAND = ROOT / "docs/library/candidates"
FINAL = ROOT / "docs/library/final"
PY = sys.executable
KEYOUT = ROOT / "scripts/library/keyout.py"

# 差し替え: (系統, 枠) → 採用した候補
OVERRIDE = {("nachikatsuura", "person-01"): "person-03",   # 01 は背景白+机 → 03(背景白、フラッドフィルで抜く)
            ("nachikatsuura", "vehicle-01"): "vehicle-01r",  # グリルのエンブレム風楕円をレタッチ
            ("noboribetsu", "vehicle-01"): "vehicle-02"}     # 01 は右側面向き → 02
FAMILIES = {"aitoma": "thin", "nachikatsuura": "thin", "noboribetsu": "thin", "mitt": "noline"}
# 地域モチーフ: 採用 id と後処理(外周の線 20px を落とし、y<370 の空のにじみを消す)
MOTIF = ("kurabuchi-haruna-aitoma-thin-03", ["--crop", "20,0,20,20", "--clear-above", "370", "--erode", "1"])


def run(args):
    r = subprocess.run([PY, str(KEYOUT), *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    print("  " + r.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    FINAL.mkdir(exist_ok=True)
    for fam, sty in FAMILIES.items():
        bg = f"{fam}-K2-{sty}-bg-01.png"
        shutil.copy(CAND / bg, FINAL / bg)
        print(f"bg   {bg}(2K マスター、そのまま)")
        for kind in ("person-01", "person-02", "vehicle-01"):
            kind = OVERRIDE.get((fam, kind), kind)
            src = CAND / f"{fam}-K2-{sty}-{kind}.png"
            if not src.exists():
                print(f"  (未生成) {src.name}"); continue
            run([str(src), str(FINAL / src.name), "--trim", "--erode", "1"])
    mid, extra = MOTIF
    run([str(CAND / f"{mid}.png"), str(FINAL / f"{mid}.png"), "--trim", *extra])
