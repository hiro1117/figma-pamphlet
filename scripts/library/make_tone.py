#!/usr/bin/env python3
"""基底案ごとの tone.json 最小版を生成する(計画書 6.2 のスキーマ、正規化規則つき)。

  .venv/bin/python scripts/library/make_tone.py            # docs/library/tone/<base_id>.json を 4 つ書く

- 値は画像に見えるもの(palette.roles.main 等)と実測(meta)だけ書き、見えないものは provenance=default
- 正規化: main は白と ≥4.5:1、cta は ground と白の両方に ≥7:1 になるまで暗くする(規則は provenance=rule)
- 出典: docs/prep/colors.md(系統色)、docs/prep/physical-size.md(meta)、docs/library/tone-spec.md(illustration.style)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/library/tone"


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#" + "".join(f"{round(max(0, min(1, v)) * 255):02X}" for v in c)


def lum(c):
    def f(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = lum(hex2rgb(a)), lum(hex2rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def darken_until(hex_color, targets, ratio, step=0.02):
    """targets(hex 群)すべてに対し ratio 以上になるまで、同じ色相のまま明度を下げる。"""
    c = hex2rgb(hex_color)
    for _ in range(60):
        cur = rgb2hex(c)
        if all(contrast(cur, t) >= ratio for t in targets):
            return cur
        c = tuple(v * (1 - step) for v in c)
    return rgb2hex(c)


# 系統ごとの実測パレット(colors.md)と採用基底案
FAMILIES = {
    "aitoma": dict(family="あいとま系", base="aitoma-K2-abst-01", ground="#FFD8E3", main="#EB6EA5", tint="#F6BED1", ink="#000000",
                   accent="#1B98D0", locked=False, bg_img="aitoma-K2-abst-bg-02", horizon=0.54, outline="noline", rotated=True, source="library_gemini_app_2k",
                   direction=("抽象グラフィック", "平坦なピンクの空と稜線1本の静かな里山に、輪郭線のない色面で描いた人物と白いミニバン", ["静か", "洗練", "ご近所"]),
                   headline={"family": "Zen Maru Gothic", "weight": "Black"}),
    "nachikatsuura": dict(family="那智勝浦系", base="nachikatsuura-K2-abst-01", ground="#E3F7FF", main="#1B98D0", tint="#76C1E3", ink="#000000",
                          accent="#FAEF50", locked=False, bg_img="nachikatsuura-K2-abst-bg-01", horizon=0.62, outline="noline", rotated=True, source="library_gemini_app_2k",
                          direction=("抽象グラフィック", "淡い水色の空と海色の稜線1本の静かな里山に、輪郭線のない色面で描いた人物と白いミニバン", ["静か", "洗練", "ご近所"]),
                          headline={"family": "Zen Maru Gothic", "weight": "Black"}),
    "noboribetsu": dict(family="登別系", base="noboribetsu-K2-abst-01", ground="#F9F2DC", main="#D7835F", tint="#FFF9B3", ink="#000000",
                        accent="#513A1E", locked=False, bg_img="noboribetsu-K2-abst-bg-01", horizon=0.65, outline="noline", rotated=True, source="library_gemini_app_2k",
                        direction=("抽象グラフィック", "クリームの空とテラコッタの稜線1本の静かな里山に、輪郭線のない色面で描いた人物と白いミニバン", ["静か", "洗練", "ご近所"]),
                        headline={"family": "Zen Maru Gothic", "weight": "Black"}),
    "mitt": dict(family="MITT系", base="mitt-K2-abst-01", ground="#FCF9C6", main="#254F99", tint="#258FC2", ink="#231815",
                 accent="#FAEF50", locked=True, bg_img="mitt-K2-abst-bg-01", horizon=0.68, outline="noline", rotated=False, source="library_gemini_app_2k",
                 direction=("抽象グラフィック", "ブランド青の空と紺の稜線1本の静かな里山に、輪郭線のない色面で描いた人物と白いミニバン", ["静か", "洗練", "ご近所"]),
                 headline={"family": "Noto Sans JP", "weight": "Black"}),
}


def build(key, f):
    main = f["main"]
    main_norm = darken_until(main, ["#FFFFFF"], 4.5)
    cta = darken_until(main, [f["ground"], "#FFFFFF"], 7.0)
    style = ({"rendering": "flat_vector_thin_outline", "outline_mm": 0.5, "shading": "none", "background": "transparent"}
             if f["outline"] == "thin" else
             {"rendering": "flat_vector_no_outline", "outline_mm": 0, "shading": "none", "background": "transparent"})
    return {
        "schema_version": "tone/3",
        "meta": {
            "template_family": f["family"],
            "sheet": {"size_mm": [297, 420], "fold": "half_then_roll3", "px_per_mm": 5.69},
            "faces": {"cover": {"name": "表1", "size_mm": [99, 210], "position": "top_right", "rotated_in_frame": False},
                      "back": {"name": "表4", "size_mm": [99, 210], "rotated_in_frame": f["rotated"]}},
            "fold_lines_px": {"x": [563.7, 1127.3], "y": [1196]}, "bottom_row_rotated": f["rotated"],
            "locked": {"brand_palette": f["locked"], "body_typography": True, "fold_and_bleed": True,
                       "fixed_blocks": ["発行者情報", "電話ブロック", "QR"]},
            "library": {"base_id": f["base"], "background_image": f["bg_img"], "regional_motif_id": None},
        },
        "direction": {"label": f.get("direction", ("テンプレ準拠フラット", "平坦な空と稜線1本の静かな里山に、細線フラットの人物と白いワゴン", ["静か", "見やすい", "ご近所"]))[0],
                      "one_liner": f.get("direction", ("", "平坦な空と稜線1本の静かな里山に、細線フラットの人物と白いワゴン", []))[1],
                      "mood_words": f.get("direction", ("", "", ["静か", "見やすい", "ご近所"]))[2]},
        "composition": {
            "cover_preset": "K2_top_visual",
            "hero": {"area_ratio_of_face": 0.581, "bleed_sides": ["top", "right"], "crop_focus": "person_and_vehicle",
                     "horizon_ratio": f["horizon"]},
            "title": {"placement": "bottom_left", "align": "left", "scale": 1.0, "max_width_ratio": 0.7},
            "cta_block": {"placement": "bottom_right", "panel": "solid"},
            "margin_scale": "normal",
        },
        "palette": {
            "roles": {"ground": f["ground"], "main": main_norm, "main_tint": f["tint"], "panel": "#FFFFFF", "ink": f["ink"],
                      "cta": cta, "cta_text": "#FFFFFF", "accent_decor": f["accent"]},
            "cta_slots": ["#電話", "#CTA"], "accent_decor_slots": ["#バッジ"],
            "illustration_palette": [main, f["tint"], f["ground"], "#FFFFFF", "#231815" if f["outline"] == "thin" else f["main"]] + (["#2B3150", "#7A7A3A", "#F5CEC1"] if f["outline"] == "noline" and f.get("source") else []),
            "print": {"max_saturation_large_fill": 0.80, "min_tint_pct": 5, "gradients_allowed": False},
            "contrast_check": {"main_vs_white": round(contrast(main_norm, "#FFFFFF"), 2),
                               "cta_vs_ground": round(contrast(cta, f["ground"]), 2), "cta_vs_white": round(contrast(cta, "#FFFFFF"), 2)},
        },
        "typography": {
            "headline_preset": "H1_round_black_horizontal_2tone",
            "headline": {"family": f["headline"]["family"], "weight": f["headline"]["weight"], "line_height": 1.25, "tracking_pct": -2,
                         "treatment": "solid_on_panel",
                         "two_tone": {"enabled": True, "colors": [f["ink"], main_norm], "apply_to": "service_name"},
                         "effects": {"outline": {"enabled": False, "max_ratio_of_size": 0.06}, "shadow": {"enabled": False}}},
            "numerals": {"family": "Noto Sans JP", "weight": "Black", "phone_min_ratio_to_body": 3.0, "tilt": "none"},
            "body": {"locked_by_template": True, "allowed_families": ["Noto Sans JP", "BIZ UDPGothic"], "min_pt": 12},
        },
        "decoration": {"signature_element": "none", "budget": {"max_devices_per_face": 3, "max_shape_patterns": 3},
                       "corner_radius_mm": {"small": 2, "large": 6}, "shadow_policy": "none",
                       "background": {"type": "flat", "gradient": None},
                       "no_go_zones": ["fold_8mm", "trim_3mm", "body_text_boxes", "phone_and_qr"]},
        "illustration": {
            "source_policy": "single_source", "source": f.get("source", "library_nbp_master_2k"), "style": style,
            "subjects": [
                {"id": "hero_person", "desc": "70代女性、受話器を持って穏やかに笑う(person-01)/ 70代男性と娘、乗車の手助け(person-02)",
                 "facing": "toward_cta", "placeholder": "#人物"},
                {"id": "vehicle", "desc": "白い中型ミニバンの乗合タクシー(屋根白・行灯はアクセント色・運転手なし)" if f.get("source") else "白いワゴン型乗合タクシー、右ハンドル", "placeholder": "#車両"},
                {"id": "local_motif", "desc": "(地域レイヤー) 案件ごとに差し替え", "placeholder": "#地域モチーフ", "placement": "hero_horizon"}],
            "min_effective_dpi": 200,
            "photos": {"allowed": True, "use": "実車・実風景のみ。中面の信頼ブロック限定。イラストと同一面に混ぜない"},
        },
        "avoid": {
            "generation": ["3d_pixar_render", "glossy_skin", "left_hand_drive", "kimono_elderly", "cane_white_hair_only",
                           "fuji_sakura_torii_mix", "fake_logos_qr_digits", "english_heavy", "photo_realism", "purple_blue_gradient",
                           "hand_drawn_watercolor"],
            "layout": ["multiple_text_effects_on_one_text", "tilted_body_or_numbers", "text_over_image_without_panel",
                       "rainbow_or_diagonal_gradient_bg", "more_than_2_font_families", "exclamation_star_overuse",
                       "box_everything", "reversed_white_small_text"],
        },
        "provenance": {
            "meta.sheet": "rule", "meta.faces": "rule", "composition.cover_preset": "default",
            "composition.hero.horizon_ratio": "image",
            "palette.roles.ground": "image", "palette.roles.main": "rule", "palette.roles.main_tint": "image",
            "palette.roles.cta": "rule", "palette.roles.accent_decor": "image",
            "typography.headline.family": "default", "decoration.signature_element": "default",
            "illustration.style": "image", "direction": "brief",
        },
        "consumers": {
            "figma_conversion": ["composition", "palette.roles", "typography.headline", "typography.numerals", "decoration", "illustration.subjects"],
            "illustration_brief": ["illustration", "palette.illustration_palette", "avoid.generation", "direction.mood_words"],
            "preflight": ["meta.sheet", "meta.fold_lines_px", "palette.print", "typography.body", "typography.headline.effects",
                          "decoration.budget", "decoration.no_go_zones", "illustration.min_effective_dpi", "avoid.layout"],
            "evaluator_pass2_R5": ["direction", "palette.roles", "typography.headline", "illustration.style", "provenance"],
        },
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for key, f in FAMILIES.items():
        t = build(key, f)
        p = OUT / f"{f['base']}.json"
        p.write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n")
        r = t["palette"]["roles"]; c = t["palette"]["contrast_check"]
        print(f"{p.name}: main {f['main']}→{r['main']} ({c['main_vs_white']}:1 vs white)  cta→{r['cta']} ({c['cta_vs_ground']}:1 ground, {c['cta_vs_white']}:1 white)  {len(p.read_text())} chars")
