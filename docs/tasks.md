# タスク台帳(計画書 第II部の段取りに対応)

状態: [ ] 未着手 / [~] 作業中 / [x] 完了 / [?] 要確認

## 第1段
- [x] リポジトリ化(skill/ 展開・git init・package.sh)
- [x] 作業対象を複製ファイルへ切替+Step 0の対象ファイル確認
- [~] 準備①: 実測は完了(docs/prep/ 参照: 面表・TEXT 824件・フォント・imageHash 33件・色)。レイアウトマスクは C で作成済み(docs/library/masks/)。残り: PDF画質設定の場所(UI)、既存イラストの出所確認、`入稿済み`ページ作成
- [ ] 準備②: 現行3案件の所要・画面外操作の実測(S4の分母)
- [~] B.1 表紙フレーム改修(指示書 docs/briefs/B1-cover-refit.md)(`#`命名・`#キービジュアル`枠K2・`#地域モチーフ`・`#人物` `#車両`・`#帯` `#背景`・12pt未満#000000・`#config`)。**(2) 実施済み・差し替え待ち**(2026-09-27、作業用ページ「テンプレ改修_作業」2053:2。rename 86 / create 37 / hide 4 / move 3 / resize 2 / 黒化 16。結果 docs/reports/B1-after/、`#`ノード一覧 docs/prep/template-refit-inventory.json)。原本との差し替えは Hiro 確認後(手順は B1-after/README.md §6)。設計: docs/reports/B1-cover-refit-design.md
- [~] C ライブラリv0(指示書 docs/briefs/C-library-v0.md)(基底案 K2向け×描法2×4系統、切り出し人物・車両、tone.json最小版、くらぶち地域モチーフ)。(1) レイアウトマスク・色チップ・生成/キー抜き/台帳スクリプト完了(docs/library/, scripts/library/)。(2) 2K 候補生成は `.env` の GEMINI_API_KEY 待ち。(5) Figma 投入は Figma MCP の認証待ち
- [x] E 第1層最小版(指示書 docs/briefs/E-preflight.md)(P1・P2・P3-a・P4単色・P6・P7・P12)。`skill/scripts/preflight.js` + `skill/references/preflight.md`。2026-09-27 レビューの CONFIG 決定(Warn/注記 9pt・10pt/白抜き役割別/電話 ×2・×3/折り線種別/label/PT_BY_FAMILY.MITT/ignored_tight)を反映し、制作物8枚+テスト4枚で再実測(docs/reports/E-test-report.md §A)。残: A4_spot の実測(B.1 の作業用ページで)、D での組み込み、第2段で Warn→Fail 格上げ
- [ ] D スキル2026-10版(指示書 docs/briefs/D-skill-2026-10.md)(Step別改訂・変換表・ラッパー自動化・参照3ファイル)
- [ ] H(a) 技術MVP(くらぶちモック1件をモードDで通す)

## 要確認
- [x] 本文サイズ: k訂正後は現行値(24〜26px)≈12ptで計画基準と一致。P2は12pt=24pxで実装。MITTの15pxのみ要判断
- [x] 折り構成: A3を横半分折り+巻き三つ折り(6面)。逆さ面あり/なしの両方式をテンプレ属性で対応(決定)
- [~] 欠落フォントはHiroがインストールして解消(Source Han Sans JP Medium/Bold, Hiragino Kaku Gothic Pro W6, ADS-piccolo)。許可外3種(Baloo Paaji / Yusei Magic / Titan One)は許可リストに追加予定
- [?] `M PLUS Rounded 1c`はFigma上に無く`Rounded Mplus 1c`(+`Rounded Mplus 1c Bold`) → 許可リストの表記を修正
- [x] 完成見本は空。実案件の完成品は`参照`ページ → 較正セット(a)は参照ページから(決定)
- [?] あいとま表紙18:2はフレーム自体が180°回転。複製にも引き継がれる → 正立化の扱い
- [x] グリーン系テンプレートは新版の系統に含めない(決定)
- [?] 印刷会社は未定(決定後にP24・6.4の既定値を確認)
- [x] (E) preflight の CONFIG 既定値は 2026-09-27 レビューで決定(docs/reports/review-2026-09-27.md)し preflight.js に反映済み。MITT 系の `PT_BY_FAMILY` は MITT 系の複製で未検証(B.1 作業用ページで確認)

## 第2段(追加分)
- [ ] MITT系テンプレの本文サイズ引き上げ(15px=7.5pt → 12pt相当)。P2 の系統別オーバーライドを撤廃
