# prep/ — figma-pamphlet 改修のための Figma 実測(読み取り専用)

対象: fileKey `09Js7rndbabLAoCchqzX9j`(本番の複製)。2026-09-26 に `use_figma`(read-only コードのみ)と `get_screenshot` で計測。**書き込み操作は一切なし。**

## ファイル一覧

| ファイル | 1行説明 |
|---|---|
| `face-table.md` | 面表。9フレームの寸法・向き・回転・clipsContent・直下の子・面(面:〜)構成・逆さ面の実装方式(葉ノード個別180°回転、あいとま表紙はフレーム自体が180°)・表4の正立スクショの取り方の提案 |
| `text-inventory.json` | 全 TEXT 824 ノードの機械可読一覧(id, name, chars20, fontFamily/Style, fontSize px(mixedは配列), sizePt, fills, フレームローカル x,y,w,h, rotInFrame, textAutoResize, parent, face, visible, hasMissingFont, align, charLen, class) |
| `text-inventory.md` | 上記の読み物版。サイズ分布・本文の実測(24〜26px≈8.4〜9.2pt、MITTは15px)・欠落フォント一覧・系統別の `#本文/#注記/#見出し/#電話/#CTA/#QR/#バッジ/#AI表記` 候補表・フレーム別の全TEXT表(繰り返し行は畳んである) |
| `fonts.md` | 7ファミリの利用可能スタイル(M PLUS Rounded 1c は無し→ `Rounded Mplus 1c`/`Rounded Mplus 1c Bold` で存在)、9フレーム+テンプレページ+参照ページ+テストページの使用フォント集計、hasMissingFont の一覧 |
| `image-inventory.json` | IMAGE fill を持つ48ノード(imageHash・scaleMode・画像px実測)、原本imageHash台帳33件、ベクターイラストグループ43件、`#〇〇置き場` プレースホルダ73件、素材ページの直下グループ構成、制作物ページの直下 |
| `colors.md` | フレーム別の SOLID fill/stroke/TEXT fill の一意色と出現数、系統別の濃/淡/紙白/文字色の推定、12pt未満の文字の fill 色 |
| `file-facts.md` | documentColorProfile(SRGB)、ページ一覧と子数、テンプレページ13ノード、凡例フレームの全文、素材ページ、テスト_真四角町ページの概要、完成見本ページが空であること |
| `shots/` | 検証用サムネイル: `shot_18-2_canvas.png`(あいとま表紙はキャンバス上で上下逆)、`shot_756-20_canvas.png`(那智勝浦の逆さ面グループをそのまま撮影=逆さ)、`shot_756-20_rot180.png`(PILで180°回転=正立で読める)、`shot_28-178_canvas.png`(スポット表は横長・正立)、`shot_47-2_canvas.png` |
| `raw/` | use_figma の生出力(JSON)と、text-inventory を生成した Python スクリプト。数値の出典 |

## 主要な発見(要約)

1. 逆さ面(表4側)は「面:〜(逆さ面)」グループで区切られているが、回転は**葉ノード個別の180°**。Vector 化された逆さ絵はない。あいとま系表紙 18:2 だけ**フレーム自体が180°回転**して置かれており、複製してもその回転が引き継がれる(テストページの複製2枚とも rot180)。
2. MITT系は逆さ面なし(6面・巻き三つ折り。中面に「ガイド:面付け枠(6面)」563×1196×6)。表紙面(右上)は高さ1216で折り線を20px越える。
3. 乗降スポット表 28:178 はノード 794×1123(縦)を rotation 90 で横置きし、中身を−90°で打ち消している。縮尺が冊子の約1/2.13(3.78 px/mm)。
4. 本文サイズの実測: あいとま/那智勝浦/登別 表紙 = 24〜26px(A4前提で ≈8.4〜9.2pt)、MITT = 15px(≈5.3pt)。12pt(34px)級の本文はどのテンプレにも無い。注記 13〜22px。
5. フォント: 使用17種。7ファミリ外 = Baloo Paaji(数字)、Yusei Magic(MITT見出し)、Titan One(スポット番号)、**欠落 = Source Han Sans JP(Medium/Bold、ノード55件)、Hiragino Kaku Gothic Pro W6(71件、48:2の❶)、ADS-piccolo(1件)= hasMissingFont 計127ノード**。`M PLUS Rounded 1c` は Figma 上に無く `Rounded Mplus 1c`(+`Rounded Mplus 1c Bold`)。
6. 画像: IMAGE fill は表紙4フレームのみ48ノード・**imageHash 33種**(共通: MITTアプリバナー 800×540、Cicacロゴ 225×225、雨/雪/晴れ/雪だるま 78〜79×70 の小画像など)。中面・スポット表には IMAGE fill が無く、地図・写真は全て `#〇〇置き場`(#E6E6E6 + #999999 破線)。`#地図置き場` は 47:2/48:2 で locked。
7. 色: 現行スキルの色対応表とほぼ一致。追加事実: 那智勝浦・登別の表紙フレーム fill がピンク #F4AEC1 のまま、登別は茶 #513A1E を文字・strokeに多用、MITT の本文黒は #231815・注記 #404040、あいとま中面の分類色 #1E5DBA/#D81B60/#1FA64A、登別中面の番号バッジ赤 #E60012。
8. 完成見本ページ(7:3)は空。制作物ページに4案件(くらぶち/くろほね/あずま/デモ)、素材ページに5グループ。テストページは「Fable 5.1」「Opus」ラベル付きの比較テスト2組。

## 調べられなかった項目・理由

- **本番ファイル(5qm3YRTEUDdb9RxFUI7ECL)との差分**: 指示により複製のみを読んだ。ノードIDは複製元と一致すると推定されるが未確認。
- **画像の実データ(バイト)・出所**: `getImageByHash().getSizeAsync()` で px 寸法のみ取得。`getBytesAsync` は行っていない(不要かつ重いため)。
- **参照ページ(6:2)の面構造・色・テキスト詳細**: フォント集計と直下104ノードの一覧のみ。TEXT 2,055 件の個別列挙は範囲外。
- **制作物ページの4案件の中身**: 直下グループ名・寸法のみ(内訳は未展開)。
- **グリーン系テンプレート(260:2/260:272/276:2)**: 対象外指定のため、寸法・回転のみ記録(fonts の「テンプレページ全体」集計には含まれる)。
- **物理サイズ(A4/A3)**: Figma 上に情報なし。pt 換算はすべて「フレーム=A4」を仮定(MITT系は要確認)。
- **get_screenshot の画像URL経由ダウンロード**: 本環境のプロキシが figma.com をブロックするため不可。`enableBase64Response:true` で代替(shots/ はその保存物)。
- **24:2 の非表示イラストフレーム(24:4/24:1520、計約2,900ノード)の内部構造**: VECTOR 中心であること・IMAGE fill を含まないことのみ確認(内部の個別列挙は省略)。
- 面グループ外に置かれた `#QR置き場` 20:6(那智勝浦・装飾:背景(逆さ面)内)の意図は不明(要確認)。
- 48:513 の `行:乗降場所060` と `061` が同じ y にある理由(テンプレ側の並びミスと推定)。
