# C ライブラリ v0 — 進捗レポート(2026-09-26、(1) 完了・(2) 着手待ち)

## 済んだこと
- **レイアウトマスク**(準備①の残り): `docs/library/masks/` に K2 用(全体 `K2-mask-face.png`、ヒーロー枠のみ `K2-mask-hero.png`)、任意の K1 用、系統色チップ 4 枚。幾何図形のみ・文字なし。凡例と寸法は `docs/library/masks/README.md`。生成は `scripts/library/make_masks.py`(数値は physical-size.md から算出、k=5.69)
- **生成スクリプト** `scripts/library/gen_candidates.py`: Gemini API(`gemini-3-pro-image-preview`、`--model` で変更可)を `.env` の `GEMINI_API_KEY` で呼ぶ。stage = candidates(2K 候補 32 点)/ master(採用案の 4K 再生成)/ motif(くらぶち榛名山)。参照画像はマスクと色チップのみ。1点ごとに `docs/library/ledger.csv` へ追記。`--dry-run` でプロンプトだけ `docs/library/prompts/` に書き出す(33 本書き出し済み)
- **キー抜き** `scripts/library/keyout.py`: 色差 alpha + spill 抑制 + エッジ収縮 + 余白トリム。合成画像で動作確認済み
- **コンタクトシート** `scripts/library/contact_sheet.py`: 候補を系統×描法の格子に並べる(採用判断用)
- Python 環境: `.venv`(Pillow / numpy / requests、gitignore 済み)

## 止まっている理由
1. リポジトリに `.env` が無い(`GEMINI_API_KEY` 未設定)→ (2) の生成が実行できない
2. Figma MCP(plugin:figma)が未認証 → (5) の `upload_assets` / `use_figma` が使えない(こちらは (3)(4) の後で良い)

## 次にやること((2) 以降)
```
.venv/bin/python scripts/library/gen_candidates.py --stage candidates --only bg          # 背景 8 点
.venv/bin/python scripts/library/gen_candidates.py --stage candidates --only person,vehicle
.venv/bin/python scripts/library/contact_sheet.py --kind bg                              # _sheet-bg.png を確認
```
→ Hiro が採用案を選ぶ → `--stage master --ids ...`(4K)→ 前景を keyout → tone.json 最小版 → Figma 投入 → library-v0.json

## 設計メモ
- 比率: 102:125 は Gemini に無いので 4:5 で生成、Figma で CROP(decisions.md)
- 実効 dpi の見込み: K2 枠 580×711px に 4K(約 3264×4080px)を置くと 3264/580×144.6 ≈ 814dpi、2K でも ≈ 407dpi(基準 200 を満たす)
- モデル id は API の `models.list` で実在を確認してから使う(`gemini-3-pro-image-preview` が既定。違う場合は `--model`)
