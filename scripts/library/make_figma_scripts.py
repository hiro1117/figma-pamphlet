#!/usr/bin/env python3
"""upload_assets の応答(imageHash・配置ノード)から、素材ページを整理する use_figma スクリプト 5 本と
docs/library/library-v0.json を生成する。

  .venv/bin/python scripts/library/make_figma_scripts.py <scratch_dir>   # <scratch_dir>/upload_responses.jsonl を読む
"""
import csv
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "docs/library/final"
S = Path(sys.argv[1])

resp = [json.loads(l) for l in open(S / "upload_responses.jsonl") if l.strip().startswith("{")]
files = sorted(p.name for p in FINAL.glob("*.png") if not p.name.startswith("_"))
assert len(resp) == len(files) == 17, (len(resp), len(files))
ups = {}
for f, r in zip(files, resp):  # POST はファイル名ソート順で行った
    w, h = Image.open(FINAL / f).size
    ups[f[:-4]] = dict(imageHash=r["imageHash"], nodeId=r["placedOnNodeId"], px=[w, h], bytes=r["sizeBytes"])

FAM = [("aitoma", "thin", "あいとま系", 1), ("nachikatsuura", "thin", "那智勝浦系", 2), ("noboribetsu", "thin", "登別系", 3), ("mitt", "noline", "MITT系", 4)]
PICK = {"aitoma": ["person-01", "person-02", "vehicle-01"], "nachikatsuura": ["person-03", "person-02", "vehicle-01r"],
        "noboribetsu": ["person-01", "person-02", "vehicle-02"], "mitt": ["person-01", "person-02", "vehicle-01"]}
K2_W, K2_H = 580, 711  # 102×125mm × 5.69
lib = {"schema": "library/v0", "file_key": "09Js7rndbabLAoCchqzX9j", "page": {"id": "7:4", "name": "素材"}, "generated": "2026-09-27",
       "k_px_per_mm": 5.69, "hero_frame_px": [K2_W, K2_H], "dpi_formula": "image_px / placed_px * 144.6", "families": {}, "projects": {}}

HEAD = '''const page = await figma.getNodeByIdAsync("7:4");
await figma.setCurrentPageAsync(page);
await figma.loadFontAsync({family: "Noto Sans JP", style: "Regular"});
await figma.loadFontAsync({family: "Noto Sans JP", style: "Bold"});
'''
for i, (fam, sty, label, num) in enumerate(FAM):
    base = f"{fam}-K2-{sty}-01"
    tone = json.dumps(json.load(open(ROOT / f"docs/library/tone/{base}.json")), ensure_ascii=False, separators=(",", ":"))
    assert "`" not in tone and "${" not in tone
    bg = f"{fam}-K2-{sty}-bg-01"
    w, h = ups[bg]["px"]
    items = [(bg, f"{num:02d}-0 背景 | {bg}", K2_W, round(K2_W * h / w))]
    assets = {"background": dict(id=bg, **ups[bg], placement={"target": "#キービジュアル", "scaleMode": "CROP", "frame_px": [K2_W, K2_H]},
                                 effective_dpi=round(w / K2_W * 144.6))}
    for j, kind in enumerate(PICK[fam], 1):
        aid = f"{fam}-K2-{sty}-{kind}"; w, h = ups[aid]["px"]
        if kind.startswith("person"):
            H = 420; W = round(H * w / h); tgt = "#人物"; role = f"人物{'AB'[j - 1]}"
        else:
            W = 360; H = round(W * h / w); tgt = "#車両"; role = "車両"
        items.append((aid, f"{num:02d}-{j} {role} | {aid}", W, H))
        assets[role] = dict(id=aid, **ups[aid], placement={"target": tgt, "scaleMode": "FIT", "suggested_px": [W, H]}, effective_dpi=round(w / W * 144.6))
    lib["families"][fam] = {"label": label, "number": num, "base_id": base, "style": sty, "tone_json": f"docs/library/tone/{base}.json",
                            "group_name": f"ライブラリ/{label}", "assets": assets}
    Y0 = 9000 + i * 900
    js = HEAD + f'''const X0 = -430, Y0 = {Y0};
const items = {json.dumps([dict(id=ups[a]["nodeId"], name=n, w=W, h=H) for a, n, W, H in items], ensure_ascii=False)};
const nodes = [];
const label = figma.createText();
label.fontName = {{family: "Noto Sans JP", style: "Bold"}};
label.characters = "{num} {label} / K2 {'細線フラット' if sty == 'thin' else '線なしフラット'} ({base})";
label.fontSize = 40; label.x = X0; label.y = Y0 - 70; label.name = "ラベル:{num:02d} {label}";
nodes.push(label);
let x = X0;
for (const it of items) {{
  const n = await figma.getNodeByIdAsync(it.id);
  n.resize(it.w, it.h); n.name = it.name; n.x = x; n.y = Y0; x += it.w + 40; nodes.push(n);
}}
const tone = figma.createText();
tone.fontName = {{family: "Noto Sans JP", style: "Regular"}};
tone.resize(800, 100); tone.textAutoResize = "HEIGHT";
tone.characters = `{tone}`;
tone.fontSize = 8; tone.name = "#tone"; tone.x = X0; tone.y = Y0 + 760; tone.visible = false; tone.locked = true;
nodes.push(tone);
const g = figma.group(nodes, page); g.name = "ライブラリ/{label}";
return {{groupId: g.id, nodeIds: nodes.map(n => n.id), bbox: [g.x, g.y, g.width, g.height], toneChars: tone.characters.length}};
'''
    (S / f"figma_{fam}.js").write_text(js)

mid = "kurabuchi-haruna-aitoma-thin-03"; w, h = ups[mid]["px"]
row = [r for r in csv.DictReader(open(ROOT / "docs/library/ledger.csv")) if r["id"] == mid][0]
led = {k: row[k] for k in ("id", "kind", "model", "route", "datetime", "aspect", "size", "status", "note", "prompt_file")}
led["ledger"] = "hiro1117/figma-pamphlet docs/library/ledger.csv"; led["post_process"] = "keyout.py --crop 20,0,20,20 --clear-above 370 --erode 1 --trim"
ledj = json.dumps(led, ensure_ascii=False, separators=(",", ":")); assert "`" not in ledj and "${" not in ledj
W = K2_W; H = round(W * h / w)
lib["projects"]["kurabuchi"] = {"label": "くらぶち", "group_name": "案件/くらぶち",
                               "regional_motif": dict(id=mid, **ups[mid], subject="榛名山(榛名富士+相馬山)",
                                                      placement={"target": "#地域モチーフ", "scaleMode": "FIT", "suggested_px": [W, H], "position": "hero_horizon"},
                                                      effective_dpi=round(w / W * 144.6))}
js = HEAD + f'''const X0 = -430, Y0 = {9000 + 4 * 900};
const nodes = [];
const label = figma.createText();
label.fontName = {{family: "Noto Sans JP", style: "Bold"}};
label.characters = "案件: くらぶち / #地域モチーフ 榛名山 ({mid})";
label.fontSize = 40; label.x = X0; label.y = Y0 - 70; label.name = "ラベル:くらぶち"; nodes.push(label);
const m = await figma.getNodeByIdAsync("{ups[mid]['nodeId']}");
m.resize({W}, {H}); m.name = "#地域モチーフ 榛名山 | {mid}"; m.x = X0; m.y = Y0; nodes.push(m);
const led = figma.createText();
led.fontName = {{family: "Noto Sans JP", style: "Regular"}};
led.resize(800, 100); led.textAutoResize = "HEIGHT";
led.characters = `{ledj}`;
led.fontSize = 8; led.name = "#台帳"; led.x = X0; led.y = Y0 + {H} + 40; led.visible = false; led.locked = true; nodes.push(led);
const g = figma.group(nodes, page); g.name = "案件/くらぶち";
return {{groupId: g.id, nodeIds: nodes.map(n => n.id), bbox: [g.x, g.y, g.width, g.height]}};
'''
(S / "figma_kurabuchi.js").write_text(js)
(ROOT / "docs/library/library-v0.json").write_text(json.dumps(lib, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: {a: v["effective_dpi"] for a, v in f["assets"].items()} for k, f in lib["families"].items()}, ensure_ascii=False))
print("motif dpi", lib["projects"]["kurabuchi"]["regional_motif"]["effective_dpi"])
