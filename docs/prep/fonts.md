# フォント実測(fonts.md)

計測: `await figma.listAvailableFontsAsync()`(この Figma 環境で読み込めるフォント 8,927 件)と、テンプレート9フレーム/テンプレートページ全体/参照ページ(6:2)/テスト_真四角町ページの TEXT を `getStyledTextSegments(['fontName'])` でセグメント単位に集計(1ノード内に複数フォントがあれば各1カウント)。完成見本ページ(7:3)は**子ノード0件**のため集計対象なし。

## (1) 7ファミリの利用可能スタイル(listAvailableFontsAsync)

| ファミリ | 結果 | スタイル |
|---|---|---|
| Noto Sans JP | あり | Thin, Light, DemiLight, Regular, Medium, Bold, Black(7) |
| BIZ UDPGothic | あり | Regular, Bold |
| BIZ UDGothic | あり | Regular, Bold |
| Zen Maru Gothic | あり | Light, Regular, Medium, Bold, Black |
| Zen Kaku Gothic New | あり | Light, Regular, Medium, Bold, Black |
| **M PLUS Rounded 1c** | **無し**(その名前のファミリは0件) | ― ※代わりに **`Rounded Mplus 1c`**(Thin, Light, Regular, Medium, ExtraBold, Black)と **`Rounded Mplus 1c Bold`**(Bold のみ、別ファミリ名扱い)が存在。Figma 上の Google Fonts "M PLUS Rounded 1c" はこの名前で登録されている(推定)。`loadFontAsync({family:'M PLUS Rounded 1c'})` は失敗するので注意 |
| M PLUS 1p | あり | Thin, Light, Regular, Medium, Bold, ExtraBold, Black |

関連して存在するもの: BIZ UDMincho / BIZ UDPMincho(Regular, Bold)、M PLUS 1 / M PLUS 2 / M PLUS 1 Code / M PLUS Code Latin、Zen Kaku Gothic Antique、Zen Old Mincho、Zen Antique、Baloo Paaji(Regular のみ)、Baloo Paaji 2(Regular〜ExtraBold)、Titan One(Regular)、Yusei Magic(Regular)。
存在しないもの(テンプレで使われているが環境に無い): **Source Han Sans JP、Hiragino 各種、ADS-piccolo、YuGothic、DNP ShueiMGoStd、DIN 2014**。

## (2) 実際に使われているフォント(family / style)と使用数

### テンプレート9フレーム(合計 TEXT 824)

| family / style | 18:2 | 20:2 | 21:2 | 24:2 | 47:2 | 48:2 | 48:393 | 48:513 | 28:178 | 合計 | 7ファミリ内? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Noto Sans JP / Bold | 17 | 13 | 16 | 25 | 4 | 144 | 20 | 4 | 7 | **250** | ○ |
| Noto Sans JP / Regular | 1 | 1 | – | 16 | 19 | – | – | 122 | 1 | 160 | ○ |
| Noto Sans JP / Medium | 4 | 7 | 7 | 2 | – | – | – | – | – | 20 | ○ |
| Noto Sans JP / Black | 2 | 2 | – | – | – | – | – | – | 1 | 5 | ○ |
| Rounded Mplus 1c / ExtraBold | 15 | 31 | 28 | – | 4 | 9 | 7 | – | 2 | 96 | △(実体は M PLUS Rounded 1c。Figma 名が違う) |
| Rounded Mplus 1c Bold / Bold | – | 5 | – | 3 | 36 | 1 | 20 | – | – | 65 | △(同上、Bold は別ファミリ名) |
| Rounded Mplus 1c / Medium | 2 | 5 | 2 | – | – | – | – | – | – | 9 | △ |
| Rounded Mplus 1c / Black | – | – | 1 | – | – | – | – | – | – | 1 | △ |
| Zen Maru Gothic / Bold | 1 | – | 3 | 1 | – | – | – | – | – | 5 | ○ |
| Zen Maru Gothic / Black | – | – | – | 2 | – | – | – | 2 | – | 4 | ○ |
| <span style="color:red">**Baloo Paaji / Regular**</span> | 24 | 19 | 17 | – | 3 | – | 3 | – | 9 | **75** | ✗(7ファミリ外。Google Fonts の欧文丸ゴ。環境にあり) |
| <span style="color:red">**Source Han Sans JP / Medium**</span> | 12 | 10 | 12 | – | – | – | – | – | – | 34 | ✗ **環境に無い(欠落)** |
| <span style="color:red">**Source Han Sans JP / Bold**</span> | 12 | 2 | 12 | – | – | – | – | – | 1 | 27 | ✗ **環境に無い(欠落)** |
| <span style="color:red">**Hiragino Kaku Gothic Pro / W6**</span> | – | – | – | – | – | 71 | – | – | – | 71 | ✗ **環境に無い(欠落)**。48:2 の停留所マーク "❶" 全71件 |
| <span style="color:red">**Yusei Magic / Regular**</span> | – | – | – | 9 | – | – | – | – | – | 9 | ✗(7ファミリ外。Google Fonts、環境にあり)MITT表紙の見出し |
| <span style="color:red">**ADS-piccolo / Regular**</span> | 1 | – | – | – | – | – | – | – | – | 1 | ✗ **環境に無い(欠落・非Google)** 596:12 #表紙サブコピー |
| <span style="color:red">**Titan One / Regular**</span> | – | – | – | – | – | – | – | – | 1 | 1 | ✗(7ファミリ外。Google Fonts、環境にあり)28:215 #スポット番号 |

テンプレートページ全体(グリーン系・凡例を含む TEXT 993 件)でも同じ17種のみ(追加ファミリなし)。欠落 129 件。

### 参照ページ 6:2(原本アーカイブ、TEXT 2,055 件、欠落 830 件)

7ファミリ内: Noto Sans JP Bold 81 / Medium 23 / Regular 16 / Black 34、BIZ UDPGothic Bold 84、Zen Kaku Gothic New Bold 14 / Black 6 / Medium 2、Zen Maru Gothic Bold 6。
<span style="color:red">7ファミリ外</span>: Rounded Mplus 1c ExtraBold 273 / Medium 28 / Black 5、Rounded Mplus 1c Bold 162、Hiragino Kaku Gothic Pro W6 273(欠落)、Source Han Sans JP Bold 244 / Medium 142 / Heavy 10 / Normal 3(欠落)、Noto Sans Javanese Regular 294(!)、Baloo Paaji Regular 197、Hiragino Kaku Gothic Std W8 62(欠落)、Hiragino Kaku Gothic StdN W8 12(欠落)、Hiragino Kaku Gothic ProN W6 10(欠落)、Hiragino Maru Gothic Pro W4 5(欠落)、YuGothic Bold 28 / Medium 21(欠落)、ADS-piccolo Regular 26(欠落)、DIN 2014 Bold 8(欠落)、DNP ShueiMGoStd B 5(欠落)、Roboto ExtraBold 7、Titan One Regular 4、Inter Regular 2 / Bold 2、DM Sans Bold 1、Noto Sans Bold 1。
※「Noto Sans Javanese」294件はおそらく Source Han/Noto 系の自動置換痕跡と推定(参照ページなので改修対象外)。

### テスト_真四角町_20260914 ページ(664:2)

表紙2枚: Noto Sans JP Bold/Medium/Regular/Black、Baloo Paaji、Rounded Mplus 1c ExtraBold/Medium、Zen Maru Gothic Bold。672:2 のみ Source Han Sans JP Bold 5 + mixed 1(欠落6)。中面2枚: Rounded Mplus 1c Bold、Noto Sans JP、Baloo Paaji(欠落0)。
→ 前回テストではあいとま系の欠落フォント(Source Han Medium)が Noto Sans JP Medium に置き換わって出力されたことが分かる(664:3 は Noto Sans JP Medium 17 件・欠落0)。

## (3) hasMissingFont = true の TEXT

| フレーム | 件数 | 内訳 |
|---|---|---|
| 18:2 あいとま表紙 | 24 | Source Han Sans JP Medium 12 / Bold 12(#利用シーン1〜3本文、#利用上の注意、#STEP1/3本文、#料金1〜5区分、ラベル:円×5、#料金n注記、#料金小見出し(注記)、#運行時期注記、#アプリ紹介キャプション)、ADS-piccolo 1(596:12 #表紙サブコピー) |
| 20:2 那智勝浦表紙 | 10 | Source Han Sans JP Medium/Bold(625:5/7/9/11/13/15、625:24〜27 #電話予約手順1〜4) |
| 21:2 登別表紙 | 21 | Source Han Sans JP Medium/Bold(629:5/7/9/10/12/13/15/16/17、629:20〜32 料金区分・注記・円、629:34、629:43) |
| 24:2 MITT表紙 | 0 | |
| 47:2 あいとま中面 | 0 | |
| 48:2 那智勝浦中面 | **71** | Hiragino Kaku Gothic Pro W6(装飾:停留所マーク(01)〜(71)、627:43 ほか) |
| 48:393 登別中面 | 0 | |
| 48:513 MITT中面 | 0 | |
| 28:178 スポット表 | 1 | 633:6 #運休注記(Source Han Sans JP Bold) |

合計 127 ノード(Source Han Sans JP 55 / Hiragino 71 / ADS-piccolo 1)。全IDは text-inventory.json の `hasMissingFont` で抽出可能。

## 所見(事実ベース)

- 現テンプレの和文は実質「Noto Sans JP + Rounded Mplus 1c(+Bold)」の2系統、数字・欧文が Baloo Paaji。BIZ UD 系は参照ページ(過去原本)にのみ登場し、テンプレでは未使用。
- 7ファミリの指定名 "M PLUS Rounded 1c" では Figma 上でロードできない。丸ゴを使うなら `Rounded Mplus 1c`(ExtraBold 等)/`Rounded Mplus 1c Bold`(Bold)の名前で `loadFontAsync` する必要がある(推定: Google Fonts 側の旧ファミリ名)。
- 欠落フォントは3種(Source Han Sans JP、Hiragino Kaku Gothic Pro、ADS-piccolo)。Source Han Sans JP は Noto Sans JP と同一設計のフォント(Adobe 版)なので Noto Sans JP の同ウェイト置換が妥当。Hiragino W6 の "❶" は記号なので Noto Sans JP Bold で代替可能(字形は変わる)。ADS-piccolo(有料の手書き風丸ゴ)は代替が必要(推定: Zen Maru Gothic / Yusei Magic 等)。
