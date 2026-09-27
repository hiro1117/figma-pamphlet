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

## 2026-09-27 (2) 2K 候補の生成完了(採用待ち)

- モデル: `gemini-3-pro-image`(API の models.list で実在確認。既定値をこれに変更)。経路は Gemini API 有料枠、参照はマスクと色チップのみ
- 生成数: 背景 9(8 + mitt 手描きの再生成 1)、人物 16、車両 8 = 33 点。すべて `docs/library/candidates/`、台帳 `docs/library/ledger.csv` に 33 行
- 実寸: 背景 1856×2304(4:5)、人物 1792×2400(3:4)、車両 2400×1792(4:3)
- コンタクトシート: `_sheet-bg.png` / `_sheet-person.png` / `_sheet-vehicle.png`

### 所見(採用判断の参考)
- 背景: 8 系統×描法とも 人物・車両・文字・名所なし、稜線は単純。`mitt-K2-hand-bg-01` は枠線と白い余白が出たため不採用(台帳 rejected)、`-02` を再生成(問題なし)。稜線の高さは画像上端から約 40〜70% でばらつく(noboribetsu-flat は約 40% と高め)。地域モチーフの配置高さ(hero_horizon)は基底案ごとに tone.json に記録して吸収する
- 背景の空: mitt 手描きは紺→青の連続グラデーション(ブランド色内なので禁止の紫→青ではない)。noboribetsu 手描きは雲の形が大きめ
- 人物: 全点で顔・表情あり、普段着、記号化なし。手描き系は緑背景が均一でなく(明るい黄緑〜濃緑のムラ)、キー抜きは色相ベースに変更が必要(→ (3) で keyout.py を改修)。`noboribetsu-K2-flat-person-01` に縦線(電話コード?)が 1 本混入
- 車両: 白ワゴン・右ハンドル(運転手が窓の左側=車両右側)は概ね守られている。注意点: グリル中央に**エンブレム風の丸い形**が出ているものがある(aitoma-flat / nachikatsuura-hand / noboribetsu-flat)→ 採用時はレタッチか再生成。`noboribetsu-K2-hand-vehicle-01` は車両の右側面が見える向き(スライドドアが見えない)。手描き系の車両は実車に近い描写(写実寄り)

## 2026-09-27 トーン確定と再生成の着手(課金切れで停止)
- Hiro 決定: 手描き風は不採用、フラット 1 種(thin: あいとま/那智勝浦/登別、noline: MITT)。仕様 `docs/library/tone-spec.md`。探索生成は省略し Pro で 1 点確認 → 展開の方式
- `gen_candidates.py` に描法 `thin` / `noline` を追加。新描法の背景プロンプトは「余白の多い情景(平坦な空・稜線 1 本・道・地面、民家は 3 つまで)」に差し替え
- `aitoma-K2-thin-bg-01` の生成で **HTTP 402(プリペイドクレジット枯渇)**。台帳に error 行あり。AI Studio でクレジット追加後に再実行:
  `.venv/bin/python scripts/library/gen_candidates.py --stage candidates --only bg --families aitoma --styles thin`
