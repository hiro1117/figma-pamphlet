# タスク台帳(計画書 第II部の段取りに対応)

状態: [ ] 未着手 / [~] 作業中 / [x] 完了 / [?] 要確認

## 第1段
- [x] リポジトリ化(skill/ 展開・git init・package.sh)
- [x] 作業対象を複製ファイルへ切替+Step 0の対象ファイル確認
- [~] 準備①: 実測は完了(docs/prep/ 参照: 面表・TEXT 824件・フォント・imageHash 33件・色)。レイアウトマスクは C で作成済み(docs/library/masks/)。残り: PDF画質設定の場所(UI)、既存イラストの出所確認、`入稿済み`ページ作成
- [ ] 準備②: 現行3案件の所要・画面外操作の実測(S4の分母)
- [x] B.1 表紙フレーム改修(指示書 docs/briefs/B1-cover-refit.md)(`#`命名・`#キービジュアル`枠K2・`#地域モチーフ`・`#人物` `#車両`・`#帯` `#背景`・12pt未満#000000・`#config`)。**2026-09-27 差し替え済み**: テンプレートページの表紙4系統は 2053:3 / 2053:334 / 2053:682 / 2053:1002、`#config` 2057:2。原本は「テンプレ旧_20260927」(2064:2)に退避。結果 docs/reports/B1-after/、`#`ノード一覧 docs/prep/template-refit-inventory.json。skill/references/template-and-assets.md の id 表は D 前半で新 id に更新済み
- [x] C ライブラリv0(指示書 docs/briefs/C-library-v0.md)。完了 2026-09-27: 描法は抽象グラフィック(abst、Gemini アプリ生成)。4 系統×(背景・人物 2・車両)= 16 点 + くらぶち榛名山モチーフ 1 点を素材ページ `ライブラリ/<系統>` `案件/くらぶち` に投入、tone.json 4 本同梱、2K マスター。検証 4 フレーム。詳細 docs/reports/C-library-v0-progress.md、library-v0.json、ledger.csv
- [x] E 第1層最小版(指示書 docs/briefs/E-preflight.md)(P1・P2・P3-a・P4単色・P6・P7・P12)。`skill/scripts/preflight.js` + `skill/references/preflight.md`。2026-09-27 レビューの CONFIG 決定(Warn/注記 9pt・10pt/白抜き役割別/電話 ×2・×3/折り線種別/label/PT_BY_FAMILY.MITT/ignored_tight)を反映し、制作物8枚+テスト4枚で再実測(docs/reports/E-test-report.md §A)。MITT 系特例と A4_spot も 2026-09-27 に一時 clone で実測済み(§B)。残: 第2段で Warn→Fail 格上げ(D での組み込みと A4_spot の P12 対象外は 2026-09-27 D 前半で済)。2026-09-28 H(a) 先行版の指摘 4 点(改行入り電話番号・令和0年0月0日・P6 の字面判定・P3-b 枠はみ出し)を v5 で修正し H(a) clone と 12 フレームで再実測(E-test-report §C)
- [x] D スキル2026-10版(指示書 docs/briefs/D-skill-2026-10.md)。前半 2026-09-27(Step 0/1/1.5/1.7/2/4・参照ファイル、報告 D-skill-part1.md)、**後半 2026-09-28**: Step 3 = scripts/fill-text.js・place-images.js・recolor.js、Step 4 = autofix.js(自動修正 2 回)、Step 5 = wrapper.js(端色延長・P1 ラッパー寸法)、#AI表記 の記述削除、K2B_panel・新 id に見直し。制作物ページで単体試験(あいとま・那智勝浦)、報告 D-skill-part2.md、`dist/figma-pamphlet_2026-10.skill`、D-release-notes.md。題字枠(あいとま 2179:2・登別 2179:3)と中面 47:2 のタイトル枠(ロゴ+地名+乗降スポット)、#config の系統名キー化、凡例規則 8 の更新も 2026-09-28 に反映済み(Hiro OK)。パッケージ作り直し済み
- [x] H(a) 先行版: D の前にくらぶちモックを手作業で1件通す(指示書 docs/briefs/Ha-tech-mvp-pre.md)。draft1 で中断 2026-09-27 → **v2 テンプレで再実行 2026-09-28**: 作業用ページに表紙 2130:2・中面 2130:341、`書き出し` ページ 2139:53 にラッパー 2139:54 / 2143:2(303×426mm)。表紙は Hiro OK。preflight 表紙 Fail 5→2(残りはテンプレ由来の逆さ面フッター P6 と案件原稿のダミー番号 P7)。第2層試走 3.15 不合格(R3 題字・地名なし、R5 車両・山の描法不一致)。報告 docs/reports/Ha-tech-mvp-pre.md(D への申し送り §7)、評価全文 Ha-tech-mvp-pre-eval.md。PDF 確認済み(303.0×426.1mm、報告 §9。中面の電話番号はみ出しを発見)。題字は `#見出し:サービス名` 枠を足す(Hiro 決定)。中面スポット一覧は B.2
- [x] B.1 v2 表紙面を K2 用に組み直す(指示書 docs/briefs/B1v2-cover-relayout.md)。**2026-09-28 差し替え済み**: 採用 = 案B(Hiro 調整版)、4 系統展開(那智勝浦・登別・MITT も Hiro 調整)、テンプレ 0:1 の表紙 = 2105:342 / 2118:2 / 2118:359 / 2118:688。`#AI表記` 削除。記録: docs/prep/template-refit-inventory.json、template-and-assets.md の id 表と枠表、library-v0.json、報告 docs/reports/B1v2-cover-relayout.md §8。残: SKILL.md 等の `#AI表記` 記述の削除(D 後半)、ライブラリのマスク再生成(C)、H(a) 再実行。2026-09-28 追記: サービス紹介面のアイコン 3 種の位置を H(a) MVP に合わせて 3 系統に反映(報告 §9、decisions に戻し値)。2026-09-28 追記2: 中面 47:2 / 48:513 の地図ピン(760:2・623:20 / 48:997・48:1091・48:1095)を削除、削除前を 2064:2 に退避(2149:2 / 2149:311)、報告 §10。28:178 にピンは無し
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
- [x] (E) preflight の CONFIG 既定値は 2026-09-27 レビューで決定(docs/reports/review-2026-09-27.md)し preflight.js に反映済み。MITT 系の `PT_BY_FAMILY` は改修済み MITT 表紙 2053:1002 の一時 clone で発火を確認(本文 15px → Warn、E-test-report §B-1)

## 第2段(追加分)
- [ ] MITT系テンプレの本文サイズ引き上げ(15px=7.5pt → 12pt相当)。P2 の系統別オーバーライドを撤廃
