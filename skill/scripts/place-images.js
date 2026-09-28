// place-images.js — Step 3-2 画像スロットへの素材投入(use_figma にそのまま貼る。先頭 CONFIG だけ書き換える)
// 表紙面: #キービジュアル = ライブラリ背景を CROP(imageTransform を枠と画像の縦横比から計算)、
//         #人物 #車両 #地域モチーフ = FIT。枠の座標・大きさは テンプレートページの #config presets.K2B_panel.by_family(系統名で引く)に合わせる。
// 案件の画像(ロゴ・QR・地図・写真)は EXTRA で置き場を指定して FIT。
// 最後に、素材の入らなかった #…置き場・サンプル: ・(サンプル一式) を非表示にする(HIDE_EMPTY)。
// 新しいノードは作らない(fills と位置・大きさ・表示だけを変える)。

const CONFIG = {
  PAGE_ID: '7:2',
  FRAME_ID: '0:0',
  KIND: 'cover',                 // 'cover' なら表紙面の絵を入れる。'inner' は EXTRA と非表示だけ
  FAMILY: 'aitoma',              // aitoma | nachikatsuura | noboribetsu | mitt(#config の series と同じ表記)
  CONFIG_NODE_ID: '2057:2',      // テンプレートページの #config
  LIB_GROUP_ID: '2074:3',        // 素材ページ ライブラリ/<系統>
  PERSON: '人物A',               // '人物A' | '人物B'
  MOTIF_GROUP_ID: '2068:16',     // 素材ページ 案件/<案件名>(#地域モチーフ)。null なら地域の絵を入れない
  CROP_FOCUS: { dx: 0, dy: 0 },  // 背景の切り抜き位置の平行移動(画像に対する割合。0 = 中央)
  EXTRA: [                       // 案件の画像: { src: 画像を持つノード id, slot: 置き場の名前, index: 同名の何番目か(省略 = 全部) }
    // { src: '71:41', slot: '#サービスロゴ置き場' },
  ],
  HIDE_EMPTY: true,
  HIDE_NAME: [/^#.*置き場/, /^サンプル:/, /(サンプル一式)/],   // 素材が入らなければ非表示にするもの
  KEEP_VISIBLE: [],              // 空でも残す名前(例 '#QR置き場' を後で手作業で入れる場合)
  HIDE_WITH: { 'ラベル:×': ['#事業者ロゴ置き場', '#ロゴ置き場'] },   // 右の枠がどれか非表示なら、左で始まる名前も非表示(ロゴの間の「×」)
};

const page = await figma.getNodeByIdAsync(CONFIG.PAGE_ID);
await figma.setCurrentPageAsync(page);
const frame = await figma.getNodeByIdAsync(CONFIG.FRAME_ID);
if (!frame) return { error: 'FRAME_ID not found' };
const round1 = v => Math.round(v * 10) / 10;
const img = n => n && Array.isArray(n.fills) ? n.fills.find(f => f.type === 'IMAGE' && f.visible !== false) : null;
const inv = m => { const [a, c, e] = m[0], [b, d, f] = m[1]; const det = a * d - c * b; return [[d / det, -c / det, (c * f - d * e) / det], [-b / det, a / det, (b * e - a * f) / det]]; };
const mul = (A, B) => [0, 1].map(i => [A[i][0] * B[0][0] + A[i][1] * B[1][0], A[i][0] * B[0][1] + A[i][1] * B[1][1], A[i][0] * B[0][2] + A[i][1] * B[1][2] + A[i][2]]);
// フレームの設計座標 (x,y) に、フレームに対して回転なしで置く(親が GROUP でも FRAME でも、フレームが 180° でも同じ)
function placeInFrame(n, x, y, w, h) {
  n.resize(w, h);
  n.relativeTransform = mul(inv(n.parent.absoluteTransform), mul(frame.absoluteTransform, [[1, 0, x], [0, 1, y]]));
}
function localBox(n) { // フレームの設計座標での箱
  const m = mul(inv(frame.absoluteTransform), n.absoluteTransform);
  return { x: round1(m[0][2]), y: round1(m[1][2]), w: round1(n.width), h: round1(n.height), rot: Math.round(Math.atan2(m[1][0], m[0][0]) * 180 / Math.PI) };
}
const withKeys = Object.keys(CONFIG.HIDE_WITH || {});
const all = frame.findAll(n => n.name.startsWith('#') || /^サンプル:|サンプル一式/.test(n.name) || withKeys.some(k => n.name.startsWith(k)));
const byName = {}; for (const n of all) (byName[n.name] = byName[n.name] || []).push(n);
const filled = new Set(), out = { placed: [], moved: [], hidden: [], warn: [] };

async function setImage(n, hash, mode, transform) {
  const p = { type: 'IMAGE', scaleMode: mode, imageHash: hash };
  if (transform) p.imageTransform = transform;
  n.fills = [p]; n.strokes = []; n.visible = true; filled.add(n.id);
}
function coverSlot(name) { const a = byName[name] || []; return a.find(n => { let p = n.parent; while (p && p !== frame) { if ((p.name || '').startsWith('面:表紙面')) return true; p = p.parent; } return false; }) || a[0]; }

if (CONFIG.KIND === 'cover') {
  const cfgNode = await figma.getNodeByIdAsync(CONFIG.CONFIG_NODE_ID);
  const cfg = JSON.parse(cfgNode.characters);
  const preset = cfg.presets[cfg.cover_preset || 'K2B_panel'];
  const fam = Object.values(preset.by_family).find(v => v.series === CONFIG.FAMILY) || preset.by_family[CONFIG.FAMILY];
  if (!fam) return { error: `#config に系統 ${CONFIG.FAMILY} の枠が無い` };
  const lib = await figma.getNodeByIdAsync(CONFIG.LIB_GROUP_ID);
  const pick = re => lib.children.find(n => re.test(n.name));
  const bgNode = pick(/ 背景 \| /), personNode = pick(new RegExp(' ' + CONFIG.PERSON + ' \\| ')), vehicleNode = pick(/ 車両 \| /);
  let motifNode = null;
  if (CONFIG.MOTIF_GROUP_ID) { const g = await figma.getNodeByIdAsync(CONFIG.MOTIF_GROUP_ID); motifNode = g && g.findOne(n => n.name.startsWith('#地域モチーフ')); }
  const jobs = [['#キービジュアル', 'hero', bgNode, 'CROP'], ['#地域モチーフ', 'motif', motifNode, 'FIT'], ['#車両', 'vehicle', vehicleNode, 'FIT'], ['#人物', 'person', personNode, 'FIT']];
  for (const [slot, key, src, mode] of jobs) {
    const n = coverSlot(slot); const box = fam[key];
    if (!n) { out.warn.push(`${slot} の枠が無い`); continue; }
    if (box) {
      const b0 = localBox(n);
      if (Math.abs(b0.x - box.x) > 0.5 || Math.abs(b0.y - box.y) > 0.5 || Math.abs(b0.w - box.w) > 0.5 || Math.abs(b0.h - box.h) > 0.5) { placeInFrame(n, box.x, box.y, box.w, box.h); out.moved.push(`${slot} ${b0.x},${b0.y} ${b0.w}×${b0.h} → ${box.x},${box.y} ${box.w}×${box.h}`); }
    }
    const f = img(src);
    if (!f) { out.warn.push(`${slot} に入れる素材が無い`); continue; }
    let tf = null;
    if (mode === 'CROP') {
      const { width: iw, height: ih } = await figma.getImageByHash(f.imageHash).getSizeAsync();
      const rn = n.width / n.height, ri = iw / ih;
      const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
      if (rn > ri) { const s = ri / rn; tf = [[1, 0, 0], [0, s, clamp((1 - s) / 2 + CONFIG.CROP_FOCUS.dy, 0, 1 - s)]]; }
      else { const s = rn / ri; tf = [[s, 0, clamp((1 - s) / 2 + CONFIG.CROP_FOCUS.dx, 0, 1 - s)], [0, 1, 0]]; }
      out.dpi = Math.round((rn > ri ? iw / n.width : ih / n.height) * 144.6);
      out.crop = tf.map(r => r.map(v => Math.round(v * 10000) / 10000));
    }
    await setImage(n, f.imageHash, mode, tf);
    out.placed.push(`${slot} ← ${(src.name.split('|')[1] || src.name).trim()} ${mode}`);
  }
}
for (const x of CONFIG.EXTRA) {
  const src = await figma.getNodeByIdAsync(x.src); const f = img(src);
  const targets = (byName[x.slot] || []).filter((n, i) => x.index === undefined || i === x.index);
  if (!f) { out.warn.push(`${x.slot}: ${x.src} に画像が無い`); continue; }
  if (!targets.length) { out.warn.push(`${x.slot} の枠が無い`); continue; }
  for (const n of targets) { await setImage(n, f.imageHash, 'FIT'); out.placed.push(`${x.slot} ← ${x.src} FIT`); }
}
if (CONFIG.HIDE_EMPTY) {
  const seen = {};
  for (const n of all) {
    if (filled.has(n.id) || n.visible === false || CONFIG.KEEP_VISIBLE.includes(n.name)) continue;
    if (!CONFIG.HIDE_NAME.some(re => re.test(n.name))) continue;
    if (img(n) && !/置き場/.test(n.name)) continue;
    const isPlaceholder = /置き場/.test(n.name) ? !img(n) : true;
    if (!isPlaceholder) continue;
    n.visible = false; seen[n.name] = (seen[n.name] || 0) + 1;
  }
  for (const k of withKeys) {
    const any = CONFIG.HIDE_WITH[k].some(nm => (byName[nm] || []).some(n => n.visible === false));
    if (any) for (const n of all) if (n.name.startsWith(k) && n.visible !== false) { n.visible = false; seen[n.name] = (seen[n.name] || 0) + 1; }
  }
  out.hidden = Object.entries(seen).map(([k, v]) => v > 1 ? `${k}×${v}` : k);
}
return Object.assign({ frame: frame.name, mutatedNodeIds: [...filled] }, out);
