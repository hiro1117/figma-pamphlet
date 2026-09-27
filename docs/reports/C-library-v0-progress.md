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

## 2026-09-27 (3)〜(5) 完了: 前景・モチーフ・tone.json・Figma 投入

### 成果物
- `docs/library/final/` 17 点(背景 4・人物 8・車両 4・地域モチーフ 1)。前景は実 alpha PNG(`scripts/library/finalize.py` → `keyout.py`)
- `docs/library/tone/*.json` 4 本(6.2 スキーマ最小版、`scripts/library/make_tone.py`)。正規化後: main は白と 4.59〜7.9:1、cta は ground/白と 7.06:1 以上
- `docs/library/library-v0.json`: 素材ページ(7:4)の imageHash・px・配置想定・実効 dpi・グループ/ノード id
- `docs/library/ledger.csv` 56 行(adopted 18 / rejected 38)
- Figma 素材ページの新規グループ(既存 5 グループには触れていない):
  - `ライブラリ/あいとま系` 2068:4 / `ライブラリ/那智勝浦系` 2068:7 / `ライブラリ/登別系` 2068:10 / `ライブラリ/MITT系` 2068:13(各: 番号ラベル + 背景 580×720 + 人物A/B 高420 + 車両 幅360 + 非表示ロック `#tone`)
  - `案件/くらぶち` 2068:16(`#地域モチーフ 榛名山` 580×170 + 非表示 `#台帳`)
  - `検証/あいとま_K2組み` 2069:9(表紙面 564×1196 に #キービジュアル CROP + #地域モチーフ + #人物 + #車両 を組んだ確認用)
- スクショ: `docs/reports/C-shots/`(verify_aitoma_K2 / library_aitoma / project_kurabuchi)

### 受け入れ条件との対応
| 条件 | 結果 |
|---|---|
| 8 点の基底案(背景)+前景+くらぶちモチーフが素材ページにある | **背景は 4 点**(Hiro 決定で描法をフラット 1 種に絞ったため。手描き 4 点は台帳上 rejected、Figma には入れていない)。前景 12・モチーフ 1 は投入済み |
| 4K マスターの実効 dpi ≥ 200 | 4K は省略(Hiro 決定)。2K 背景を K2 枠 580px に置いて **463dpi**、人物 575〜740dpi、車両 676〜872dpi、モチーフ 765dpi |
| tone.json 最小版が同梱、main/cta の正規化 | 4 系統とも `#tone` 同梱。contrast_check を JSON 内に記録 |
| あいとま 1 系統の組み合わせスクショ(R1) | `検証/あいとま_K2組み` で確認: 人物高 420/711 = 59% ≥ 1/3、顔と車両はシルエットに隠れず枠内。**B.1 改修後の表紙フレームではなく素材ページ内の検証フレーム**で実施(「Figma への書き込みは素材ページの新規グループのみ」の制約のため) |
| tasks.md / decisions.md 更新 | 済 |

### 見つかった問題と対処
- Gemini は `imageSize` 2K 指定でも **JPEG バイト**を返す(mime=image/jpeg)。背景 4 点は JPEG のまま PNG 名でアップロードしたが Figma の IMAGE fill は正常。final/ の背景は後から本物の PNG に変換
- 前景の緑背景はムラ(#04CB2B〜#0BCC2A)があり、単純な色差しきい値では不足 → **外周から連結した領域だけを透明化するフラッドフィル方式**に変更。線で囲まれた穴(電話コードのコイル)は「有彩色キーのとき内部のキー色そのものも透明」で対応
- spill 抑制はキー色の主チャンネルを抑えるため、**白キーでは肌が灰緑になる**バグがあった → 有彩色キーのみ・外周近傍と穴の縁だけに限定
- 那智勝浦の人物 1 は 2 回とも背景が白で出た(青系パレットの影響?)→ 白をフラッドフィルで抜いて採用
- 那智勝浦の車両はグリルにエンブレム風の楕円 → 周囲色で塗りつぶし(`-01r`)。登別の車両は右側面向き → 再生成
- 地域モチーフは 3 回で採用(1: 枠線+ぼかし、2: 半透明の遠景、3: 空の小さなにじみ → `--clear-above 370` で除去)
- `upload_assets` の `nodeIds` 指定は既存ノードの fill 差し替えに使える(人物 3 点で使用)。zsh の `set -- $var` は単語分割しないので curl のループは関数で書く

### 未対応・次の担当者へ
- 登別の背景は稜線が上端から約 40% と高め(tone.json `horizon_ratio: 0.4` に記録)。地域モチーフの配置高さはこの値を使う
- `aitoma-K2-thin-person-02` の足元に短い地面線 2 本が残る(軽微、必要ならレタッチ)
- 手描き風候補(16 点)と太線フラット候補(16 点)は `docs/library/candidates/` に残置(比較用。Figma には未投入。`#案_透かし有` は透かし付き画像を使っていないため作っていない)
- B.1 改修後の表紙フレームでの本組みは技術 MVP(H(a))で行う。`#キービジュアル` は CROP、`#人物` `#車両` `#地域モチーフ` は FIT、素材は `library-v0.json` の nodeId を clone
- 生成コスト: Pro 2K 計 56 回(有料枠)

## 2026-09-27 描法の再検討(人物が AI らしくリアル寄り → 抽象グラフィックへ)
- Hiro 判断: thin/noline の人物・車両は「AI 生成らしいリアル寄りの質感」で不採用。参照ページの人物イラスト系統を調査(`docs/library/illustration-style-research.md`)
- Hiro 提供の英語プロンプト(抽象グラフィック、参照画像なし)を描法 `abst` として `scripts/library/prompt_abst.py` に組み込み。肌色は person-02 実測の #F5CEC1 に固定
- 生成経路は **Gemini アプリ(Google AI Pro)で Hiro が手動生成**(API 費用ゼロ)。4K JPEG で受領、四隅に可視透かしなしを確認(SynthID は残る)。台帳の route = gemini-app
- あいとま系 4 点(背景・人物 2・車両)を final/ に加工(長辺 4096、キー抜き)し、素材ページに `ライブラリ/あいとま系(abst 比較用)` 2074:3 と `検証/あいとま_K2組み_abst` 2074:11 を追加。細線版のグループ・検証はそのまま残して比較できる状態
- keyout.py を支配度ベースに書き直し(明るさの違う緑の帯・島も透明化、境界の despill)。アプリ出力は緑が 2 段になることがあるため必須
- 残: 採否の決定(abst 採用なら 他 3 系統もアプリで生成 → 投入、細線版グループの整理、tone.json の illustration.style 更新、地域モチーフの描法合わせ)

## 2026-09-27 Claude in Chrome で Gemini アプリを自動操作(車両・背景の作り直し)
- 経路: gemini.google.com の「Images」モード(Hiro のログイン済み Chrome を Claude in Chrome で操作)。モデル Pro、比率は 4:3 / 3:4 を UI で選択。プロンプトは `paste/` の 1 行化版をタイプ入力(contenteditable は form_input 不可、Enter 送信のため改行を除去)
- 解像度: 画像モードの初回生成は Nano Banana 2(1K, 1200×896)。「Redo with Pro」または「Output at 4K」の追記で Nano Banana Pro になるが、保存ファイルは **2K(2400×1792 / 1792×2400)**。UI の「4K」表記と保存解像度は一致しない。K2 配置での実効 dpi は背景 447・車両 746 で基準 200 を満たす
- 車両の向き: 「左側面(スライドドア側)を見せる」指示を 3 回試しても Pro は右側面向きを返した。**運転手シルエットなしの版を作らせ、こちらで左右反転**して解決(`aitoma-K2-abst-vehicle-02m`)。運転手がいないので右ハンドルと矛盾しない
- 背景: `aitoma-K2-abst-bg-02`(稜線 54%、民家 1・木 1)。Redo 版 bg-03 は予備(rejected)
- Figma: `ライブラリ/あいとま系(abst 比較用)` の 2073:2 / 2073:5 を `upload_assets` の nodeIds 指定で差し替え、検証 v2(2074:4)の #キービジュアル/#車両 も更新。スクショ `C-shots/verify_aitoma_K2_abst_v2.png`
- 注意: Chrome 拡張は一度「not connected」を返したが再試行で復帰(一過性)。ダウンロードは Chrome 既定の ~/Downloads に `Gemini_Generated_Image_*.jpeg` で保存される
- 2026-09-27 車両を再度作り直し(Hiro 指示: 屋根と行灯が同色、軽バンは不可)。プロンプトに「中型ミニバンのタクシー(軽バン・セダン・バス不可)」「屋根は白、行灯はアクセント色」「運転手なし」を明記 → Pro 2K で左側面向きが一発で出た(`aitoma-K2-abst-vehicle-03`、反転不要)。Figma 2073:5 / 検証 v2 を差し替え

## 2026-09-27 残り 3 系統を Claude in Chrome で自動生成(進行中)
- 那智勝浦・登別: 背景・人物 2・車両の 4 点ずつ生成 → キー抜き → 素材ページに `ライブラリ/那智勝浦系` 2078:7、`ライブラリ/登別系` 2082:4 と検証グループ(2079:8、2083:8)を作成。thin 版グループは `#旧` に改名
- MITT: 背景生成・投入済み(2084:2)、人物・車両は続行中
- 自動操作の知見: 画像モードの「Aspect ratio」は navigate 直後の 1 クリック目が効かない(2 回目で開く)。テキスト入力は find で textbox の ref を取り click → type。送信は Return ではなく送信ボタン座標(926,470)。**ダウンロードは座標クリックだと失敗することがあり、`javascript_tool` で aria-label="Download full size image" の button を .click() するのが確実**。生成待ちは 100〜150 秒(バッチの合計待機は 100 秒以内にしないとツールがタイムアウト)

## 2026-09-27 4 系統の abst 素材が揃った(Hiro 確認待ち: 那智勝浦・登別・MITT)
- 生成: 那智勝浦 4 点(一発)、登別 4 点(一発)、MITT 4 点(人物 02 は肌が赤みに寄り Redo → 03)。すべて Gemini アプリ画像モード Pro 2K、可視透かしなし
- 素材ページ: `ライブラリ/那智勝浦系` 2078:7 / `ライブラリ/登別系` 2082:4 / `ライブラリ/MITT系` 2088:3(各: ラベル+背景 580×777+人物 A/B 高 420+車両 幅 360+非表示 `#tone`)。検証: 2079:8 / 2083:8 / 2088:10。旧 thin/noline グループは `#旧` に改名
- tone.json 4 本を abst 版に更新(`illustration.style` = flat_vector_no_outline、`horizon_ratio` は各背景の実測 0.54 / 0.62 / 0.65 / 0.68、`source` = library_gemini_app_2k)。旧版は `_old_` で残置
- 実効 dpi: 背景 447(2K を K2 枠 580px に配置)、人物 667〜724、車両 803〜825
- 残: Hiro の採否確認 → 台帳 adopted 化、榛名山モチーフの abst 化(あいとま)、`#旧` グループの削除判断、B.1 テンプレでの本組み(H(a))
- 2026-09-27 Hiro 指示: `#旧` 5 グループを削除。MITT の人物 B → person-04(Hiro 手動、4K→長辺 3300 に縮小。upload_assets は 10MB 上限)、背景 → bg-02(青紫の空。服と同系色の回避)。Figma 2084:2 / 2086:2 の fill を差し替え、#tone と検証 MITT を更新
- 2026-09-27 車両を 4 系統共通の JPN タクシー型に置換(Hiro 提供)。他 3 系統はアクセント色置換(マスク: 青支配・b>120・g>90 で行灯/ストライプのみ。明るさ下限なしだとグリルの紺まで色替えされ斑点が出る)。Figma のライブラリ車両ノードと検証 4 つの #車両 を差し替え。tone.json の vehicle desc を更新
