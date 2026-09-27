# preflight.js — 第1層チェック(最小版)仕様書

対象: `skill/scripts/preflight.js`(2026-09-27 版 = レビュー `docs/reports/review-2026-09-27.md` の CONFIG 決定を反映。最小版 = P1・P2・P3-a・P4単色・P6・P7・P12)。
計画書 v5.1 §6.5 の第1層のうち機械判定できる 7 項目を `use_figma` 1 回で実行し、**Pass / Fail / Warn / Manual / Error** の 5 値で返す。Warn は「第2段の目標値に未達だが第1段では入稿を止めない」。オペレータには ○/✗/△ の要約だけを見せる(組み込みはスキル改訂 D)。

## 1. 前提

- Figma は複製ファイル `09Js7rndbabLAoCchqzX9j` だけ。テンプレート原本(ページ `テンプレート` 0:1)には走らせない(P3-a が一時 clone を書き込むため)。制作物・テスト・作業用ページで使う
- 1 回の `use_figma` で扱うのは 1 ページ(`CONFIG.PAGE_ID`)。複数ページは呼び出しを分けて並列に投げる
- シート種別 `CONFIG.SHEET`
  - `A3_booklet`: 1691×2392 または 2392×1691。k = 短辺 px ÷ 297 = 5.694 px/mm。折り線は長辺方向 2 本(1/3・2/3)+短辺方向 1 本(1/2)
  - `A4_spot`: 794×1123(乗降スポット表)。k = 794 ÷ 210 = 3.781 px/mm。折り線なし。**P12 は対象外**(`SHEETS.A4_spot.p12 = false`。このシートの本文はスポット名 40pt で、電話番号を本文の倍率で測る規則が合わないため。2026-09-27 Hiro 了承)
- フレーム種別 `CONFIG.FRAME_KIND`(`auto` = 名前に 表紙 → `cover`、中面 → `inner`、どちらも無ければ `cover`)。P6 の折り線種別に使う
- 系統 `CONFIG.FAMILY`(`auto` = 名前に MITT/ミット → `MITT`)。`PT_BY_FAMILY` の系統別しきい値に使う。**スキルからは系統選択(`#tone` の `meta.template_family`)をもとに明示して渡す**(§5-2)
- **しきい値は毎回 k から計算する**。`ptPx(pt) = round(pt × k × 25.4 / 72)`、`mmPx(mm) = round(mm × k)`

| 量 | A3_booklet(k=5.694) | A4_spot(k=3.781) |
|---|---|---|
| 12pt(本文・白抜き本文) | 24px | 16px |
| 10pt(注記の目標 Warn) | 20px | 13px |
| 9pt(注記の Fail、白抜き見出し/ラベルの Fail) | 18px | 12px |
| 7.5pt(MITT 系の本文 Fail) | 15px | — |
| 6pt(絶対下限) | 12px | 8px |
| 8mm(面境界の Warn) / 5mm(面境界の Fail) | 46px / 28px | — |

## 2. ステータスとしきい値の 2 段構え

- 各 item は `sev: 'Fail' | 'Warn' | 'Manual'`。チェックの `status` は Fail が 1 件でもあれば Fail、なければ Warn、なければ Manual、なければ Pass。`Error` はそのチェックだけ失敗(他は続行)
- しきい値は `{ fail, warn }`。`fail` 未満で Fail、`warn` 未満で Warn(`warn` 省略可)。目標値(warn)は第2段のテンプレ改修で `fail` に格上げする
- `summary` はフレームごとに `{ fail, warn, manual, pass, error, ignored_tight }`(ステータス別のチェック数と、P3-a で無視した tight 件数)

## 3. チェック定義

| ID | 対象 | 判定 | Fail | Warn | Manual |
|---|---|---|---|---|---|
| P1 作業寸法 | フレームの width/height | `SHEETS[SHEET].dims` と ±0.01px で一致 | 不一致(rescale 不可、複製をやり直す) | — | — |
| P2 文字サイズ | 可視 TEXT の全セグメント(`getStyledTextSegments(['fontSize','fills','fontName'])`) | 役割ごとに `PT[role]`(body `{fail:12}`、note `{fail:9, warn:10}`)、全セグメント `PT.absMin {fail:6}`、白抜き(fill 輝度 ≥ `WHITE_LUM` 0.85)は `PT.white[role]`(body/note/phone `{fail:12}`、heading/label/other `{fail:9, warn:12}`)。系統別 `PT_BY_FAMILY`(MITT: body `{fail:7.5, warn:12}`)で上書き。複数規則に当たれば最も重い方を採る。同一ノードでは (px, 規則, 重さ) が同じ違反を 1 件に畳む | fail 未満 | warn 未満 | — |
| P3-a 文字あふれ | `textAutoResize === 'NONE'` の可視 TEXT | 全フォントを `loadFontAsync` → `clone()`(名前 `__preflight_tmp__`、非表示)→ **`textAutoResize='HEIGHT'`(箱幅で折り返した高さ hFit。必ず先)→ `'WIDTH_AND_HEIGHT'`(自然高さ hNat)** → **finally で `clone.remove()`**。`diff = hFit − 箱高` が `OVERFLOW_TOL_PX`(1px)を超え、かつ「hFit > hNat+1(折返しが増えた)」または「diff ≥ 1行高 × `TIGHT_RATIO`(0.5)」なら あふれ。それ以外(単行バッジの箱が行高より少し低いだけ = tight)は `TIGHT_BOX`('ignore' 既定 / 'manual' / 'fail')に従い、ignore の件数を `summary.ignored_tight` に出す | あふれ | — | `hasMissingFont`、フォントロード失敗、clone 失敗 |
| P4 コントラスト(単色背景) | 役割 body/note/phone(7:1)・heading/label(4.5:1)。`CONTRAST.other = null` は対象外 | 前景 = セグメント fill(可視 SOLID stroke があれば袋文字としてその色)。背景 = 描画順で TEXT より手前にあり TEXT 矩形の `BG_COVER`(90%)以上を覆う軸平行の RECTANGLE/FRAME/COMPONENT/INSTANCE の最前面(なければフレーム fill)。WCAG 相対輝度で比 | 比 < しきい値 | — | 前景が SOLID/不透明でない、背景未検出、背景が IMAGE/GRADIENT/半透明、背景と TEXT の間に TEXT 矩形の 50% 以上を覆う非矩形(VECTOR 等)・画像がある |
| P6 折り安全域 | 可視 TEXT(`P6_EXCLUDE_NAME` = ガイド:/装飾: を除く) | 折り線は絶対座標で計算し(180°回転でも対称)、設計座標に戻して**種別**を付ける。`P6_FOLD_KINDS[kind]`: 表紙 = 長辺 1/3(x=563.7)`spread`(見開き内)、2/3(x=1127.3)`boundary`(面境界)、短辺 1/2(y=1196)`boundary`。中面 = 3 本とも `spread`。横型フレームは軸を入れ替える | boundary をまたぐ、または余白 < `P6_MARGIN_MM.fail`(5mm=28px) | boundary の余白 < `P6_MARGIN_MM.warn`(8mm=46px)、spread をまたぐ(余白は見ない) | — |
| P7 仮置き文言 | 可視 TEXT の characters(`P7_EXCLUDE_NAME` = `サンプル:` を除く) | `P7_PATTERN`(`[〇○◯]{2,}`、`〇`+年/月/日/時/号/地区/市/町/村、`0000`、`(仮)`、ダミー、サンプル、XXX、TODO) | 一致あり | — | — |
| P12 電話番号 | 役割 phone で characters に電話番号らしい数字列を含む TEXT。`SHEETS[SHEET].p12 === false`(A4_spot)なら検査せず Pass(message `対象外(A4_spot)`) | **最大の**電話番号の fontSize ÷ 本文(役割 body)セグメントの fontSize 中央値 = 倍率 | 倍率 < `PHONE_RATIO.fail`(2.0) | 倍率 < `PHONE_RATIO.warn`(3.0) | 電話番号が無い、本文が無い |

共通: `visible === false` の枝と名前 `#tone` `#state` `#config` は走査から除く。characters が空の TEXT は P2/P3-a/P4/P6/P12 の対象外。幾何は absoluteBoundingBox。`frame.rotation` は absoluteTransform から求めた絶対回転(0〜359)。`frame.kind` `frame.family` も出力する。

## 4. 役割判定(NAME_MAP)

判定順: (1) 名前の接頭辞 `ROLE_PREFIX`(`#本文` `#注記` `#見出し` `#電話` `#CTA`。`ROLE_PREFIX_EXCEPT` の `#電話` + 受付/時間/注記/説明 は除く)→ (2) 名前の正規表現 `ROLE_NAME`(note → **label**(`ラベル:` / TEL / LINE / FAX / ℡)→ phone(`電話番号`)→ heading → body)→ (3) characters の正規表現 `ROLE_CHARS`(電話番号の数字列 → phone、TEL/LINE/FAX/QR/℡ だけ → label、先頭 `※＊*` → note、30 字以上 → body)→ (4) `other`。
役割は 6 種: body / note / heading / phone / **label**(短いラベル。P4 は 4.5:1、白抜きは 9pt Fail/12pt Warn)/ other。**数字列を含むものだけが phone**(7:1)。出力の `role` は `役割/根拠`(prefix / name / chars / default)。

## 5. 実行手順

1. Figma の `figma-use` スキルを読む(use_figma の前に必ず)
2. `skill/scripts/preflight.js` をそのまま `use_figma` の `code` に貼り、先頭 `CONFIG` の `PAGE_ID` / `FRAME_IDS` / `SHEET` だけ書き換える(必要なら `FRAME_KIND` `FAMILY` を明示)
   - 制作物 `'7:2'`、テスト `'664:2'`。**表紙は 1 枚 / 呼び出し、中面は 2 枚まで**(返り値の上限 20KB は UTF-8 バイト換算。超えると items を 5 → 2 → 0 件に段階的に切り詰め、`note` を付ける。件数 fail/warn/manual は残る)
   - **スキル(SKILL.md Step 4)からの渡し方**: `SHEET` = 冊子 `'A3_booklet'` / 乗降スポット表 `'A4_spot'`、`FRAME_KIND` = 表紙 `'cover'` / 中面 `'inner'`、`FAMILY` = 系統選択から(あいとま系 `'aitoma'` / 那智勝浦系 `'nachikatsuura'` / 登別系 `'noboribetsu'` / MITT 系 `'MITT'`。系統別しきい値 `PT_BY_FAMILY` があるのは現在 MITT だけ)
3. しきい値を変えるときも CONFIG だけを触る(`PT` `PT_BY_FAMILY` `CONTRAST` `P6_FOLD_KINDS` `P6_MARGIN_MM` `PHONE_RATIO` `TIGHT_BOX` など)
4. 複数ページ・多数フレームは呼び出しを分けて同じメッセージで並列に投げる(ページ切替は 1 呼び出し 1 回)
5. 実行後 `tmpRemovedAtEnd` が 0 であることを確認する(P3-a の一時 clone が残っていない証拠)
6. 念のためページ全体で `page.findAllWithCriteria({types:['TEXT']}).filter(n => n.name === '__preflight_tmp__')` が 0 件であることを見る

注意: 転送経路で ` ` のような正規表現リテラルは実文字に化けて構文エラーになる。スクリプトでは `String.fromCharCode(8232)` で組んでいる。

## 6. 出力の読み方

```json
{ "page": "制作物", "sheet": "A3_booklet",
  "results": [ { "frame": { "id", "name", "w", "h", "k", "rotation", "sheet", "kind": "cover|inner", "family": "MITT|null", "texts", "roles": {"body": 9, "label": 3, ...} },
                 "checks": [ { "id": "P6", "status": "Fail", "count": 21, "fail": 4, "warn": 17, "manual": 0,
                               "items": [ { "node", "name", "sev": "Fail|Warn|Manual", "role", "value", "limit", "chars", "fix", "at"? } ], "truncated"?: 1, "message"? } ],
                 "summary": { "fail": 5, "warn": 1, "manual": 0, "pass": 1, "error": 0, "ignored_tight": 5 } } ],
  "tmpRemovedAtEnd": 0, "ms": 509, "bytes": 10537, "note"? }
```

- `items` は Fail / Warn / Manual のみ、1 チェック最大 20 件(`truncated` は溢れた件数)。`name` は先頭 20 字、`chars` は先頭 15 字
- P6 の `value` は `x=1127.3面境界(gap 18.7)` `x=563.7見開き(またぎ)` のように折り線の設計座標・種別・状態を示す。`at` は TEXT の設計座標(x,y w×h)
- P12 の `value` は `50px = 本文×2.8`、`limit` に Fail 線(×2)と目標(×3)の px を併記
- **○/✗/△ 要約の作り方**(オペレータ向け、チェックごとに 1 行):
  - Pass → `○ 文字サイズ: 問題なし`
  - Fail → `✗ 文字サイズ: 19 か所(例: 「リード文」21px → 24px 以上に)`。例は sev=Fail の items[0] の name と fix
  - Warn → `△ 折り線: 17 か所は次回改善(入稿は可)`。Fail と Warn が混在するチェックは `✗ … 4 か所 / △ 17 か所` と併記
  - Manual → `△ コントラスト: 11 か所は目で確認(背景が絵柄のため)`
  - Error → `? 文字あふれ: 検査できませんでした(次回に再実行)`
  - P1 の Fail はそれ以外を読まずに「寸法が違うので複製からやり直し」を先に出す。`ignored_tight` は要約に出さない

## 7. 既知の限界(2026-09-27 時点)

- P4 は単色の矩形背景だけ計算する。テンプレの「背景」グループにある波形 VECTOR が TEXT の下にあると Manual になる(現行表紙で対象の 1/3〜2/3)。B.1 で文字に座布団(矩形)を敷けば計算できる
- P4 は `other` 役割(バッジ・無名テキスト・数字)を見ない
- P6 の種別は `FRAME_KIND`(名前判定)に依存する。名前に 表紙/中面 が無いフレームは `cover` 扱い。面グループ幅からの自動判定は B.1 の命名確定後
- P6 は見開き内の折りをまたぐ文字を Warn にとどめる(現行テンプレの 2 面見開き設計を第1段で許容)。第2段でサービス紹介面を組み直すかを判断
- P3-a は Figma がテキストを clip しない前提で「行が増えた/半行以上足りない」だけを見る。隣接要素との重なりは見ない(P3-b 予定)。`hasMissingFont` の TEXT は計測できない(Manual)
- P12 は最大の電話番号だけを評価する。本文が無名の中面では中央値が取れず Manual
- P2 の白抜き判定は fill の輝度 ≥ 0.85 で、淡黄色なども白扱い
- 系統(FAMILY)は名前で推定する。案件フレーム(`くらぶち_表紙_…`)の名前には系統名が無いので、スキルは `#tone` の `meta.template_family` から `CONFIG.FAMILY` を明示する(§5-2)
- 無名 TEXT の役割は characters(※ / 電話番号 / 短いラベル / 30 字以上)からの推定に頼る
- ラッパー寸法(1725.2×2426.2 / 858.9×1207.9)と PDF 実寸は次版(P1 の残り)
- A4_spot は 2026-09-27 に原本 28:178 の一時 clone で実測済み。P12 は対象外にした(2026-09-27 D で再実行し `対象外(A4_spot)` の Pass を確認)
- `frame.findAll` ではなく自前の再帰で 1 回だけ走査している(非表示の枝を丸ごと飛ばすため)

## 8. スクリプト全文(逐語)

以下は `skill/scripts/preflight.js` と同一。差分が出たらファイル側を正とする(2026-09-27 D で A4_spot の P12 対象外を追加)。

```js
// preflight.js — 第1層チェック(最小版: P1・P2・P3-a・P4単色・P6・P7・P12)
// use_figma にそのまま貼る素の JavaScript(トップレベル await + return)。
// 仕様: skill/references/preflight.md。しきい値は k(px/mm)から毎回計算する。
// 書き込みは P3-a の一時 clone のみ(try/finally で必ず remove)。
// ステータスは Pass / Fail / Warn / Manual / Error。Warn = 第2段の目標値に未達(入稿は止めない)。

const CONFIG = {
  PAGE_ID: '7:2',                    // 対象ページ(1呼び出しで切替は1回)
  FRAME_IDS: ['71:2'],               // 対象フレーム(表紙1枚なら1件、中面なら2枚まで)
  SHEET: 'A3_booklet',               // 'A3_booklet'(1691×2392 / 2392×1691) | 'A4_spot'(794×1123)
  SHEETS: {
    A3_booklet: { dims: [[1691, 2392], [2392, 1691]], shortMm: 297, folds: true,  p12: true },
    A4_spot:    { dims: [[794, 1123], [1123, 794]],   shortMm: 210, folds: false, p12: false },   // 乗降スポット表は本文=スポット名(40pt)で電話倍率の規則が合わないため P12 対象外
  },
  FRAME_KIND: 'auto',                // 'auto'(名前で判定) | 'cover'(表紙) | 'inner'(中面)。P6 の折り線種別に使う
  FRAME_KIND_PATTERNS: { cover: /表紙/, inner: /中面/ }, FRAME_KIND_DEFAULT: 'cover',
  FAMILY: 'auto',                    // 'auto'(名前で判定) | 'MITT' | ... 系統別しきい値 PT_BY_FAMILY に使う
  FAMILY_PATTERNS: { MITT: /MITT|ミット/i },
  // P2(pt)。{fail, warn}: fail 未満で Fail、warn 未満で Warn(warn 省略可)
  PT: {
    body: { fail: 12 }, note: { fail: 9, warn: 10 }, absMin: { fail: 6 },
    white: { body: { fail: 12 }, note: { fail: 12 }, phone: { fail: 12 }, heading: { fail: 9, warn: 12 }, label: { fail: 9, warn: 12 }, other: { fail: 9, warn: 12 } },
  },
  PT_BY_FAMILY: { MITT: { body: { fail: 7.5, warn: 12 } } },   // 系統別オーバーライド(第2段でテンプレを直すまでの暫定)
  WHITE_LUM: 0.85,                   // 白抜き = fill の相対輝度がこれ以上
  CONTRAST: { body: 7, note: 7, phone: 7, heading: 4.5, label: 4.5, other: null }, // P4(null=対象外)
  BG_COVER: 0.9,                     // P4 背景候補は TEXT 矩形の 90% 以上を覆う
  // P6 折り線の種別。boundary=面境界(またぐ→Fail、余白<fail mm→Fail、<warn mm→Warn)、spread=見開き内(またぐ→Warn、余白は見ない)
  // third1/third2 = 長辺方向の 1/3・2/3 の折り(設計座標で小さい方が third1)、half = 短辺方向の 1/2 の折り
  P6_FOLD_KINDS: { cover: { third1: 'spread', third2: 'boundary', half: 'boundary' }, inner: { third1: 'spread', third2: 'spread', half: 'spread' } },
  P6_MARGIN_MM: { fail: 5, warn: 8 },
  P6_SKIP_FOLDS: { x: [], y: [] },   // 検査しない折り線(設計座標px)
  P6_EXCLUDE_NAME: /^(ガイド:|装飾:)/,          // P6 で無視する TEXT 名
  OVERFLOW_TOL_PX: 1,                // P3-a 高さ差の許容
  TIGHT_BOX: 'ignore',               // P3-a 箱が文字より低いが不足が 1行×TIGHT_RATIO 未満(単行バッジ等): 'ignore'|'manual'|'fail'
  TIGHT_RATIO: 0.5,                  // 不足 ≥ 1行高×0.5 なら明示改行の追加でもあふれと判定
  PHONE_RATIO: { fail: 2.0, warn: 3.0 }, // P12 最大の電話番号 ≥ 本文中央値 × 倍率
  P7_PATTERN: /[〇○◯]{2,}|[〇○◯](?=年|月|日|時|号|地区|市|町|村)|0000|[（(]仮[)）]|ダミー|サンプル|XXX|TODO/,
  P7_EXCLUDE_NAME: /^サンプル:/,                 // テンプレの見本文言は除外
  EXCLUDE_NAME: /^#(tone|state|config)$/,      // 状態保持ノードは走査から除外
  // 役割判定: 名前の接頭辞 > 名前の正規表現 > 文字列の正規表現 > other
  ROLE_PREFIX: { '#本文': 'body', '#注記': 'note', '#見出し': 'heading', '#電話': 'phone', '#CTA': 'heading' },
  ROLE_PREFIX_EXCEPT: { '#電話': /受付|時間|注記|説明/ },   // 「#電話受付時間」は phone でなく名前規則へ
  ROLE_NAME: [
    ['note',    /注記|注意|受付時間|補助金表記|発行者情報|事業主体|運行事業者|協力会社|実施主体|更新\)|^※|※/],
    ['label',   /^ラベル:|^(TEL|LINE|FAX|℡)[.:：]?$/i],     // 短いラベル(TEL/LINE 等)は見出し相当 4.5:1
    ['phone',   /電話番号/],
    ['heading', /見出し|キャッチコピー|サブコピー|サービス名|タイトル|自治体名|事業名|^見出し:|分類\d/],
    ['body',    /本文|リード文|名称|停留所名|スポット名|乗降場所\d|リスト|説明|キャプション|手順/],
  ],
  ROLE_CHARS: [
    ['phone', /0\d{1,4}[-‐−ー–]\d{1,4}[-‐−ー–]\d{3,4}/],   // 数字列だけを phone
    ['label', /^(TEL|LINE|FAX|QR|℡)[.:：]?$/i],
    ['note',  /^[※＊*]/],
    ['body',  /^[\s\S]{30,}$/],                          // 無名ノードでも 30 字以上なら本文扱い
  ],
  MAX_ITEMS: 20, NAME_LEN: 20, CHARS_LEN: 15, OUT_LIMIT_BYTES: 19000,   // MCP の返り値上限 20KB は UTF-8 バイト換算(日本語は 3 バイト)
  TMP_NAME: '__preflight_tmp__',
};

// ---------- 共通ユーティリティ ----------
const t0 = Date.now();
const LINE_BREAK = new RegExp('\\r?\\n|' + String.fromCharCode(8232)); // 改行と U+2028(リテラルで書くと転送時に壊れる)
const round1 = v => Math.round(v * 10) / 10;
const cut = (s, n) => (s || '').replace(/\s+/g, ' ').slice(0, n);
const lum = c => { const f = v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
const contrast = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const absDeg = n => { const m = n.absoluteTransform; return ((Math.round(Math.atan2(m[1][0], m[0][0]) * 180 / Math.PI) % 360) + 360) % 360; };
const isAxisAligned = n => { const d = ((absDeg(n) % 90) + 90) % 90; return d < 0.5 || d > 89.5; };
const inter = (a, b) => { const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x); const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y); return (w > 0 && h > 0) ? w * h : 0; };
// 絶対座標 → フレームの設計座標(回転を打ち消す)
const toLocal = (frame, px, py) => { const [[a, c, e], [b, d, f]] = frame.absoluteTransform; const det = a * d - b * c; return { x: round1((d * (px - e) - c * (py - f)) / det), y: round1((-b * (px - e) + a * (py - f)) / det) }; };
const topFill = n => { const fs = Array.isArray(n.fills) ? n.fills : null; if (!fs) return undefined; for (let i = fs.length - 1; i >= 0; i--) if (fs[i].visible !== false) return fs[i]; return null; };
const SEV = { Fail: 3, Warn: 2, Manual: 1 };
const detect = (name, patterns, fallback) => { for (const k in patterns) if (patterns[k].test(name)) return k; return fallback; };

function roleOf(node) {
  const name = node.name || '';
  for (const p in CONFIG.ROLE_PREFIX) if (name.startsWith(p) && !(CONFIG.ROLE_PREFIX_EXCEPT[p] && CONFIG.ROLE_PREFIX_EXCEPT[p].test(name))) return { role: CONFIG.ROLE_PREFIX[p], by: 'prefix' };
  for (const [r, re] of CONFIG.ROLE_NAME) if (re.test(name)) return { role: r, by: 'name' };
  for (const [r, re] of CONFIG.ROLE_CHARS) if (re.test(node.characters || '')) return { role: r, by: 'chars' };
  return { role: 'other', by: 'default' };
}

// 1回だけ走査(DFS 前順 = 描画順)。visible=false の枝と除外名は捨てる
function walk(root) {
  const all = [];
  const rec = (n, depth) => {
    if (n.visible === false || CONFIG.EXCLUDE_NAME.test(n.name || '')) return;
    all.push({ node: n, idx: all.length, depth });
    if ('children' in n) for (const c of n.children) rec(c, depth + 1);
  };
  for (const c of root.children) rec(c, 1);
  return all;
}

// item: sev は 'Fail' | 'Warn' | 'Manual'
function item(n, sev, extra) { return Object.assign({ node: n ? n.id : null, name: n ? cut(n.name, CONFIG.NAME_LEN) : '-', sev }, extra); }
function finish(id, items, message) {
  const c = { Fail: 0, Warn: 0, Manual: 0 }; for (const i of items) c[i.sev]++;
  const check = { id, status: c.Fail ? 'Fail' : c.Warn ? 'Warn' : c.Manual ? 'Manual' : 'Pass', count: items.length, fail: c.Fail, warn: c.Warn, manual: c.Manual, items: items.slice(0, CONFIG.MAX_ITEMS) };
  if (items.length > CONFIG.MAX_ITEMS) check.truncated = items.length - CONFIG.MAX_ITEMS;
  if (message) check.message = message;
  return check;
}
const errCheck = (id, err) => ({ id, status: 'Error', count: 0, items: [], message: String(err) });

// ---------- 1フレーム分の検査 ----------
async function inspect(frame) {
  const sheet = CONFIG.SHEETS[CONFIG.SHEET];
  const w = frame.width, h = frame.height;
  const dimOk = sheet.dims.some(([a, b]) => Math.abs(w - a) < 0.01 && Math.abs(h - b) < 0.01);
  const k = (dimOk ? Math.min(w, h) : Math.min(...sheet.dims[0])) / sheet.shortMm; // px/mm
  const ptPx = pt => Math.round(pt * k * 25.4 / 72);   // 12pt→24px, 10pt→20px, 9pt→18px, 6pt→12px
  const mmPx = mm => Math.round(mm * k);              // 5mm→28px, 8mm→46px
  const fbb = frame.absoluteBoundingBox;
  const kind = CONFIG.FRAME_KIND === 'auto' ? detect(frame.name, CONFIG.FRAME_KIND_PATTERNS, CONFIG.FRAME_KIND_DEFAULT) : CONFIG.FRAME_KIND;
  const family = CONFIG.FAMILY === 'auto' ? detect(frame.name, CONFIG.FAMILY_PATTERNS, null) : CONFIG.FAMILY;
  const PT = Object.assign({}, CONFIG.PT, (family && CONFIG.PT_BY_FAMILY[family]) || {});
  const out = { frame: { id: frame.id, name: cut(frame.name, 40), w: round1(w), h: round1(h), k: round1(k * 100) / 100, rotation: absDeg(frame), sheet: CONFIG.SHEET, kind, family }, checks: [], summary: {} };
  const checks = out.checks;
  let ignoredTight = 0;

  // P1 作業寸法
  checks.push(finish('P1', dimOk ? [] : [item(frame, 'Fail', { value: `${round1(w)}×${round1(h)}`, limit: sheet.dims.map(d => d.join('×')).join(' / '), fix: '複製をやり直す(resize 不可)' })]));

  // 走査(1回)
  const all = walk(frame);
  const texts = all.filter(e => e.node.type === 'TEXT');
  const meta = new Map(); // text id → {role, by, segs, bbox}
  for (const e of texts) {
    const n = e.node;
    let segs = [];
    try { segs = n.getStyledTextSegments(['fontSize', 'fills', 'fontName']); } catch (err) { segs = [{ characters: n.characters, fontSize: n.fontSize, fills: n.fills, fontName: n.fontName }]; }
    meta.set(n.id, Object.assign(roleOf(n), { segs, bbox: n.absoluteBoundingBox, empty: !(n.characters || '').trim() }));
  }
  const liveTexts = texts.filter(e => !meta.get(e.node.id).empty && meta.get(e.node.id).bbox);
  out.frame.texts = texts.length;
  out.frame.roles = liveTexts.reduce((a, e) => { const r = meta.get(e.node.id).role; a[r] = (a[r] || 0) + 1; return a; }, {});

  // P2 文字サイズ(セグメント単位、Fail/Warn の2段)
  try {
    const items = [];
    const judge = (px, th) => !th ? null : px < ptPx(th.fail) ? 'Fail' : (th.warn && px < ptPx(th.warn)) ? 'Warn' : null;
    const lim = th => th ? `${ptPx(th.fail)}px${th.warn ? '/' + ptPx(th.warn) + 'px' : ''}` : '';
    for (const e of liveTexts) {
      const m = meta.get(e.node.id); const seen = new Set();
      for (const s of m.segs) {
        if (!(s.characters || '').trim()) continue;
        const px = s.fontSize; const f = Array.isArray(s.fills) && s.fills.length ? s.fills[s.fills.length - 1] : null;
        const white = f && f.type === 'SOLID' && lum(f.color) >= CONFIG.WHITE_LUM;
        const rules = [['abs', PT.absMin], [m.role, PT[m.role]], white ? ['white/' + m.role, PT.white[m.role] || PT.white.other] : null].filter(r => r && r[1]);
        let worst = null;
        for (const [why, th] of rules) { const sev = judge(px, th); if (sev && (!worst || SEV[sev] > SEV[worst.sev])) worst = { sev, why, th }; }
        if (!worst) continue;
        const key = px + worst.why + worst.sev; if (seen.has(key)) continue; seen.add(key);
        items.push(item(e.node, worst.sev, { role: m.role + '/' + m.by, value: `${round1(px)}px=${round1(px / k / 25.4 * 72)}pt`, limit: `${lim(worst.th)}(${worst.why})`, chars: cut(s.characters, CONFIG.CHARS_LEN), fix: `fontSize を ${ptPx(worst.th.fail)}px 以上に(文言を短くして収める)` }));
      }
    }
    checks.push(finish('P2', items, `limits px(fail/warn): body ${lim(PT.body)} / note ${lim(PT.note)} / abs ${lim(PT.absMin)} / white heading ${lim(PT.white.heading)}${family ? ' / family ' + family : ''}`));
  } catch (err) { checks.push(errCheck('P2', err)); }

  // P3-a 文字あふれ(textAutoResize NONE のみ。clone → HEIGHT → WIDTH_AND_HEIGHT → 高さ比較 → finally remove)
  try {
    const items = []; let checked = 0, tight = 0;
    const targets = liveTexts.filter(e => e.node.textAutoResize === 'NONE');
    const fontKeys = new Map();
    for (const e of targets) if (!e.node.hasMissingFont) for (const s of meta.get(e.node.id).segs) if (s.fontName) fontKeys.set(s.fontName.family + '|' + s.fontName.style, s.fontName);
    const failedFonts = new Set();
    for (const [key, fn] of fontKeys) { try { await figma.loadFontAsync(fn); } catch (err) { failedFonts.add(key); } }
    for (const e of targets) {
      const n = e.node, m = meta.get(n.id);
      if (n.hasMissingFont) { items.push(item(n, 'Manual', { role: m.role, value: 'hasMissingFont', fix: 'フォントを入れて再実行、または目視' })); continue; }
      if (m.segs.some(s => s.fontName && failedFonts.has(s.fontName.family + '|' + s.fontName.style))) { items.push(item(n, 'Manual', { role: m.role, value: 'font load failed', fix: '目視' })); continue; }
      let c = null;
      try {
        c = n.clone(); c.name = CONFIG.TMP_NAME; c.visible = false;
        c.textAutoResize = 'HEIGHT'; const hFit = c.height;             // 箱幅で折り返した高さ(必ず先。順を逆にすると幅が自然幅に変わる)
        c.textAutoResize = 'WIDTH_AND_HEIGHT'; const hNat = c.height;   // 自然高さ(明示改行のみ、幅は自然幅)
        checked++;
        const diff = hFit - n.height;
        if (diff > CONFIG.OVERFLOW_TOL_PX) {
          const lineH = hNat / ((n.characters || '').split(LINE_BREAK).length || 1); // 1行の高さ(明示改行で割る)
          const wrapped = hFit > hNat + 1 || diff >= lineH * CONFIG.TIGHT_RATIO;          // 折り返し増、または不足が半行以上
          if (wrapped || CONFIG.TIGHT_BOX === 'fail') items.push(item(n, 'Fail', { role: m.role, value: `${wrapped ? 'あふれ' : 'tight'} need ${round1(hFit)}px / box ${round1(n.height)}px (+${round1(diff)}, line ${round1(lineH)})`, limit: `+${CONFIG.OVERFLOW_TOL_PX}px`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '文言を短くする(箱・フォントは変えない)' }));
          else if (CONFIG.TIGHT_BOX === 'manual') items.push(item(n, 'Manual', { role: m.role, value: `tight box ${round1(n.height)}px < text ${round1(hFit)}px`, fix: '目視(折り返しは増えていない)' }));
          else tight++;
        }
      } catch (err) { items.push(item(n, 'Manual', { role: m.role, value: 'clone error: ' + String(err).slice(0, 60), fix: '目視' }));
      } finally { if (c) { try { c.remove(); } catch (e2) {} } }
    }
    ignoredTight = tight;
    checks.push(finish('P3-a', items, `NONE ${targets.length} 件中 ${checked} 件を計測、tight(折返し増なし) ${tight} 件は ${CONFIG.TIGHT_BOX}`));
  } catch (err) { checks.push(errCheck('P3-a', err)); }

  // P4 コントラスト(単色背景のみ)
  try {
    const items = []; let skipped = 0;
    const rectTypes = new Set(['RECTANGLE', 'FRAME', 'COMPONENT', 'INSTANCE']);
    const shapeTypes = new Set(['VECTOR', 'BOOLEAN_OPERATION', 'ELLIPSE', 'POLYGON', 'STAR', 'LINE']);
    const cands = []; // 背景候補・要注意シェイプ
    for (const e of all) {
      const n = e.node; const bb = n.absoluteBoundingBox; if (!bb || n.type === 'TEXT') continue;
      const tf = topFill(n); if (!tf) continue; // fills なし/全非表示
      const rect = rectTypes.has(n.type) && isAxisAligned(n);
      cands.push({ idx: e.idx, bb, fill: tf, opacity: n.opacity == null ? 1 : n.opacity, rect, shape: !rect && (shapeTypes.has(n.type) || rectTypes.has(n.type)), name: n.name });
    }
    const rootFill = topFill(frame);
    for (const e of liveTexts) {
      const n = e.node, m = meta.get(n.id);
      const need = CONFIG.CONTRAST[m.role]; if (!need) { skipped++; continue; }
      const tb = m.bbox, ta = tb.width * tb.height; if (!ta) continue;
      // 前景色(セグメント fill。可視 SOLID stroke があればそれを優先=袋文字)
      const strokes = (n.strokes || []).filter(s => s.visible !== false);
      let fgs = [];
      if (strokes.length && n.strokeWeight > 0) { const s = strokes[strokes.length - 1]; fgs = [s.type === 'SOLID' && (s.opacity == null || s.opacity >= 0.99) ? s.color : null]; }
      else for (const s of m.segs) { if (!(s.characters || '').trim()) continue; const f = Array.isArray(s.fills) && s.fills.length ? s.fills[s.fills.length - 1] : null; fgs.push(f && f.type === 'SOLID' && (f.opacity == null || f.opacity >= 0.99) ? f.color : null); }
      if ((n.opacity != null && n.opacity < 0.99) || fgs.some(c => !c)) { items.push(item(n, 'Manual', { role: m.role, value: '文字色が SOLID/不透明でない', fix: '目視' })); continue; }
      // 背景=TEXT 矩形を 90% 以上覆う、手前側の最上位。root フレームは最背面候補
      let bg = rootFill ? { idx: -1, fill: rootFill, opacity: frame.opacity == null ? 1 : frame.opacity, rect: true, name: '(frame)' } : null;
      for (const c of cands) if (c.idx < e.idx && c.rect && inter(c.bb, tb) / ta >= CONFIG.BG_COVER) bg = c;
      if (!bg) { items.push(item(n, 'Manual', { role: m.role, value: '背景未検出', fix: '目視' })); continue; }
      const between = cands.find(c => c.idx > bg.idx && c.idx < e.idx && (c.shape || c.fill.type !== 'SOLID') && inter(c.bb, tb) / ta >= 0.5);
      if (between) { items.push(item(n, 'Manual', { role: m.role, value: `背景に非矩形/画像 ${cut(between.name, 12)}`, fix: '目視' })); continue; }
      const semi = bg.opacity < 0.99 || (bg.fill.opacity != null && bg.fill.opacity < 0.99);
      if (bg.fill.type !== 'SOLID' || semi) { items.push(item(n, 'Manual', { role: m.role, value: `背景 ${bg.fill.type}${semi ? '(半透明)' : ''} ${cut(bg.name, 12)}`, fix: '目視' })); continue; }
      let worst = Infinity, worstFg = null;
      for (const c of new Set(fgs.map(hex))) { const col = fgs.find(x => hex(x) === c); const r = contrast(col, bg.fill.color); if (r < worst) { worst = r; worstFg = col; } }
      if (worst < need) items.push(item(n, 'Fail', { role: m.role + '/' + m.by, value: `${round1(worst)}:1 ${hex(worstFg)} on ${hex(bg.fill.color)} (${cut(bg.name, 12)})`, limit: `${need}:1`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '文字色を濃く/背景を淡く' }));
    }
    checks.push(finish('P4', items, `対象 ${liveTexts.length - skipped} 件(other ${skipped} 件は対象外)`));
  } catch (err) { checks.push(errCheck('P4', err)); }

  // P6 折り安全域(折り線の種別: boundary=面境界 / spread=見開き内)
  try {
    if (!sheet.folds || !fbb) checks.push(finish('P6', [], '折り線なしのシート'));
    else {
      const items = [];
      const mFail = mmPx(CONFIG.P6_MARGIN_MM.fail), mWarn = mmPx(CONFIG.P6_MARGIN_MM.warn);
      const portrait = fbb.height >= fbb.width;
      const kinds = CONFIG.P6_FOLD_KINDS[kind] || CONFIG.P6_FOLD_KINDS.cover;
      // 折り線は絶対座標で計算(180°回転でも 1/3・2/3・1/2 は対称)。種別・表示・除外は設計座標
      const lx = ax => toLocal(frame, ax, fbb.y + fbb.height / 2).x, ly = ay => toLocal(frame, fbb.x + fbb.width / 2, ay).y;
      const skip = (v, arr) => arr.some(s => Math.abs(s - v) < 1);
      const thirds = (len, off) => [off + len / 3, off + len * 2 / 3];
      const folds = []; // {axis:'x'|'y', abs, local, kind}
      const longLen = portrait ? h : w;
      for (const ax of (portrait ? thirds(fbb.width, fbb.x) : [fbb.x + fbb.width / 2])) { const l = lx(ax); if (skip(l, CONFIG.P6_SKIP_FOLDS.x)) continue; folds.push({ axis: 'x', abs: ax, local: l, kind: portrait ? kinds[l < w / 2 ? 'third1' : 'third2'] : kinds.half }); }
      for (const ay of (portrait ? [fbb.y + fbb.height / 2] : thirds(fbb.height, fbb.y))) { const l = ly(ay); if (skip(l, CONFIG.P6_SKIP_FOLDS.y)) continue; folds.push({ axis: 'y', abs: ay, local: l, kind: portrait ? kinds.half : kinds[l < longLen / 2 ? 'third1' : 'third2'] }); }
      for (const e of liveTexts) {
        const n = e.node; if (CONFIG.P6_EXCLUDE_NAME.test(n.name || '')) continue;
        const b = meta.get(n.id).bbox; const hits = []; let sev = null;
        for (const f of folds) {
          const lo = f.axis === 'x' ? b.x : b.y, hi = lo + (f.axis === 'x' ? b.width : b.height);
          const cross = f.abs > lo && f.abs < hi; const gap = cross ? 0 : Math.min(Math.abs(lo - f.abs), Math.abs(hi - f.abs));
          let s = null;
          if (f.kind === 'boundary') s = cross || gap < mFail ? 'Fail' : gap < mWarn ? 'Warn' : null;
          else if (cross) s = 'Warn';
          if (!s) continue;
          hits.push(`${f.axis}=${f.local}${f.kind === 'boundary' ? '面境界' : '見開き'}(${cross ? 'またぎ' : 'gap ' + round1(gap)})`);
          if (!sev || SEV[s] > SEV[sev]) sev = s;
        }
        if (hits.length) { const p = toLocal(frame, b.x, b.y), q = toLocal(frame, b.x + b.width, b.y + b.height); items.push(item(n, sev, { role: meta.get(n.id).role, value: hits.join(' '), limit: `面境界: またぎ/<${mFail}px Fail, <${mWarn}px Warn。見開き: またぎ Warn`, at: `${Math.min(p.x, q.x)},${Math.min(p.y, q.y)} ${round1(b.width)}×${round1(b.height)}`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: sev === 'Fail' ? '折り線から離す/文言を短くする' : '第2段で見開きの組み直しを検討(入稿は可)' })); }
      }
      checks.push(finish('P6', items, `kind ${kind}, folds(local): ${folds.map(f => f.axis + '=' + f.local + ':' + f.kind).join(' ')}`));
    }
  } catch (err) { checks.push(errCheck('P6', err)); }

  // P7 仮置き文言
  try {
    const items = [];
    for (const e of texts) {
      const n = e.node; if (CONFIG.P7_EXCLUDE_NAME.test(n.name || '')) continue;
      const mt = (n.characters || '').match(CONFIG.P7_PATTERN);
      if (mt) items.push(item(n, 'Fail', { role: meta.get(n.id).role, value: mt[0], chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '実内容に置換、使わないなら hidden に' }));
    }
    checks.push(finish('P7', items));
  } catch (err) { checks.push(errCheck('P7', err)); }

  // P12 電話番号(最大の電話番号が本文中央値×倍率以上か。fail/warn の2段)
  if (!sheet.p12) checks.push(finish('P12', [], `対象外(${CONFIG.SHEET})`));
  else try {
    const bodyPx = []; const phones = [];
    for (const e of liveTexts) {
      const m = meta.get(e.node.id);
      if (m.role === 'body') for (const s of m.segs) if ((s.characters || '').trim()) bodyPx.push(s.fontSize);
      if (m.role === 'phone' && CONFIG.ROLE_CHARS[0][1].test(e.node.characters || '')) phones.push({ n: e.node, px: Math.max(...m.segs.map(s => s.fontSize || 0)) });
    }
    if (!phones.length) checks.push(finish('P12', [item(null, 'Manual', { value: '電話番号らしい TEXT が見つからない(role phone + 数字列)' })]));
    else if (!bodyPx.length) checks.push(finish('P12', [item(null, 'Manual', { value: '本文(role body)が見つからず中央値が取れない' })]));
    else {
      bodyPx.sort((a, b) => a - b); const med = bodyPx[Math.floor(bodyPx.length / 2)];
      phones.sort((a, b) => b.px - a.px); const top = phones[0];
      const sev = top.px < med * CONFIG.PHONE_RATIO.fail ? 'Fail' : top.px < med * CONFIG.PHONE_RATIO.warn ? 'Warn' : null;
      const items = sev ? [item(top.n, sev, { role: 'phone', value: `${round1(top.px)}px = 本文×${round1(top.px / med)}`, limit: `≥×${CONFIG.PHONE_RATIO.fail}(${round1(med * CONFIG.PHONE_RATIO.fail)}px) Fail / ≥×${CONFIG.PHONE_RATIO.warn}(${round1(med * CONFIG.PHONE_RATIO.warn)}px) 目標`, chars: cut(top.n.characters, CONFIG.CHARS_LEN), fix: '電話番号を大きくする' })] : [];
      checks.push(finish('P12', items, `body median ${med}px, phones: ${phones.map(p => round1(p.px) + 'px').join('/')}`));
    }
  } catch (err) { checks.push(errCheck('P12', err)); }

  out.summary = checks.reduce((a, c) => { const key = c.status.toLowerCase(); a[key] = (a[key] || 0) + 1; return a; }, { fail: 0, warn: 0, manual: 0, pass: 0, error: 0 });
  out.summary.ignored_tight = ignoredTight;
  return out;
}

// ---------- 実行 ----------
const page = await figma.getNodeByIdAsync(CONFIG.PAGE_ID);
if (!page || page.type !== 'PAGE') return { error: `PAGE_ID ${CONFIG.PAGE_ID} がページではない` };
await figma.setCurrentPageAsync(page);
const results = [];
for (const id of CONFIG.FRAME_IDS) {
  const f = await figma.getNodeByIdAsync(id);
  if (!f || !('children' in f)) { results.push({ frame: { id }, error: 'not found / not a container' }); continue; }
  try { results.push(await inspect(f)); } catch (err) { results.push({ frame: { id, name: f.name }, error: String(err) }); }
}
// 一時 clone の残骸を掃く(通常 0 件)
let tmpLeft = 0;
for (const id of CONFIG.FRAME_IDS) { const f = await figma.getNodeByIdAsync(id); if (f && 'findAllWithCriteria' in f) for (const n of f.findAllWithCriteria({ types: ['TEXT'] })) if (n.name === CONFIG.TMP_NAME) { tmpLeft++; n.remove(); } }
// UTF-8 バイト数(TextEncoder は使わない)
const utf8 = s => { let b = 0; for (let i = 0; i < s.length; i++) { const c = s.charCodeAt(i); b += c < 0x80 ? 1 : c < 0x800 ? 2 : (c >= 0xd800 && c <= 0xdfff) ? 2 : 3; } return b; };
let payload = { page: page.name, sheet: CONFIG.SHEET, results, tmpRemovedAtEnd: tmpLeft, ms: Date.now() - t0 };
let bytes = utf8(JSON.stringify(payload)); const before = bytes;
for (const keep of [5, 2, 0]) {   // 超えていれば items を 5 → 2 → 0 件に段階的に切り詰める(件数 fail/warn/manual は残る)
  if (bytes <= CONFIG.OUT_LIMIT_BYTES) break;
  for (const r of results) for (const c of (r.checks || [])) if (c.items && c.items.length > keep) { c.truncated = (c.truncated || 0) + c.items.length - keep; c.items = c.items.slice(0, keep); }
  payload.note = `出力が ${before} バイトで上限を超えたため items を ${keep} 件に切り詰めた。FRAME_IDS を分けて再実行すること`;
  bytes = utf8(JSON.stringify(payload));
}
payload.bytes = bytes;
return payload;
```
