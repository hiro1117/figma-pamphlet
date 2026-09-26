# preflight.js — 第1層チェック(最小版)仕様書

対象: `skill/scripts/preflight.js`(2026-09-26 版、最小版 = P1・P2・P3-a・P4単色・P6・P7・P12)。
計画書 v5.1 §6.5 の第1層のうち、機械判定できる 7 項目を `use_figma` 1 回で実行し、Pass / Fail / Manual を JSON で返す。オペレータには ○/✗ の要約だけを見せる(組み込みはスキル改訂 D で行う)。

## 1. 前提

- Figma は複製ファイル `09Js7rndbabLAoCchqzX9j` だけ。本番は触らない。テンプレート原本(ページ `テンプレート` 0:1)には走らせない(P3-a が一時 clone を書き込むため)
- 1 回の `use_figma` で扱うのは 1 ページ(`CONFIG.PAGE_ID`)。複数ページは呼び出しを分けて並列に投げる
- シート種別 `CONFIG.SHEET`
  - `A3_booklet`: 1691×2392 または 2392×1691。k = 短辺 px ÷ 297 = 5.694 px/mm。折り線は縦 2 本(1/3・2/3)+横 1 本(1/2)。横型は縦横を入れ替える
  - `A4_spot`: 794×1123(乗降スポット表)。k = 794 ÷ 210 = 3.781 px/mm。折り線なし
- **しきい値は毎回 k から計算する**(旧計画の 34px は使わない)。`ptPx(pt) = round(pt × k × 25.4 / 72)`、`mmPx(mm) = round(mm × k)`

| 量 | A3_booklet(k=5.694) | A4_spot(k=3.781) |
|---|---|---|
| 12pt(本文・白抜き) | 24px | 16px |
| 10pt(注記) | 20px | 13px |
| 6pt(絶対下限) | 12px | 8px |
| 8mm(折り安全域) | 46px | — |

## 2. チェック定義

| ID | 対象 | 判定 | Fail | Manual |
|---|---|---|---|---|
| P1 作業寸法 | フレームの width/height | `SHEETS[SHEET].dims` と ±0.01px で一致 | 不一致(rescale 不可、複製をやり直す) | — |
| P2 文字サイズ | 可視 TEXT の全セグメント(`getStyledTextSegments(['fontSize','fills','fontName'])`) | 役割 body ≥ `PT.body`、note ≥ `PT.note`、全セグメント ≥ `PT.absMin`、fill 輝度 ≥ `WHITE_LUM`(0.85)の白抜きは ≥ `PT.white`。同一ノードでは (px, 理由) が同じ違反を 1 件に畳む | いずれか未達 | — |
| P3-a 文字あふれ | `textAutoResize === 'NONE'` の可視 TEXT | 全フォントを `loadFontAsync` → `clone()`(名前 `__preflight_tmp__`、非表示)→ `textAutoResize='HEIGHT'` で箱幅の折返し高さ hFit → `'WIDTH_AND_HEIGHT'` で自然高さ hNat → **finally で `clone.remove()`**。`diff = hFit − 箱高` が `OVERFLOW_TOL_PX`(1px)を超え、かつ「hFit > hNat+1(折返しが増えた)」または「diff ≥ 1行高 × `TIGHT_RATIO`(0.5)」なら あふれ。それ以外の超過(単行バッジの箱が行高より低いだけ)は tight として `TIGHT_BOX`('ignore'/'manual'/'fail')に従う | あふれ | `hasMissingFont`、フォントロード失敗、clone 失敗 |
| P4 コントラスト(単色背景) | 役割 body/note/phone(7:1)・heading(4.5:1)。`CONTRAST.other = null` の役割は対象外 | 前景 = セグメント fill(可視 SOLID stroke があれば袋文字としてその色)。背景 = 走査順(描画順)で TEXT より手前にあり、TEXT 矩形の `BG_COVER`(90%)以上を覆う軸平行の RECTANGLE/FRAME/COMPONENT/INSTANCE のうち最前面(なければフレーム自身の fill)。WCAG 相対輝度で比 | 比 < しきい値 | 前景が SOLID/不透明でない、背景未検出、背景が IMAGE/GRADIENT/半透明、背景と TEXT の間に TEXT 矩形の 50% 以上を覆う非矩形(VECTOR 等)や画像がある |
| P6 折り安全域 | 可視 TEXT(`P6_EXCLUDE_NAME` = ガイド:/装飾: を除く) | 折り線は絶対座標で `absoluteBoundingBox` から計算(180°回転フレームでも 1/3・2/3・1/2 は対称)。TEXT の absoluteBoundingBox が折り線 ± `FOLD_MARGIN_MM`(8mm=46px)に入る、または折り線をまたぐ。表示・除外(`P6_SKIP_FOLDS`)は設計座標(回転を打ち消した px) | 該当あり | — |
| P7 仮置き文言 | 可視 TEXT の characters(`P7_EXCLUDE_NAME` = `サンプル:` で始まる名前を除く) | `P7_PATTERN` に一致(既定: `[〇○◯]{2,}`、`〇`+年/月/日/時/号/地区/市/町/村、`0000`、`(仮)`、ダミー、サンプル、XXX、TODO) | 一致あり | — |
| P12 電話番号 | 役割 phone で characters に電話番号らしい数字列(`0\d{1,4}-\d{1,4}-\d{3,4}`)を含む TEXT | **最大の**電話番号の fontSize ≥ 本文(役割 body)セグメントの fontSize 中央値 × `PHONE_RATIO`(3) | 未達 | 電話番号が見つからない、本文が見つからない |

共通: `visible === false` の枝と名前 `#tone` `#state` `#config` は走査から除く。characters が空の TEXT は P2/P3-a/P4/P6/P12 の対象外。幾何は absoluteBoundingBox。出力の `frame.rotation` は absoluteTransform から求めた絶対回転(0〜359)。

## 3. 役割判定(NAME_MAP)

判定順: (1) 名前の接頭辞 `ROLE_PREFIX`(`#本文` `#注記` `#見出し` `#電話` `#CTA`。ただし `ROLE_PREFIX_EXCEPT` の `#電話` + 受付/時間/注記/説明 は除く)→ (2) 名前の正規表現 `ROLE_NAME`(note → phone → heading → body の順)→ (3) characters の正規表現 `ROLE_CHARS`(電話番号の数字列 → phone、先頭 `※＊*` → note、30 字以上 → body)→ (4) `other`。
出力の `role` は `役割/根拠`(prefix / name / chars / default)。既定値は `docs/prep/text-inventory.md` の候補表から決めた(`#〜本文` `#リード文` `#〜名称` → body、`#〜注記` `#利用上の注意` `#受付時間` `#補助金表記` `#事業主体` → note、`#キャッチコピー` `#サービス名` `#タイトル` `見出し:` → heading、`#電話番号〜` `TEL` `℡` → phone)。

## 4. 実行手順

1. Figma の `figma-use` スキルを読む(use_figma の前に必ず)
2. `skill/scripts/preflight.js` をそのまま `use_figma` の `code` に貼り、先頭 `CONFIG` の 3 行だけ書き換える
   - `PAGE_ID`: 制作物 `'7:2'`、テスト `'664:2'`
   - `FRAME_IDS`: 検査するフレーム ID の配列。**表紙は 1 枚 / 呼び出し、中面は 2 枚まで**(返り値 20KB の目安。超えると自動で items を 5 件に切り詰め `note` を付ける)
   - `SHEET`: 冊子 `'A3_booklet'`、乗降スポット表 `'A4_spot'`
3. しきい値を変えるときも CONFIG だけを触る(`PT` `CONTRAST` `FOLD_MARGIN_MM` `PHONE_RATIO` `P6_SKIP_FOLDS` `TIGHT_BOX` など)
4. 複数ページ・多数フレームは呼び出しを分けて同じメッセージで並列に投げる(ページ切替は 1 呼び出し 1 回)
5. 実行後 `tmpRemovedAtEnd` が 0 であることを確認する(P3-a の一時 clone が残っていない証拠。0 以外なら掃き残しを消した件数)
6. ページ全体で確認したいときは読み取り専用で `page.findAllWithCriteria({types:['TEXT']}).filter(n => n.name === '__preflight_tmp__')` が 0 件であることを見る

注意: 転送経路で ` ` のような正規表現リテラルは実文字に化けて構文エラーになる。スクリプトでは `String.fromCharCode(8232)` で組んでいる。同種の追加をするときも同じ書き方にする。

## 5. 出力の読み方

```json
{ "page": "制作物", "sheet": "A3_booklet",
  "results": [ { "frame": { "id", "name", "w", "h", "k", "rotation", "sheet", "texts", "roles": {"body": 9, ...} },
                 "checks": [ { "id": "P2", "status": "Pass|Fail|Manual|Error", "count": 24,
                               "items": [ { "node", "name", "role", "value", "limit", "chars", "fix", "at"? } ], "truncated"?: 4, "message"? } ],
                 "summary": { "fail": 6, "manual": 0, "pass": 1 } } ],
  "tmpRemovedAtEnd": 0, "ms": 509, "bytes": 10537, "note"? }
```

- `items` は Fail / Manual のみ、1 チェック最大 20 件(`truncated` は溢れた件数)。`name` は先頭 20 字、`chars` は先頭 15 字
- `value` は実測、`limit` はしきい値、`fix` は直し方の一言。P6 の `at` は設計座標(x,y w×h)、`value` の `x=563.7(またぎ)` `y=1196(gap 27)` も設計座標
- `status` の決め方: Fail が 1 件でもあれば Fail、なければ Manual があれば Manual、どちらもなければ Pass。`Error` はそのチェックだけ失敗(他は続行)
- **○/✗ 要約の作り方**(オペレータ向け、チェックごとに 1 行):
  - Pass → `○ 文字サイズ: 問題なし`
  - Fail → `✗ 文字サイズ: 24 か所(例: 「リード文」21px → 24px 以上に)`。例は items[0] の name と fix を使う
  - Manual → `△ コントラスト: 10 か所は目で確認(背景が絵柄のため)`。message の要約を添える
  - Error → `? 文字あふれ: 検査できませんでした(次回に再実行)`
  - P1 の Fail はそれ以外を読まずに「寸法が違うので複製からやり直し」を先に出す

## 6. 既知の限界(2026-09-26 時点)

- P4 は単色の矩形背景だけ計算する。テンプレの「背景」グループにある波形 VECTOR が TEXT の下にあると Manual になる(現行テンプレの表紙ではほぼ全滅)。B.1 で文字に座布団(矩形)を敷けば計算できる
- P4 は `other` 役割(ラベル・バッジ・無名テキスト)を見ない。`ラベル:TEL` など名前に TEL を含むものは phone(7:1)で判定される
- P6 は現行テンプレの設計そのもの(2 面見開きの中央折りをまたぐ見出し・リード文、折りから 27〜45px の STEP バッジやフッター)と衝突して大量に Fail する。`P6_SKIP_FOLDS` と `FOLD_MARGIN_MM` で緩和できるが、既定値は仕様どおり厳格。詳細は `docs/reports/E-test-report.md`
- P3-a は Figma がテキストを clip しない前提で「行が増えた/半行以上足りない」だけを見る。tight(箱が行高より少し低い)は既定で無視。隣接要素との重なりは見ない(P3-b 予定)。`hasMissingFont` の TEXT は計測できない(Manual)
- P12 は最大の電話番号だけを評価する(フッターの小さい電話番号は message に一覧)。倍率 3 は現行テンプレの電話(43〜75px)では達成不能(本文 24px × 3 = 72px)
- P2 の白抜き判定は fill の輝度 ≥ 0.85 で、淡黄色なども白扱いになる
- 無名 TEXT の役割は characters(※ / 電話番号 / 30 字以上)からの推定に頼る。旧世代の複製(制作物ページの 2026-08 版)は無名が多い
- ラッパー寸法(1725.2×2426.2 / 858.9×1207.9)と PDF 実寸は次版(P1 の残り)
- `frame.findAll` ではなく自前の再帰で 1 回だけ走査している(非表示の枝を丸ごと飛ばすため)。走査回数は同じ

## 7. スクリプト全文(逐語)

以下は `skill/scripts/preflight.js` と同一。差分が出たらファイル側を正とする。

```js
// preflight.js — 第1層チェック(最小版: P1・P2・P3-a・P4単色・P6・P7・P12)
// use_figma にそのまま貼る素の JavaScript(トップレベル await + return)。
// 仕様: skill/references/preflight.md。しきい値は k(px/mm)から毎回計算する。
// 書き込みは P3-a の一時 clone のみ(try/finally で必ず remove)。

const CONFIG = {
  PAGE_ID: '7:2',                    // 対象ページ(1呼び出しで切替は1回)
  FRAME_IDS: ['71:2'],               // 対象フレーム(表紙1枚なら1件、中面なら2〜3件まで)
  SHEET: 'A3_booklet',               // 'A3_booklet'(1691×2392 / 2392×1691) | 'A4_spot'(794×1123)
  SHEETS: {
    A3_booklet: { dims: [[1691, 2392], [2392, 1691]], shortMm: 297, folds: true },
    A4_spot:    { dims: [[794, 1123], [1123, 794]],   shortMm: 210, folds: false },
  },
  PT: { body: 12, note: 10, absMin: 6, white: 12 },   // P2(pt)。白抜き=fill 輝度 ≥ WHITE_LUM
  WHITE_LUM: 0.85,
  CONTRAST: { body: 7, note: 7, phone: 7, heading: 4.5, other: null }, // P4(null=対象外)
  BG_COVER: 0.9,                     // P4 背景候補は TEXT 矩形の 90% 以上を覆う
  FOLD_MARGIN_MM: 8,                 // P6 折り線からの安全域(46px)
  OVERFLOW_TOL_PX: 1,                // P3-a 高さ差の許容
  TIGHT_BOX: 'ignore',               // P3-a 箱が文字より低いが不足が 1行×TIGHT_RATIO 未満(単行バッジ等): 'ignore'|'manual'|'fail'
  TIGHT_RATIO: 0.5,                  // 不足 ≥ 1行高×0.5 なら明示改行の追加でもあふれと判定
  P6_SKIP_FOLDS: { x: [], y: [] },   // P6 で検査しない折り線(設計座標px。例: 2面見開きの中央 x:[563.7])
  PHONE_RATIO: 3,                    // P12 電話 ≥ 本文中央値 × 3
  P6_EXCLUDE_NAME: /^(ガイド:|装飾:)/,          // P6 で無視する TEXT 名
  P7_PATTERN: /[〇○◯]{2,}|[〇○◯](?=年|月|日|時|号|地区|市|町|村)|0000|[（(]仮[)）]|ダミー|サンプル|XXX|TODO/,
  P7_EXCLUDE_NAME: /^サンプル:/,                 // テンプレの見本文言は除外
  EXCLUDE_NAME: /^#(tone|state|config)$/,      // 状態保持ノードは走査から除外
  // 役割判定: 名前が #本文 等で始まれば優先。次に名前の正規表現、最後に文字列
  ROLE_PREFIX: { '#本文': 'body', '#注記': 'note', '#見出し': 'heading', '#電話': 'phone', '#CTA': 'heading' },
  ROLE_PREFIX_EXCEPT: { '#電話': /受付|時間|注記|説明/ },   // 「#電話受付時間」は phone でなく名前規則へ
  ROLE_NAME: [
    ['note',    /注記|注意|受付時間|補助金表記|発行者情報|事業主体|運行事業者|協力会社|実施主体|更新\)|^※|※/],
    ['phone',   /電話番号|(^|[^a-zA-Z])TEL($|[^a-zA-Z])|℡/],
    ['heading', /見出し|キャッチコピー|サブコピー|サービス名|タイトル|自治体名|事業名|^見出し:|^ラベル:見出し|分類\d/],
    ['body',    /本文|リード文|名称|停留所名|スポット名|乗降場所\d|リスト|説明|キャプション|手順/],
  ],
  ROLE_CHARS: [
    ['phone', /0\d{1,4}[-‐−ー–]\d{1,4}[-‐−ー–]\d{3,4}/],
    ['note',  /^[※＊*]/],
    ['body',  /^[\s\S]{30,}$/],                   // 無名ノードでも 30 字以上なら本文扱い
  ],
  MAX_ITEMS: 20, NAME_LEN: 20, CHARS_LEN: 15, OUT_LIMIT: 20000,
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

function item(n, extra) { return Object.assign({ node: n.id, name: cut(n.name, CONFIG.NAME_LEN) }, extra); }
function finish(check, items, fails, manuals, message) {
  check.status = fails > 0 ? 'Fail' : manuals > 0 ? 'Manual' : 'Pass';
  check.count = fails + manuals;
  check.items = items.slice(0, CONFIG.MAX_ITEMS);
  if (items.length > CONFIG.MAX_ITEMS) check.truncated = items.length - CONFIG.MAX_ITEMS;
  if (message) check.message = message;
  return check;
}

// ---------- 1フレーム分の検査 ----------
async function inspect(frame) {
  const sheet = CONFIG.SHEETS[CONFIG.SHEET];
  const w = frame.width, h = frame.height;
  const dimOk = sheet.dims.some(([a, b]) => Math.abs(w - a) < 0.01 && Math.abs(h - b) < 0.01);
  const k = (dimOk ? Math.min(w, h) : Math.min(...sheet.dims[0])) / sheet.shortMm; // px/mm
  const ptPx = pt => Math.round(pt * k * 25.4 / 72);   // 12pt→24px, 10pt→20px, 6pt→12px
  const mmPx = mm => Math.round(mm * k);              // 8mm→46px
  const fbb = frame.absoluteBoundingBox;
  const out = { frame: { id: frame.id, name: cut(frame.name, 40), w: round1(w), h: round1(h), k: round1(k * 100) / 100, rotation: absDeg(frame), sheet: CONFIG.SHEET }, checks: [], summary: {} };
  const checks = out.checks;

  // P1 作業寸法
  checks.push({ id: 'P1', status: dimOk ? 'Pass' : 'Fail', count: dimOk ? 0 : 1,
    items: dimOk ? [] : [item(frame, { value: `${round1(w)}×${round1(h)}`, limit: sheet.dims.map(d => d.join('×')).join(' / '), fix: '複製をやり直す(resize 不可)' })] });

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

  // P2 文字サイズ(セグメント単位)
  try {
    const items = []; let fails = 0;
    const lim = { body: ptPx(CONFIG.PT.body), note: ptPx(CONFIG.PT.note), abs: ptPx(CONFIG.PT.absMin), white: ptPx(CONFIG.PT.white) };
    for (const e of liveTexts) {
      const m = meta.get(e.node.id); const seen = new Set();
      for (const s of m.segs) {
        if (!(s.characters || '').trim()) continue;
        const px = s.fontSize; const f = Array.isArray(s.fills) && s.fills.length ? s.fills[s.fills.length - 1] : null;
        const white = f && f.type === 'SOLID' && lum(f.color) >= CONFIG.WHITE_LUM;
        let limit = lim.abs, why = 'abs';
        if (m.role === 'body' && lim.body > limit) { limit = lim.body; why = 'body'; }
        if (m.role === 'note' && lim.note > limit) { limit = lim.note; why = 'note'; }
        if (white && lim.white > limit) { limit = lim.white; why = 'white'; }
        const key = px + why; if (px >= limit || seen.has(key)) continue; seen.add(key); fails++;
        items.push(item(e.node, { role: m.role + '/' + m.by, value: `${round1(px)}px=${round1(px / k / 25.4 * 72)}pt`, limit: `${limit}px(${why})`, chars: cut(s.characters, CONFIG.CHARS_LEN), fix: `fontSize を ${limit}px 以上に(文言を短くして収める)` }));
      }
    }
    checks.push(finish({ id: 'P2' }, items, fails, 0, `limits px: body ${lim.body} / note ${lim.note} / abs ${lim.abs} / white ${lim.white}`));
  } catch (err) { checks.push({ id: 'P2', status: 'Error', count: 0, items: [], message: String(err) }); }

  // P3-a 文字あふれ(textAutoResize NONE のみ。clone → HEIGHT → 高さ比較 → finally remove)
  try {
    const items = []; let fails = 0, manuals = 0, checked = 0, tight = 0;
    const targets = liveTexts.filter(e => e.node.textAutoResize === 'NONE');
    const fontKeys = new Map();
    for (const e of targets) if (!e.node.hasMissingFont) for (const s of meta.get(e.node.id).segs) if (s.fontName) fontKeys.set(s.fontName.family + '|' + s.fontName.style, s.fontName);
    const failedFonts = new Set();
    for (const [key, fn] of fontKeys) { try { await figma.loadFontAsync(fn); } catch (err) { failedFonts.add(key); } }
    for (const e of targets) {
      const n = e.node, m = meta.get(n.id);
      if (n.hasMissingFont) { manuals++; items.push(item(n, { role: m.role, value: 'hasMissingFont', fix: 'フォントを入れて再実行、または目視' })); continue; }
      if (m.segs.some(s => s.fontName && failedFonts.has(s.fontName.family + '|' + s.fontName.style))) { manuals++; items.push(item(n, { role: m.role, value: 'font load failed', fix: '目視' })); continue; }
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
          if (wrapped || CONFIG.TIGHT_BOX === 'fail') { fails++; items.push(item(n, { role: m.role, value: `${wrapped ? 'あふれ' : 'tight'} need ${round1(hFit)}px / box ${round1(n.height)}px (+${round1(diff)}, line ${round1(lineH)})`, limit: `+${CONFIG.OVERFLOW_TOL_PX}px`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '文言を短くする(箱・フォントは変えない)' })); }
          else if (CONFIG.TIGHT_BOX === 'manual') { manuals++; items.push(item(n, { role: m.role, value: `tight box ${round1(n.height)}px < text ${round1(hFit)}px`, fix: '目視(折り返しは増えていない)' })); }
          else tight++;
        }
      } catch (err) { manuals++; items.push(item(n, { role: m.role, value: 'clone error: ' + String(err).slice(0, 60), fix: '目視' }));
      } finally { if (c) { try { c.remove(); } catch (e2) {} } }
    }
    checks.push(finish({ id: 'P3-a' }, items, fails, manuals, `NONE ${targets.length} 件中 ${checked} 件を計測、tight(折返し増なし) ${tight} 件は ${CONFIG.TIGHT_BOX}`));
  } catch (err) { checks.push({ id: 'P3-a', status: 'Error', count: 0, items: [], message: String(err) }); }

  // P4 コントラスト(単色背景のみ)
  try {
    const items = []; let fails = 0, manuals = 0, skipped = 0;
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
      if ((n.opacity != null && n.opacity < 0.99) || fgs.some(c => !c)) { manuals++; items.push(item(n, { role: m.role, value: '文字色が SOLID/不透明でない', fix: '目視' })); continue; }
      // 背景=TEXT 矩形を 90% 以上覆う、手前側の最上位。root フレームは最背面候補
      let bg = rootFill ? { idx: -1, fill: rootFill, opacity: frame.opacity == null ? 1 : frame.opacity, rect: true, name: '(frame)' } : null;
      for (const c of cands) if (c.idx < e.idx && c.rect && inter(c.bb, tb) / ta >= CONFIG.BG_COVER) bg = c;
      if (!bg) { manuals++; items.push(item(n, { role: m.role, value: '背景未検出', fix: '目視' })); continue; }
      const between = cands.find(c => c.idx > bg.idx && c.idx < e.idx && (c.shape || c.fill.type !== 'SOLID') && inter(c.bb, tb) / ta >= 0.5);
      if (between) { manuals++; items.push(item(n, { role: m.role, value: `背景に非矩形/画像 ${cut(between.name, 12)}`, fix: '目視' })); continue; }
      if (bg.fill.type !== 'SOLID' || (bg.fill.opacity != null && bg.fill.opacity < 0.99) || bg.opacity < 0.99) { manuals++; items.push(item(n, { role: m.role, value: `背景 ${bg.fill.type}${bg.opacity < 0.99 || (bg.fill.opacity != null && bg.fill.opacity < 0.99) ? '(半透明)' : ''} ${cut(bg.name, 12)}`, fix: '目視' })); continue; }
      let worst = Infinity, worstFg = null;
      for (const c of new Set(fgs.map(hex))) { const col = fgs.find(x => hex(x) === c); const r = contrast(col, bg.fill.color); if (r < worst) { worst = r; worstFg = col; } }
      if (worst < need) { fails++; items.push(item(n, { role: m.role + '/' + m.by, value: `${round1(worst)}:1 ${hex(worstFg)} on ${hex(bg.fill.color)} (${cut(bg.name, 12)})`, limit: `${need}:1`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '文字色を濃く/背景を淡く' })); }
    }
    checks.push(finish({ id: 'P4' }, items, fails, manuals, `対象 ${liveTexts.length - skipped} 件(other ${skipped} 件は対象外)`));
  } catch (err) { checks.push({ id: 'P4', status: 'Error', count: 0, items: [], message: String(err) }); }

  // P6 折り安全域(全 TEXT が折り線 ±46px に入らない・またがない)
  try {
    const items = []; let fails = 0;
    if (!sheet.folds || !fbb) { checks.push({ id: 'P6', status: 'Pass', count: 0, items: [], message: '折り線なしのシート' }); }
    else {
      const margin = mmPx(CONFIG.FOLD_MARGIN_MM);
      const portrait = fbb.height >= fbb.width;
      // 折り線は絶対座標で計算(180°回転でも 1/3・2/3・1/2 は対称)。表示・除外は設計座標
      const lx = ax => toLocal(frame, ax, fbb.y + fbb.height / 2).x, ly = ay => toLocal(frame, fbb.x + fbb.width / 2, ay).y;
      const skip = (v, arr) => arr.some(s => Math.abs(s - v) < 1);
      const vx = (portrait ? [fbb.x + fbb.width / 3, fbb.x + fbb.width * 2 / 3] : [fbb.x + fbb.width / 2]).filter(x => !skip(lx(x), CONFIG.P6_SKIP_FOLDS.x));
      const hy = (portrait ? [fbb.y + fbb.height / 2] : [fbb.y + fbb.height / 3, fbb.y + fbb.height * 2 / 3]).filter(y => !skip(ly(y), CONFIG.P6_SKIP_FOLDS.y));
      for (const e of liveTexts) {
        const n = e.node; if (CONFIG.P6_EXCLUDE_NAME.test(n.name || '')) continue;
        const b = meta.get(n.id).bbox; const hits = [];
        for (const x of vx) if (x > b.x - margin && x < b.x + b.width + margin) hits.push(`x=${lx(x)}(${x > b.x && x < b.x + b.width ? 'またぎ' : 'gap ' + round1(Math.min(Math.abs(b.x - x), Math.abs(b.x + b.width - x)))})`);
        for (const y of hy) if (y > b.y - margin && y < b.y + b.height + margin) hits.push(`y=${ly(y)}(${y > b.y && y < b.y + b.height ? 'またぎ' : 'gap ' + round1(Math.min(Math.abs(b.y - y), Math.abs(b.y + b.height - y)))})`);
        if (hits.length) { const p = toLocal(frame, b.x, b.y), q = toLocal(frame, b.x + b.width, b.y + b.height); fails++; items.push(item(n, { role: meta.get(n.id).role, value: hits.join(' '), limit: `≥${margin}px`, at: `${Math.min(p.x, q.x)},${Math.min(p.y, q.y)} ${round1(b.width)}×${round1(b.height)}`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '折り線から離す/文言を短くする' })); }
      }
      checks.push(finish({ id: 'P6' }, items, fails, 0, `folds(local) x:${vx.map(lx).join(',')} y:${hy.map(ly).join(',')} margin ${margin}px`));
    }
  } catch (err) { checks.push({ id: 'P6', status: 'Error', count: 0, items: [], message: String(err) }); }

  // P7 仮置き文言
  try {
    const items = []; let fails = 0;
    for (const e of texts) {
      const n = e.node; if (CONFIG.P7_EXCLUDE_NAME.test(n.name || '')) continue;
      const mt = (n.characters || '').match(CONFIG.P7_PATTERN);
      if (mt) { fails++; items.push(item(n, { role: meta.get(n.id).role, value: mt[0], chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '実内容に置換、使わないなら hidden に' })); }
    }
    checks.push(finish({ id: 'P7' }, items, fails, 0));
  } catch (err) { checks.push({ id: 'P7', status: 'Error', count: 0, items: [], message: String(err) }); }

  // P12 電話番号(最大の電話番号が本文中央値×倍率以上か)
  try {
    const bodyPx = []; const phones = [];
    for (const e of liveTexts) {
      const m = meta.get(e.node.id);
      if (m.role === 'body') for (const s of m.segs) if ((s.characters || '').trim()) bodyPx.push(s.fontSize);
      if (m.role === 'phone' && CONFIG.ROLE_CHARS[0][1].test(e.node.characters || '')) phones.push({ n: e.node, px: Math.max(...m.segs.map(s => s.fontSize || 0)) });
    }
    if (!phones.length) checks.push({ id: 'P12', status: 'Manual', count: 1, items: [], message: '電話番号らしい TEXT が見つからない(role phone + 数字列)' });
    else if (!bodyPx.length) checks.push({ id: 'P12', status: 'Manual', count: 1, items: [], message: '本文(role body)が見つからず中央値が取れない' });
    else {
      bodyPx.sort((a, b) => a - b); const med = bodyPx[Math.floor(bodyPx.length / 2)];
      const limit = med * CONFIG.PHONE_RATIO; phones.sort((a, b) => b.px - a.px); const top = phones[0];
      const items = top.px < limit ? [item(top.n, { role: 'phone', value: `${round1(top.px)}px`, limit: `≥${round1(limit)}px(本文中央値 ${med}px×${CONFIG.PHONE_RATIO})`, chars: cut(top.n.characters, CONFIG.CHARS_LEN), fix: '電話番号を大きくする' })] : [];
      checks.push(finish({ id: 'P12' }, items, items.length, 0, `body median ${med}px, phones: ${phones.map(p => round1(p.px) + 'px').join('/')}`));
    }
  } catch (err) { checks.push({ id: 'P12', status: 'Error', count: 0, items: [], message: String(err) }); }

  out.summary = checks.reduce((a, c) => { const key = c.status.toLowerCase(); a[key] = (a[key] || 0) + 1; return a; }, { fail: 0, manual: 0, pass: 0 });
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
let payload = { page: page.name, sheet: CONFIG.SHEET, results, tmpRemovedAtEnd: tmpLeft, ms: Date.now() - t0 };
let json = JSON.stringify(payload);
if (json.length > CONFIG.OUT_LIMIT) {
  for (const r of results) for (const c of (r.checks || [])) { if (c.items && c.items.length > 5) { c.truncated = (c.truncated || 0) + c.items.length - 5; c.items = c.items.slice(0, 5); } }
  payload.note = `出力が ${json.length} 字で 20KB を超えたため items を 5 件に切り詰めた。FRAME_IDS を分けて再実行すること`;
  json = JSON.stringify(payload);
}
payload.bytes = json.length;
return payload;
```
