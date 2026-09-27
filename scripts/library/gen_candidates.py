#!/usr/bin/env python3
"""Gemini API(Nano Banana Pro)でキービジュアル・ライブラリ v0 の素材を生成し、台帳に記録する。

  .venv/bin/python scripts/library/gen_candidates.py --stage candidates [--only bg,person,vehicle] [--families aitoma,mitt] [--styles hand,flat] [--dry-run]
  .venv/bin/python scripts/library/gen_candidates.py --stage master --ids aitoma-K2-hand-bg-01       # 採用案の 4K 再生成
  .venv/bin/python scripts/library/gen_candidates.py --stage motif --families aitoma --styles hand    # くらぶち地域モチーフ(採用案の描法で)

- API キーは .env の GEMINI_API_KEY(コミット禁止)。経路は必ず API(有料枠)。Gemini アプリの透かし付き出力は使わない
- 参照画像はレイアウトマスクと系統の色チップだけ(docs/library/masks/)。テンプレ・完成見本・フリー素材は渡さない
- 生成物1点ごとに docs/library/ledger.csv へ モデル名・経路・日時・プロンプト・採否 を追記
- プロンプト構造は計画書 5.1(役割/案件/必須要素/因子/制約/参照/出力)
"""
import argparse
import base64
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import requests

from prompt_abst import abst_prompt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
LIB = ROOT / "docs/library"
MASKS = LIB / "masks"
LEDGER = LIB / "ledger.csv"
PROMPTS = LIB / "prompts"
DEFAULT_MODEL = "gemini-3-pro-image"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# ---------------------------------------------------------------- 系統・描法
FAMILIES = {
    "aitoma": dict(
        label="あいとま系",
        palette="メイン #EB6EA5(ローズピンク)、淡 #F6BED1 / #FFD8E3(桜色)、紙白 #FFFFFF、線・文字 #000000",
        band="空は淡い桜色の平坦な色面(グラデーションなし)、遠景・稜線は少し濃いピンク寄りの灰、道と手前の里山は明るいクリーム〜淡いピンク",
        chips="chips-aitoma.png",
    ),
    "nachikatsuura": dict(
        label="那智勝浦系",
        palette="メイン #1B98D0(海の青)、淡 #76C1E3 / #E3F7FF(水色)、アクセント黄 #FAEF50、紙白 #FFFFFF、線・文字 #000000",
        band="空は淡い水色、遠景・稜線は寒色(青〜青緑)可、道と手前は明るいクリーム〜淡い水色。全体に寒色の透明感",
        chips="chips-nachikatsuura.png",
    ),
    "noboribetsu": dict(
        label="登別系",
        palette="メイン #D7835F(テラコッタ橙)、淡 #F9F2DC(クリーム)/ #FFF9B3(淡黄)、濃茶 #513A1E、紙白 #FFFFFF",
        band="空は淡いクリーム〜淡黄、稜線はテラコッタ寄りの橙〜茶、道と手前は温かいクリーム。全体に暖色の落ち着き",
        chips="chips-noboribetsu.png",
    ),
    "mitt": dict(
        label="MITT系(ブランド色固定)",
        palette="メイン #254F99(紺)、#258FC2(青)、濃 #143747、黄 #FAEF50 / #F9F27F、紙白 #FFFFFF、本文 #231815。この配色から外れない",
        band="空は明るい青(#258FC2 系)から上に向かって紺に寄る平坦な2段色面、稜線は紺、道と手前は白〜淡黄(#F9F27F 系)。紫は使わない",
        chips="chips-mitt.png",
    ),
}
YURU_DESC = ("『ゆるい線画のビジネスイラスト』(日本の自治体広報でよく使われる、人が描いた簡略イラスト)。"
             "頭身は 4.5〜5(頭が大きく手足は細く短い)。顔の輪郭は丸く、目は小さな黒い点 2 つだけ(白目・まつげ・ハイライト・二重線なし)、鼻は描かない、口は短い線 1 本(笑顔は上向きの弧)、眉は省略。頬紅・しわ・ほうれい線なし。"
             "髪は 1 色のベタ塗りの塊で毛束・毛流れ・ツヤを描かない。手は指を描かない丸い塊(ミトン)。首・関節・筋肉を描かない。"
             "服は 1 色のベタ+輪郭線で、しわ線・柄・ボタン・縫い目を描かない。1 人あたり色は 5 色以内(肌・髪・上衣・下衣・靴)。"
             "情報量はピクトグラムより少し豊かで、アニメ・劇画・ストックイラストよりはるかに単純。"
             "English: simple flat line-art character, dot eyes, no nose, one-line mouth, solid single-color hair, mitten hands, 4.5-head proportions, uniform outline, flat fills, no shading, no texture, minimal detail.")
ABST_PALETTE = {
    "aitoma": ("#EB6EA5", "Use muted navy, olive, warm off-white and natural skin tones."),
    "nachikatsuura": ("#1B98D0", "Use muted navy, sand, warm off-white and natural skin tones."),
    "noboribetsu": ("#D7835F", "Use muted dark brown #513A1E, olive, cream off-white and natural skin tones."),
    "mitt": ("#254F99", "Use brand blue #258FC2, deep navy #143747, soft yellow #F9F27F, off-white and natural skin tones. Stay within this brand palette."),
}
STYLES = {
    "abst": dict(label="抽象グラフィック(Hiro 提供プロンプト)", desc="(prompt_abst.py の英語プロンプトを使用)"),
    "yuru": dict(
        label="ゆるい線画(参照準拠)",
        desc=YURU_DESC + " 輪郭は均一な細さの黒線(#231815)で閉じる。線の強弱なし。塗りは均一で、影・ハイライト・グラデーション・質感なし。",
    ),
    "yuru_noline": dict(
        label="ゆるい線なしフラット(MITT 参照準拠)",
        desc=YURU_DESC + " 輪郭線は一切使わず、均一なベタ塗りの色面だけで形を作る。影・ハイライト・グラデーション・質感なし。",
    ),
    "thin": dict(
        label="フラット・細い均一線(テンプレ準拠)",
        desc="日本の自治体パンフレットで使われるシンプルなフラットイラスト。輪郭は均一で細い #231815 の線(画面幅の約0.3%の太さ)、塗りは均一なベタ塗りのみ。影・ハイライト・グラデーション・紙の質感・線の強弱を一切つけない。形は単純化し、細部を描き込まない。色は指定パレットの濃・淡 2 段と紙白、肌色、黒だけに限定する",
    ),
    "noline": dict(
        label="フラット・線なし(MITT テンプレ準拠)",
        desc="輪郭線を一切使わず、均一なベタ塗りの色面だけで形を作るフラットイラスト。影・ハイライト・グラデーション・質感なし。形は単純化し、細部を描き込まない。色は指定パレット(紺・青・濃紺・黄・白)と肌色だけに限定する",
    ),
    "hand": dict(
        label="手描きの温かみ",
        desc="色鉛筆と水彩を合わせたような手描きのタッチ。輪郭は少し揺れた柔らかい線、塗りは紙の目が見える淡い塗り重ね、光はやわらかい午前の日差し。デジタル感・グラデーション感を出さない",
    ),
    "flat": dict(
        label="フラットで明快",
        desc="ベクター風のフラットイラスト。均一なベタ塗り、太めで均一な輪郭線(または輪郭なし)、影は最小限のワントーン、形は単純化して明快。質感やグラデーションは使わない",
    ),
}

ROLE = "あなたは地域交通(自治体の乗合タクシー)の高齢者向けパンフレットを手がけるアートディレクター兼イラストレーターです。"
PROJECT_GENERIC = ("案件: 自治体が運行する予約制の乗合タクシーの案内パンフレット(表紙用)。読み手は70代を中心とした地域住民とその家族。"
                   "ゴールは『気軽に予約して乗ってみよう』と感じてもらうこと(LINE 登録または電話予約)。地域名は指定しません。")
COMMON_BANS = ("文字・ロゴ・看板・QRコードや電話番号らしき数字を描かない。写実(写真調)禁止。3D レンダ調・CG 調禁止。"
               "メーカーのエンブレム・実在の店舗・実在の人物に似せない。富士山+桜+鳥居の組み合わせ禁止。紫→青のグラデーション禁止。"
               "透かし・署名・枠線・余白を入れない。")


def bg_prompt(fam, sty):
    f, s = FAMILIES[fam], STYLES[sty]
    if sty in ("thin", "noline"):
        return "\n".join([
            f"1. 役割: {ROLE}",
            f"2. {PROJECT_GENERIC}",
            "3. 必須要素(背景のみ): 表紙上部に置く『背景の絵』。余白の多い静かな情景で、要素は次の4つだけ: (a) 平坦な1色の空 (b) 画面上端から約60%の高さに、なだらかで単純な稜線1本(濃色1段のシルエット) (c) 手前に向かって伸びる1本の道(紙白〜淡色) (d) 淡色1色の地面。"
            "民家・木・畑は描かないか、描くとしても小さく3つまで。人物・車両・動物・地域固有の名所・雲・太陽・鳥は描かない。",
            "   稜線より上は空だけ。画面下部(下端から約25%)は道と地面だけにし、あとから人物と車両を前面に重ねる余地を残す。",
            f"4. 因子: 構図 = 上ビジュアル+下情報(K2)向け、画面いっぱいの情景で余白なし。描法 = {s['label']}: {s['desc']}",
            f"   色: {f['label']}のパレット。{f['palette']}。色帯域: {f['band']}。空も地面もグラデーションにせず平坦な1色ずつ。",
            f"5. 制約: 画像比率は 4:5(縦長)。{COMMON_BANS} 参照画像2枚は『レイアウトの幾何(白=絵の領域、薄灰=断裁で消える塗り足し、薄い横帯=地平線帯の目安)』と『色チップ』であり、それらの形や灰色を絵に描き込まない。",
            "6. 参照: 添付1 = レイアウトマスク(幾何図形)、添付2 = 色チップ。",
            "7. 出力: 1枚の PNG。文字なし。",
        ])
    return "\n".join([
        f"1. 役割: {ROLE}",
        f"2. {PROJECT_GENERIC}",
        "3. 必須要素(背景のみ): 表紙上部に置く『背景の絵』を描いてください。内容は 空・なだらかな稜線(遠景の低い山並み)・手前に向かって伸びる一本の道・汎用的な里山または小さな街並み(民家・畑・街路樹など、どこの地域とも特定できないもの)。"
        "人物・車両・動物・地域固有の名所(実在の山・城・橋・塔など)は絶対に描かない。",
        "   地平線帯(画面上端から約60%の高さ)は、後からその地域の山のシルエットを重ねるため、単純でなだらかな稜線1本にとどめ、そこに複雑な要素を置かない。稜線より上は空だけ。",
        "   画面下部(下端から約20%)は道と地面で、あとから人物と車両を前面に重ねるため、そこに目を引く要素を置かない。",
        f"4. 因子: 構図 = 上ビジュアル+下情報(K2)向け、画面いっぱいの情景で余白なし。描法 = {s['label']}: {s['desc']}",
        f"   色: {f['label']}のパレットに従う。{f['palette']}。色帯域: {f['band']}。大きな面の彩度は高すぎないように(印刷での網点を想定)。",
        f"5. 制約: 画像比率は 4:5(縦長)。{COMMON_BANS} 参照画像2枚は『レイアウトの幾何(白=絵の領域、薄灰=断裁で消える塗り足し、薄い横帯=地平線帯の目安)』と『色チップ』であり、それらの形や灰色を絵に描き込まない。",
        "6. 参照: 添付1 = レイアウトマスク(幾何図形)、添付2 = 色チップ。",
        "7. 出力: 1枚の PNG。文字なし。",
    ])


AI_REALISM_BANS = ("次の要素は『AI が描いたリアル寄りの質感』になるため絶対に描かない: 6 頭身以上の写実的な体型、白目・まつげ・ハイライト・二重のある目、鼻筋・小鼻、頬の赤み・しわ・ほうれい線、"
                   "毛束・毛流れ・ツヤのある髪、服のしわ・柄・ボタン・縫い目、指の描き分け、影・ハイライト・グラデーション、線の強弱・かすれ、アニメ調・劇画調・3D 調・ストックイラスト調の仕上げ、地面の線や影。")


def person_prompt(fam, sty, variant):
    f, s = FAMILIES[fam], STYLES[sty]
    if sty == "abst":
        return abst_prompt(f"person-{variant:02d}", *ABST_PALETTE[fam])
    if sty.startswith("yuru"):
        who = {
            1: "70代の女性が1人。受話器を耳に当てて、にこやかに予約の電話をしている立ち姿(全身)。年齢は白髪ではなく、落ち着いた髪色(灰茶)と服(カーディガン)と少し前かがみの姿勢で表す。",
            2: "70代の男性と、その娘とみられる40代の女性の2人。娘が父の腕に軽く手を添えて並んで立つ姿(全身)。2人とも口は笑顔の弧。",
        }[variant]
        return "\n".join([
            f"1. 役割: {ROLE}",
            f"2. {PROJECT_GENERIC}",
            f"3. 必須要素(前景の切り出し素材): {who} 服装は今の日本の普段着(カーディガン、ブラウス、スラックス、スニーカー)。着物・杖・白髪で高齢者を記号化しない。人物は画面中央にひとかたまりで配置し、画面端に触れさせない。",
            f"4. 因子: 描法 = {s['label']}: {s['desc']} 色: 肌は薄いベージュ 1 色、服の 1 か所に {f['palette'].split('、')[0]}、他は {f['label']}の淡色・紙白・黒・灰茶のみ。",
            f"5. 制約: {AI_REALISM_BANS} 背景は必ず完全に均一なベタ塗りの #00FF00(純緑)のみ(白や他の色の背景は不可)。地面・床・影・机・椅子・電話機本体・小物・景色を一切描かない(受話器は手に持つものだけ)。"
            f"画像比率は 3:4。{COMMON_BANS}",
            "6. 参照: 添付1 = スタイル見本(幾何図形で描いた人物図。頭身・点目・ミトンの手・単色ベタ・均一線という『作り』だけを真似る。ポーズや服の形は真似なくてよい)、添付2 = 色チップ。",
            "7. 出力: 1枚の PNG。文字なし。",
        ])
    who = {
        1: "70代の女性が1人。自宅の玄関先で、少し身を乗り出して固定電話の受話器(またはスマートフォン)を耳に当て、穏やかに笑って予約の電話をしている全身像。",
        2: "70代の男性と、その娘とみられる40代の女性の2人。乗合タクシーに乗り込もうとして、娘が父の手を軽く支えている全身像。表情は明るくリラックス。",
    }[variant]
    return "\n".join([
        f"1. 役割: {ROLE}",
        f"2. {PROJECT_GENERIC}",
        f"3. 必須要素(前景の切り出し素材): {who} 顔をはっきり描き、目・口の表情があること。服装は今の日本の普段着(カーディガン、ブラウス、スラックス、スニーカーなど)。"
        "着物・杖・白髪だけで高齢者を記号化しない(髪型・体格・服に個性を持たせる)。人物は画面中央にひとかたまりで配置し、画面端に触れさせない。",
        f"4. 因子: 描法 = {s['label']}: {s['desc']}。色: {f['label']}のパレットと調和する色(肌・髪は自然な色、服の差し色に {f['palette'].split('、')[0]} を1か所)。",
        "5. 制約: 背景は必ず完全に均一なベタ塗りの #00FF00(純緑)のみ(白や他の色の背景は不可)。地面・床・影・机・椅子・電話機本体・小物・背景の景色を一切描かない(受話器やスマートフォンは手に持つものだけ)。人物の輪郭に緑色のにじみ(フリンジ)を出さない。"
        f"画像比率は 3:4。{COMMON_BANS}",
        "6. 参照: 添付 = 色チップ。",
        "7. 出力: 1枚の PNG。文字なし。",
    ])


def vehicle_prompt(fam, sty):
    f, s = FAMILIES[fam], STYLES[sty]
    if sty == "abst":
        return abst_prompt("vehicle-01", *ABST_PALETTE[fam])
    if sty.startswith("yuru"):
        return "\n".join([
            f"1. 役割: {ROLE}",
            f"2. {PROJECT_GENERIC}",
            "3. 必須要素(前景の切り出し素材): 乗合タクシーの車両 1 台を、子ども向け絵本のように数本の線で単純化した箱型の白いワゴン(ミニバン)として描く。日本仕様の右ハンドル・左側通行。"
            "斜め前(車の左前が見える向き。左側のスライドドアが見える)から見た全体像。窓は 1 色のベタ、タイヤは黒い丸+灰の円、グリルは横線 2 本、ヘッドライトは単純な形 1 つ。"
            "ドアハンドル・ミラー・ワイパー・ナンバープレートの文字・エンブレム・ラッピング・ロゴは描かない(ナンバープレートは無地の小さな矩形)。運転席の人物は黒いシルエット 1 つ。",
            f"4. 因子: 描法 = {s['label']}: {s['desc']} 色: 車体は白、窓は {f['label']}の淡色、ドアの帯に {f['palette'].split('、')[0]} を 1 本。車両全体で 5 色以内。",
            f"5. 制約: {AI_REALISM_BANS} 背景は完全に均一なベタ塗りの #00FF00(純緑)のみ。地面・影・道路・景色を一切描かない。車両は画面中央、画面端に触れさせない。"
            f"画像比率は 4:3。{COMMON_BANS}",
            "6. 参照: 添付1 = スタイル見本(幾何図形で描いた人物図。均一線・単色ベタという『作り』だけを真似る)、添付2 = 色チップ。",
            "7. 出力: 1枚の PNG。文字なし。",
        ])
    return "\n".join([
        f"1. 役割: {ROLE}",
        f"2. {PROJECT_GENERIC}",
        "3. 必須要素(前景の切り出し素材): 乗合タクシーの車両1台。白いワゴン(ミニバン)型で、日本仕様の右ハンドル・左側通行。斜め前(車の左前が見える向き。歩道側=左側のスライドドアが見える)から見た全体像。車両の右側面は見せない(運転席側を手前にしない)。"
        "運転席側(車体の右側)に運転手のシルエットは入れてよいが顔は描かない。ナンバープレートは無地。フロントグリルの中央にエンブレム・紋章・丸い飾りを描かない(グリルは横線だけ)。車体にロゴ・文字・電話番号・ラッピング模様を入れない。ルーフに小さな行灯(社名なし)は可。",
        f"4. 因子: 描法 = {s['label']}: {s['desc']}。色: 車体は白、窓は {f['label']}のパレットの淡色、差し色(ドアのラインなど)に {f['palette'].split('、')[0]} を1本。",
        "5. 制約: 背景は完全に均一なベタ塗りの #00FF00(純緑)のみ。地面・影・道路・景色を一切描かない。車両は画面中央、画面端に触れさせない。"
        f"画像比率は 4:3。{COMMON_BANS}",
        "6. 参照: 添付 = 色チップ。",
        "7. 出力: 1枚の PNG。文字なし。",
    ])


def motif_prompt(fam, sty):
    f, s = FAMILIES[fam], STYLES[sty]
    return "\n".join([
        f"1. 役割: {ROLE}",
        "2. 案件: 群馬県高崎市倉渕(くらぶち)地区の乗合タクシー案内パンフレット。読み手は70代中心の地域住民と家族。",
        "3. 必須要素(地域モチーフ): 倉渕から見た榛名山(はるなさん)の山並みのシルエット/簡略画。左寄りに丸みのある円錐形の独立峰『榛名富士』、その右に『相馬山』などのごつごつした峰が横に連なる特徴的な稜線を、単純化して横長に描く。"
        "山並みは不透明で、画像の左端から右端まで途切れずに続き、下辺は画像の下端で水平に切れていること(後で背景の稜線の上に重ねる)。手前の里・人物・車両・建物・文字・雲は描かない。"
        "山並みを四角い枠や線で囲まない。画像の外周に線や枠を一切描かない。山並みは1つだけ描き、その上や後ろに半透明の遠景・霞・影・重複した山並みを重ねない(不透明な色面だけで構成)。",
        f"4. 因子: 描法 = {s['label']}: {s['desc']}。色: {f['label']}のパレットの濃色〜中間色 2〜3 段で(遠い峰ほど淡く)。",
        "5. 制約: 背景は完全に均一なベタ塗りの #00FF00(純緑)のみ(山並みの上の空も緑)。山の塗りは平坦なベタ塗りで、ぼかし・グラデーション・霞を使わない。"
        f"画像比率は 21:9(横長)。{COMMON_BANS} 富士山型の単峰にしない。",
        "6. 参照: 添付 = 色チップ。",
        "7. 出力: 1枚の PNG。文字なし。",
    ])


# ---------------------------------------------------------------- API
def load_key():
    key = os.environ.get("GEMINI_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("GEMINI_API_KEY が見つかりません(.env に GEMINI_API_KEY=... を置いてください)")
    return key


def b64file(p: Path):
    return base64.b64encode(p.read_bytes()).decode()


def generate(key, model, prompt, refs, aspect, size, retries=3):
    parts = [{"text": prompt}]
    for r in refs:
        parts.append({"inline_data": {"mime_type": "image/png", "data": b64file(r)}})
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {"aspectRatio": aspect, "imageSize": size},
        },
    }
    url = ENDPOINT.format(model=model)
    for attempt in range(retries):
        r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=300)
        if r.status_code == 200:
            data = r.json()
            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        return base64.b64decode(part["inlineData"]["data"]), part["inlineData"].get("mimeType"), data.get("usageMetadata")
            raise RuntimeError(f"画像が返りませんでした: {json.dumps(data, ensure_ascii=False)[:800]}")
        if r.status_code in (429, 500, 503) and attempt < retries - 1:
            wait = 15 * (attempt + 1)
            print(f"  HTTP {r.status_code} → {wait}s 待って再試行", file=sys.stderr)
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:800]}")


def ledger_append(row):
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["id", "kind", "family", "style", "model", "route", "datetime", "aspect", "size", "prompt_file", "output_file", "status", "note", "prompt"])
        w.writerow(row)


# ---------------------------------------------------------------- jobs
def build_jobs(ns):
    fams = ns.families.split(",") if ns.families else list(FAMILIES)
    stys = ns.styles.split(",") if ns.styles else list(STYLES)
    only = set(ns.only.split(",")) if ns.only else {"bg", "person", "vehicle"}
    jobs = []
    if ns.stage == "candidates":
        for fam in fams:
            for sty in stys:
                base = f"{fam}-K2-{sty}"
                chips = MASKS / FAMILIES[fam]["chips"]
                if "bg" in only:
                    jobs.append(dict(id=f"{base}-bg-{ns.seq:02d}", kind="bg", family=fam, style=sty, prompt=bg_prompt(fam, sty),
                                     refs=[MASKS / "K2-mask-hero.png", chips], aspect="4:5", size=ns.size, out=LIB / "candidates"))
                style_ref = Path(ns.style_ref) if ns.style_ref else MASKS / "style-tile-person.png"
                fg_refs = ([style_ref, chips] if (sty.startswith("yuru") or sty == "abst") else [chips])
                if "person" in only:
                    for v in (1, 2):
                        jobs.append(dict(id=f"{base}-person-{v + 2*(ns.seq-1):02d}", kind="fg_person", family=fam, style=sty, prompt=person_prompt(fam, sty, v),
                                         refs=fg_refs, aspect="3:4", size=ns.size, out=LIB / "candidates"))
                if "vehicle" in only:
                    jobs.append(dict(id=f"{base}-vehicle-{ns.seq:02d}", kind="fg_vehicle", family=fam, style=sty, prompt=vehicle_prompt(fam, sty),
                                     refs=fg_refs, aspect="4:3", size=ns.size, out=LIB / "candidates"))
    elif ns.stage == "master":
        if not ns.ids:
            sys.exit("--ids に採用した基底案 id(例 aitoma-K2-hand-bg-01)を指定してください")
        for cid in ns.ids.split(","):
            fam, _, sty, kind, _ = cid.split("-")
            chips = MASKS / FAMILIES[fam]["chips"]
            jobs.append(dict(id=cid.replace("-bg-", "-bgmaster-"), kind="bg_master", family=fam, style=sty, prompt=bg_prompt(fam, sty),
                             refs=[MASKS / "K2-mask-hero.png", chips], aspect="4:5", size="4K", out=LIB / "masters"))
    elif ns.stage == "motif":
        for fam in fams:
            for sty in stys:
                chips = MASKS / FAMILIES[fam]["chips"]
                jobs.append(dict(id=f"kurabuchi-haruna-{fam}-{sty}-{ns.seq:02d}", kind="motif", family=fam, style=sty, prompt=motif_prompt(fam, sty),
                                 refs=[chips], aspect="21:9", size=ns.size, out=LIB / "candidates"))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["candidates", "master", "motif"], default="candidates")
    ap.add_argument("--only", help="bg,person,vehicle")
    ap.add_argument("--families")
    ap.add_argument("--styles")
    ap.add_argument("--ids")
    ap.add_argument("--seq", type=int, default=1, help="連番(2回目の生成は 2)")
    ap.add_argument("--style-ref", help="スタイル参照画像のパス(自前の権利物のみ。既定は masks/style-tile-person.png)")
    ap.add_argument("--size", default="2K", choices=["1K", "2K", "4K"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--dry-run", action="store_true", help="API を呼ばずプロンプトだけ書き出す")
    ap.add_argument("--force", action="store_true", help="出力が既にあっても再生成")
    ns = ap.parse_args()

    jobs = build_jobs(ns)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    key = None if ns.dry_run else load_key()
    for j in jobs:
        out = j["out"] / f"{j['id']}.png"
        pf = PROMPTS / f"{j['id']}.txt"
        pf.write_text(j["prompt"] + "\n")
        if ns.dry_run:
            print(f"[dry] {j['id']} aspect={j['aspect']} size={j['size']} refs={[r.name for r in j['refs']]} → {pf.relative_to(ROOT)}")
            continue
        if out.exists() and not ns.force:
            print(f"skip {j['id']}(既存)")
            continue
        for r in j["refs"]:
            if not r.exists():
                sys.exit(f"参照画像がありません: {r}(先に make_masks.py を実行)")
        j["out"].mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        print(f"gen  {j['id']} ...", end="", flush=True)
        try:
            png, mime, usage = generate(key, ns.model, j["prompt"], j["refs"], j["aspect"], j["size"])
        except Exception as e:
            print(f" 失敗: {e}")
            ledger_append([j["id"], j["kind"], j["family"], j["style"], ns.model, "gemini-api", dt.datetime.now().isoformat(timespec="seconds"),
                           j["aspect"], j["size"], str(pf.relative_to(ROOT)), "", "error", str(e)[:200], j["prompt"]])
            continue
        out.write_bytes(png)
        from PIL import Image
        w, h = Image.open(out).size
        print(f" {w}x{h} {time.time()-t0:.0f}s")
        ledger_append([j["id"], j["kind"], j["family"], j["style"], ns.model, "gemini-api", dt.datetime.now().isoformat(timespec="seconds"),
                       j["aspect"], j["size"], str(pf.relative_to(ROOT)), str(out.relative_to(ROOT)), "candidate",
                       f"{w}x{h} mime={mime} usage={json.dumps(usage) if usage else ''}", j["prompt"]])


if __name__ == "__main__":
    main()
