# Figma操作の必須ルール(use_figma)

use_figmaはFigmaファイル内でJavaScript(Plugin API)を実行する。以下はFigma公式figma-useスキルの要点をパンフレット制作向けに凝縮したもの。環境に公式figma-useスキルがあればそちらを正とする。

## 基本ルール

1. **少しずつ作る。** 大きな操作は複数呼び出しに分割し、1ステップごとに検証する
2. 結果は`return`で返す(`console.log`は返らない)。作成・変更した全ノードIDを`return { createdNodeIds: [...], mutatedNodeIds: [...] }`で返し、次の呼び出しで参照する
3. 素のJavaScriptで書く。トップレベル`await`と`return`が使える。async即時関数で包まない。`figma.notify()`は使えない
4. 色は0〜1の範囲。`{r: 1, g: 0, b: 0}`が赤
5. fills / strokesは読み取り専用配列。複製→変更→再代入:
   ```js
   const fills = JSON.parse(JSON.stringify(node.fills));
   fills[0].color = { r: 1, g: 0.95, b: 0.85 };
   node.fills = fills;
   ```
6. エラー時は即リトライしない。失敗したスクリプトは何も実行されていないので、エラー文を読み、直してから再実行する
7. すべてのPromiseに`await`を付ける(付け忘れは無言の失敗になる)
8. ページ直下の新規ノードは(0,0)を避け、既存ノードの右側など空き位置に置く

## テキスト編集の定型

フォントを読み込まずにテキストを触ると必ずエラーになる。定型: フォント読み込み→await→変更→ID返却。

```js
const node = await figma.getNodeByIdAsync("123:45");
const segments = node.getStyledTextSegments(["fontName"]);
for (const seg of segments) {
  await figma.loadFontAsync(seg.fontName);  // 現在のフォントを取得して読む。決め打ちしない
}
node.characters = "新しい文言";
return { mutatedNodeIds: [node.id] };
```

- 日本語フォントのスタイル名が不確かなら、先に`await figma.listAvailableFontsAsync()`で確認する
- **loadFontAsyncが失敗する(テンプレのフォントが環境にない)場合**は、同等ウェイトのNoto Sans JPに置換して続行し、置換した旨を利用者に報告する。対応例: Source Han Sans JP の Regular/Medium/Bold/Heavy → Noto Sans JP の Regular/Medium/Bold/Black。置換時はそのテキストノードのfontNameを新フォントに設定してからcharactersを変更する
- 文言差し替えではフォント・サイズを変えない。テンプレートのテキストスタイルを崩さない
- 文字数が元より大幅に増えたら、差し替え後にget_screenshotであふれを確認する

## ページ

- 切り替えは`await figma.setCurrentPageAsync(page)`。同期代入はエラー
- 1回の呼び出しで切り替えは1回まで。ページ状態は呼び出しごとに先頭ページへリセットされる
- 素材ページ→作業ページの複製は、素材ページでclone→作業ページにappendChildを1スクリプト内で行う(切り替え1回で済む)

## レイアウト

- 関連する子要素を並べる容器は`figma.createAutoLayout()`。絶対座標の手並べは文字量の変化で崩れる
- 子の`layoutSizingHorizontal/Vertical`(`'FIXED'|'HUG'|'FILL'`)は、親にappendChildしてから設定する
- フレーム自身の`primaryAxisSizingMode / counterAxisSizingMode`は`'FIXED'|'AUTO'`。子用の値と混同しない
- テンプレート複製ベースでは既存構造を尊重し、構造変更は最小限にする

## 画像

use_figma内から外部URLの画像取得はできない。手段は2つ:

**手段A(本線): ファイル内の既存画像を複製する。** 「素材」ページの画像をcloneするか、既存ノードの`imageHash`を使い回す:
```js
node.fills = [{ type: 'IMAGE', scaleMode: 'FILL', imageHash: '既存ノードのhash' }];
```

**手段B: upload_assetsツール。** チャット添付の画像を取り込める環境でのみ有効。失敗したらリトライせず手段Aに切り替え、「素材」ページへのドラッグ&ドロップを案内する。

SVGは`figma.createNodeFromSvg('<svg>...</svg>')`で直接生成できる。雲・帯・バッジ等の装飾はこれで自作してよい。

## 回転・面付けフレームへの配置

冊子テンプレートは面付けのため180°回転した面を含む。回転した親の中ではx/yの直接指定が見た目とズレ、新規ノードが逆さ・枠外になる。

- **第一原則: 逆さ面では既存の空欄テキスト・プレースホルダの差し替えで済ませ、新規ノードの追加を避ける**
- 新規追加が必要な場合のみ、`relativeTransform = 親のabsoluteTransformの逆行列 × 目標の絶対変換` で配置する:

```js
function inv(m) {
  const [a, c, e] = m[0], [b, d, f] = m[1];
  const det = a * d - c * b;
  return [[d / det, -c / det, (c * f - d * e) / det],
          [-b / det, a / det, (b * e - a * f) / det]];
}
function mul(A, B) {
  return [0, 1].map(i => [
    A[i][0] * B[0][0] + A[i][1] * B[1][0],
    A[i][0] * B[0][1] + A[i][1] * B[1][1],
    A[i][0] * B[0][2] + A[i][1] * B[1][2] + A[i][2]
  ]);
}
parent.appendChild(node);
// ページ絶対座標(ax, ay)に絶対回転angle(逆さ面に沿わせるならMath.PI)で置く
const t = [[Math.cos(angle), -Math.sin(angle), ax], [Math.sin(angle), Math.cos(angle), ay]];
node.relativeTransform = mul(inv(parent.absoluteTransform), t);
```

- 配置後は必ずget_screenshotで向きと位置を確認する

## 検証

- 1ブロック作業するごとにget_screenshotで対象フレームを取得し、崩れを目視確認する
- 構造の確認(ノード名・階層・ID)はget_metadataを使う。findAllでの全走査を先にしない

## 探索と返り値の約束(2026-10)

- **`figma.root.findAll` は使わない。** ページをまたぐ全走査は重く、1呼び出し1ページの制約にも反する
- `#` ノードの探索は**制作物フレームを起点に1回だけ**行い、`{名前 → id[]}` の地図を返す。以後の呼び出しは id で `getNodeByIdAsync` する(非表示の枠も拾うため `findAll` を使う。表紙1枚で約65名・1.5KB)
  ```js
  const frame = await figma.getNodeByIdAsync(FRAME_ID);
  const map = {};
  for (const n of frame.findAll(n => n.name.startsWith('#'))) (map[n.name] = map[n.name] || []).push(n.id);
  return map;   // 同名が複数あるもの(#QR置き場 #ロゴ置き場 など)は id が配列に並ぶ
  ```
- `node.query()` のセレクタに日本語の名前は使えない(`findOne` / `findAll` の述語で書く)
- **返り値は 20KB(UTF-8 換算、日本語は1字3バイト)以内。** 文字列は先頭15〜20字に切る、件数の多い配列は件数+先頭数件だけ返す、フレームを分けて呼び出しを並べる。preflight は超過時に自動で切り詰める(preflight.md §6)
- 一時的に作ったノード(計測用の複製など)は `try { … } finally { node.remove() }` で必ず消す
- `setPluginData` と `FrameNode.description` への書き込みは使えない(失敗する)。状態は下記の非表示テキストに持つ

## 状態の置き場所(`#config` / `#tone` / `#state`)

いずれも**非表示・ロック済みの TEXT ノード**で、中身は1行の JSON。フォントは `Noto Sans JP` Regular(`#tone` `#state` は 8px、`#config` は 24px)。読み書きの前にそのノードの `fontName` を `loadFontAsync` し、書き換えるときは `locked = false` → `characters` 代入 → `locked = true` の順にする。オペレータに中身を見せない。

| 名前 | 置き場所 | 書く人 | 中身 |
|---|---|---|---|
| `#config` | `テンプレート`ページ直下(id 2057:2) | デザイン担当のみ(スキルは読むだけ) | `skill_min_version` / `pipeline`("on"/"off")/ 物理寸法 / K2 プリセットの枠座標 / `pipeline_off_hide` |
| `#tone` | Step 1.7 はスタイルタイルの中 → Step 2 以降は**表紙フレームの直下**。素材ページの `ライブラリ/<系統>` にも原本がある | Step 1.7 | ライブラリの見た目の方針(tone/3)+ オペレータの選択(`meta.operator_choice`)+ 地域の絵の id(`meta.library.regional_motif_id`) |
| `#state` | `#tone` と同じ場所 | 各 Step の終わり | 進み具合(下記) |

### #config を読む(Step 0)

```js
const tp = figma.root.children.find(p => p.name === 'テンプレート');
await figma.setCurrentPageAsync(tp);
const cfg = tp.children.find(n => n.name === '#config' && n.type === 'TEXT');
if (!cfg) return { found: false };
try { const c = JSON.parse(cfg.characters); return { found: true, skill_min_version: c.skill_min_version, pipeline: c.pipeline, pipeline_off_hide: c.pipeline_off_hide }; }
catch (e) { return { found: true, parseError: String(e).slice(0, 80) }; }
```

- 版の比較は文字列の大小(`"2026-10" < "2026-11"`)。`skill_min_version` > スキル版 なら停止
- `pipeline_off_hide` は `pipeline: off` のとき複製直後に非表示にする枠の名前(`#キービジュアル` `#地域モチーフ` `#人物` `#車両`)
- 既知の注意: 2026-09-27 時点の `#config` の `templates` と `presets.K2.vehicle.by_series` は旧 id(18:2 など)をキーにしている。**id ではなく系統名で引く**こと(スキルは現在これらを使わない)

### 地域の絵のゲート(Step 1.5)

```js
const page = await figma.getNodeByIdAsync('7:4');            // 素材ページ
await figma.setCurrentPageAsync(page);
const g = page.children.find(n => n.name === '案件/' + CASE_NAME);
const motif = g && 'findOne' in g ? g.findOne(n => n.name.startsWith('#地域モチーフ')) : null;
return { group: g ? g.id : null, motif: motif ? { id: motif.id, name: motif.name } : null };
```

`motif` が null なら着手しない。案件名の表記ゆれ(「くらぶち」と「倉渕」など)で見つからないときは、`案件/` で始まるグループ名の一覧を返してオペレータに選んでもらう(他案件の絵を勝手に使わない)。

### #state の形

```json
{"schema":"state/1","skill_version":"2026-10","pipeline":"on","case":"くらぶち","step":"2",
 "family":"あいとま系","base_id":"aitoma-K2-abst-01","style_tile":"<id>",
 "frames":{"cover":"<id>","inner":"<id>","spot":null},
 "preflight":{"at":"<ISO>","cover":{"fail":0,"warn":1,"manual":0}},"autofix_rounds":0,
 "handoff":[],"updated":"<ISO>"}
```

- `step` は最後に**終わった** Step("1.7" / "2" / "3" / "4" / "5")。再開は次の Step から
- 再開の探し方: `制作物`ページ直下で名前が `<案件名>_表紙_` で始まるフレームの直下 `#state` を読む(複数あれば `updated` が新しい方を示して、どれを正とするかオペレータに確認する。勝手に消さない)

### #tone / #state を表紙へ移す(Step 2)

```js
const tile = await figma.getNodeByIdAsync(TILE_ID), cover = await figma.getNodeByIdAsync(COVER_ID);
const moved = [];
for (const nm of ['#tone', '#state']) {
  const t = tile.findOne(n => n.name === nm && n.type === 'TEXT'); if (!t) continue;
  t.locked = false; cover.appendChild(t); t.visible = false; t.locked = true; moved.push(t.id);
}
const st = cover.findOne(n => n.name === '#state');
await figma.loadFontAsync(st.fontName);
const s = JSON.parse(st.characters);
Object.assign(s, { step: '2', frames: { cover: COVER_ID, inner: INNER_ID, spot: SPOT_ID || null }, updated: new Date().toISOString() });
st.locked = false; st.characters = JSON.stringify(s); st.locked = true;
return { mutatedNodeIds: moved };
```

180°回転した表紙(あいとま系)に入れても非表示なので見た目は変わらない。preflight は `#tone` `#state` `#config` を検査対象から外している。

### 指定色の反映(Step 1.5 の4)

指定色は `#tone` の `palette.roles.main` に入れ、`provenance["palette.roles.main"] = "operator"` とする。白い文字を載せる・見出しの2色目に使うため、**白と `ground` の両方に対して 4.5:1 以上になるまで明度を下げる**(色相は保つ)。`main_tint` は同じ色相で明度を上げ彩度を下げる(目安 HSL で L+25〜35・S−20〜30)。`meta.locked.brand_palette` が true(MITT 系)の場合は反映しない。

## スタイルタイル(Step 1.7)

先頭の `C` だけを書き換えて実行する(2026-09-27 に制作物ページで試験済み)。素材ページのライブラリ `#tone` を読み、タイルを作り、**同じ呼び出しでタイルの中に `#tone` と `#state` を保存して読み戻す**。やり直すときは前のタイルの id を `DELETE_IDS` に入れる。

```js
const C = {
  PAGE_ID: '7:2', LIB_GROUP_ID: '2074:3', MOTIF_GROUP_ID: '2068:16',   // 制作物 / ライブラリ/<系統> / 案件/<案件名>
  CASE: 'くらぶち', DATE: '20261001', OPTION: 1, REASON: 'うちの地域の人っぽい',   // REASON はオペレータの言葉のまま
  TITLE: 'くらぶち のりあいタクシー', SERVICE: 'のりあいタクシー', TITLE_PX: 60, PHONE: '0120-000-000',
  DELETE_IDS: [],
};
const page = await figma.getNodeByIdAsync(C.PAGE_ID);
await figma.setCurrentPageAsync(page);
for (const id of C.DELETE_IDS) { const n = await figma.getNodeByIdAsync(id); if (n) n.remove(); }
const lib = await figma.getNodeByIdAsync(C.LIB_GROUP_ID);
const toneSrc = lib.findOne(n => n.name === '#tone' && n.type === 'TEXT');
const tone = JSON.parse(toneSrc.characters);
const pick = re => lib.children.find(n => re.test(n.name));
const img = n => n && n.fills.find(f => f.type === 'IMAGE');
const bg = img(pick(/ 背景 \| /)), person = pick(/ 人物A \| /), vehicle = pick(/ 車両 \| /);
const mg = C.MOTIF_GROUP_ID ? await figma.getNodeByIdAsync(C.MOTIF_GROUP_ID) : null;
const motif = mg && mg.findOne(n => n.name.startsWith('#地域モチーフ'));
const hex = h => ({ r: parseInt(h.slice(1,3),16)/255, g: parseInt(h.slice(3,5),16)/255, b: parseInt(h.slice(5,7),16)/255 });
const R = tone.palette.roles, H = tone.typography.headline;
const REG = {family:'Noto Sans JP',style:'Regular'}, BOLD = {family:'Noto Sans JP',style:'Bold'};
let head = {family:H.family, style:H.weight}, headFallback = false;
try { await figma.loadFontAsync(head); } catch (e) { head = {family:'Noto Sans JP',style:'Black'}; headFallback = true; await figma.loadFontAsync(head); }
await Promise.all([REG, BOLD].map(f => figma.loadFontAsync(f)));
const right = page.children.reduce((m, n) => Math.max(m, n.x + n.width), 0);
const tile = figma.createFrame(); page.appendChild(tile);
tile.name = `${C.CASE}_スタイルタイル_${C.DATE}`; tile.resize(1500, 760); tile.x = right + 200; tile.y = 0;
tile.fills = [{type:'SOLID', color: hex('#FFFFFF')}];
const rect = (name, x, y, w, h, fills) => { const r = figma.createRectangle(); tile.appendChild(r); r.name = name; r.resize(w, h); r.x = x; r.y = y; r.fills = fills; return r; };
const txt = (s, size, font, color, x, y, w) => { const t = figma.createText(); tile.appendChild(t); t.fontName = font; t.fontSize = size; t.characters = s; t.fills = [{type:'SOLID', color: hex(color)}]; t.x = x; t.y = y; if (w) { t.textAutoResize = 'HEIGHT'; t.resize(w, t.height); } return t; };
// (1) 表紙の絵の縮小(ヒーロー 580.7×711 の 1/2)。背面→前面: 背景 → 地域モチーフ → 車両 → 人物
const s = 0.5, X = 40, Y = 40, HW = 580.7 * s, HH = 711 * s;
rect('見本:キービジュアル', X, Y, HW, HH, [{type:'IMAGE', scaleMode:'FILL', imageHash: bg.imageHash}]);
if (motif) rect('見本:地域モチーフ', X, Y + HH * (tone.composition.hero.horizon_ratio || 0.6) - 170 * s * 0.7, HW, 170 * s, [{type:'IMAGE', scaleMode:'FIT', imageHash: img(motif).imageHash}]);
if (vehicle) rect('見本:車両', X + HW - 300 * s - 2, Y + HH - 4 - 172 * s, 300 * s, 172 * s, [{type:'IMAGE', scaleMode:'FIT', imageHash: img(vehicle).imageHash}]);
if (person) { const ph = 380 * s, pw = ph * person.width / person.height; rect('見本:人物', X + 7, Y + HH - 6 - ph, pw, ph, [{type:'IMAGE', scaleMode:'FIT', imageHash: img(person).imageHash}]); }
// (2) 色チップ(役割名はオペレータ向けの言葉)
const roleLabel = { ground:'地の色', main:'メインの色', main_tint:'淡い色', panel:'パネル', ink:'文字', cta:'電話・申込の色', accent_decor:'差し色' };
Object.entries(roleLabel).forEach(([k, lab], i) => {
  const r = rect('見本:色 ' + lab, 380 + i * 150, 40, 110, 110, [{type:'SOLID', color: hex(R[k])}]);
  r.cornerRadius = 8; r.strokes = [{type:'SOLID', color: hex('#CCCCCC')}]; r.strokeWeight = 1;
  txt(lab, 20, REG, '#000000', 380 + i * 150, 160, 130);
});
// (3) 実タイトルを見出し書体で実寸(サービス名だけメイン色)
const title = txt(C.TITLE, C.TITLE_PX, head, R.ink, 380, 250, 1080);
const at = C.TITLE.indexOf(C.SERVICE);
if (H.two_tone && H.two_tone.enabled && at >= 0) title.setRangeFills(at, at + C.SERVICE.length, [{type:'SOLID', color: hex(R.main)}]);
// (4) 電話の見本(cta 色)
const p = rect('見本:電話パネル', 380, 400, 520, 120, [{type:'SOLID', color: hex(R.panel)}]); p.cornerRadius = 12; p.strokes = [{type:'SOLID', color: hex(R.cta)}]; p.strokeWeight = 4;
txt(C.PHONE, 64, BOLD, R.cta, 410, 420);
const sig = tone.decoration.signature_element;
txt('飾り: ' + (sig === 'none' ? 'なし(落ち着いた見た目)' : sig), 24, REG, '#000000', 380, 560, 1080);
txt('雰囲気の見本です。文字と細かい配置は変わります', 22, REG, '#666666', 40, 700, 1400);
// (5) #tone / #state を保存(非表示・ロック・Noto Sans JP Regular 8px)
tone.meta.operator_choice = { selected_option: C.OPTION, reason_verbatim: C.REASON };
tone.meta.library.regional_motif_id = motif ? (motif.name.split('|')[1] || '').trim() || motif.id : null;
tone.provenance = Object.assign({}, tone.provenance, { 'meta.operator_choice': 'operator' });
const state = { schema: 'state/1', skill_version: '2026-10', pipeline: 'on', case: C.CASE, step: '1.7',
  family: tone.meta.template_family, base_id: tone.meta.library.base_id, style_tile: tile.id, frames: {},
  preflight: null, autofix_rounds: 0, handoff: [], updated: new Date().toISOString() };
const save = (name, obj) => { const t = figma.createText(); tile.appendChild(t); t.fontName = REG; t.fontSize = 8; t.characters = JSON.stringify(obj); t.name = name; t.x = 0; t.y = 0; t.visible = false; t.locked = true; return t; };
const tn = save('#tone', tone), sn = save('#state', state);
const back = JSON.parse(tn.characters), backS = JSON.parse(sn.characters);
const defaults = Object.entries(tone.provenance).filter(([, v]) => v === 'default').map(([k]) => k);
return { createdNodeIds: [tile.id, tn.id, sn.id], tile: tile.id, headFallback, defaults,
  readback: { base: back.meta.library.base_id, motif: back.meta.library.regional_motif_id, step: backS.step } };
```

- 返り値の `defaults`(見本側で決まっていない項目)をやさしい言葉にしてオペレータへの確認文に添える(例: `typography.headline.family` → 「見出しの書体は標準のもの」、`composition.cover_preset` → 「構図は標準のもの」)
- `headFallback: true` は見出し書体が読み込めず Noto Sans JP Black で代用したという意味。デザイン担当への報告事項に入れる(オペレータには言わない)
- 色の指定がある場合は、実行前に `tone.palette.roles.main` / `main_tint` を「指定色の反映」の規則で置き換える行を (5) の前に足す

## 画像の切り抜き配置(`#キービジュアル` の CROP)

- `imageTransform` は `scaleMode: 'CROP'` のときだけ効く。`FILL` / `FIT` では無視される
- ライブラリの背景は K2 ヒーロー枠(580.7×711、比率 0.817)に近い 4:5 で作ってあるので、枠を満たす最小の拡大(ほぼ等倍)で上下を約2%切るだけになる。`crop_focus` の平行移動の実装は Step 3(【H の結果待ち】)
- 人物・車両・地域の絵は `scaleMode: 'FIT'`(切り抜かない)。配置規則は template-and-assets.md「表紙の絵の配置規則」
