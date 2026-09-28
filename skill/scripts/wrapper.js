// wrapper.js — Step 5 書き出し用フレーム(ラッパー)の作成(use_figma にそのまま貼る。先頭 CONFIG だけ書き換える)
// 1 回で 1 枚(表紙 or 中面)。**最後の preflight の後に作る**(ラッパーは clone なので、制作物を直したら作り直す)。
// (1) 書き出しページ(無ければ作る)に、塗り足し 3mm(17.08px)を四辺に足した空フレームを作る(clipsContent=true)
// (2) 制作物フレームの clone(clipsContent=false、回転は保つ)を (17.08, 17.08) に入れる
// (3) 塗り足しの色 = 端の色の延長: clone の四辺の 2px 内側を 4px おきに調べ、最前面の単色の面の色を取る。
//     一番長い色をラッパーの塗りに、それ以外の区間は clone の背面に塗り足し矩形(`塗り足し:…`)を置く
// (4) rescale(0.497865 = 841.89 / 1691)→ 858.9×1207.9(= 303×426mm @1px=1pt)。縮小前後の寸法を確認(P1 のラッパー分)

const CONFIG = {
  PAGE_NAME: '書き出し',          // 書き出しページの名前(無ければ作る)
  SRC_FRAME_ID: '0:0',           // 制作物フレーム(表紙 or 中面)
  NAME: '案件名_表紙_書き出し_20261001',
  REPLACE: true,                 // 同名のラッパーがあれば消して作り直す
  BLEED_PX: 17.08,               // 3mm × k(5.694)
  SCALE: 0.497865,               // 841.89 / 1691
  EXPECT: { before: [1725.16, 2426.16], after: [858.9, 1207.9], tolBefore: 0.5, tolAfter: 0.2 },
  STEP: 4, INSET: 2,             // 端の色を調べる間隔と、端からの内側距離(px)
};

let page = figma.root.children.find(p => p.name === CONFIG.PAGE_NAME);
const createdPage = !page;
if (!page) { page = figma.createPage(); page.name = CONFIG.PAGE_NAME; }
await figma.setCurrentPageAsync(page);
const src = await figma.getNodeByIdAsync(CONFIG.SRC_FRAME_ID);
if (!src) return { error: 'SRC_FRAME_ID not found' };
const rot = Math.round(Math.atan2(src.relativeTransform[1][0], src.relativeTransform[0][0]) * 180 / Math.PI);
if (rot !== 0 && Math.abs(rot) !== 180) return { error: `回転 ${rot}° のフレームは未対応(0° と 180° のみ)` };
const removed = [];
if (CONFIG.REPLACE) for (const n of page.children.filter(n => n.name === CONFIG.NAME)) { removed.push(n.id); n.remove(); }
const b = CONFIG.BLEED_PX, W = src.width, H = src.height;
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const rgb = h => ({ r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255, b: parseInt(h.slice(5, 7), 16) / 255 });

// (1)(2) 枠と clone
const right = page.children.reduce((m, n) => Math.max(m, n.x + n.width), 0);
const wrap = figma.createFrame(); page.appendChild(wrap);
wrap.name = CONFIG.NAME; wrap.resize(W + 2 * b, H + 2 * b); wrap.x = right + 200; wrap.y = 0; wrap.clipsContent = true;
const c = src.clone(); wrap.appendChild(c); c.clipsContent = false;
c.relativeTransform = rot === 0 ? [[1, 0, b], [0, 1, b]] : [[-1, 0, b + W], [0, -1, b + H]];
const before = [Math.round(wrap.width * 100) / 100, Math.round(wrap.height * 100) / 100];

// (3) 端の色(clone の見た目の四辺)。最前面の、可視・単色・軸平行の面(テンプレの面背景は VECTOR が多いので含める。箱で近似)
const faces = [];
(function walk(n) { if (n.visible === false) return; if (n !== c && n.type !== 'TEXT' && ['RECTANGLE', 'FRAME', 'INSTANCE', 'COMPONENT', 'VECTOR', 'BOOLEAN_OPERATION'].includes(n.type) && Array.isArray(n.fills)) { const f = n.fills.filter(p => p.visible !== false).slice(-1)[0]; const m = n.absoluteTransform; const aligned = Math.abs(m[0][1]) < 1e-6 && Math.abs(m[1][0]) < 1e-6; if (f && aligned && n.absoluteBoundingBox) faces.push({ bb: n.absoluteBoundingBox, fill: f, name: n.name }); } if ('children' in n) for (const k of n.children) walk(k); })(c);
const rootFill = (c.fills || []).filter(p => p.visible !== false).slice(-1)[0];
const cb = c.absoluteBoundingBox, wb = wrap.absoluteBoundingBox, used = new Set();
function colorAt(ax, ay) {
  for (let i = faces.length - 1; i >= 0; i--) { const f = faces[i], q = f.bb; if (ax >= q.x && ax <= q.x + q.width && ay >= q.y && ay <= q.y + q.height) { used.add(f.name); return f.fill.type === 'SOLID' && (f.fill.opacity == null || f.fill.opacity > 0.99) ? hex(f.fill.color) : '?' + f.fill.type; } }
  return rootFill && rootFill.type === 'SOLID' ? hex(rootFill.color) : '#FFFFFF';
}
const edges = { top: [], bottom: [], left: [], right: [] };
for (let t = 0; t <= cb.width; t += CONFIG.STEP) { edges.top.push([t, colorAt(cb.x + t, cb.y + CONFIG.INSET)]); edges.bottom.push([t, colorAt(cb.x + t, cb.y + cb.height - CONFIG.INSET)]); }
for (let t = 0; t <= cb.height; t += CONFIG.STEP) { edges.left.push([t, colorAt(cb.x + CONFIG.INSET, cb.y + t)]); edges.right.push([t, colorAt(cb.x + cb.width - CONFIG.INSET, cb.y + t)]); }
const runs = []; const len = {};
for (const [edge, pts] of Object.entries(edges)) {
  const L = edge === 'top' || edge === 'bottom' ? cb.width : cb.height;
  let s = 0;
  for (let i = 1; i <= pts.length; i++) if (i === pts.length || pts[i][1] !== pts[s][1]) { const from = pts[s][0], to = i === pts.length ? L : pts[i][0]; runs.push({ edge, from, to, color: pts[s][1] }); len[pts[s][1]] = (len[pts[s][1]] || 0) + (to - from); s = i; }
}
const major = Object.entries(len).filter(([k]) => k[0] === '#').sort((a, b2) => b2[1] - a[1])[0][0];
wrap.fills = [{ type: 'SOLID', color: rgb(major) }];
const ox = cb.x - wb.x, oy = cb.y - wb.y;  // clone の左上(= b, b)
const bleeds = [];
for (const r of runs) {
  if (r.color === major || r.color[0] !== '#') continue;
  const rect = figma.createRectangle(); rect.name = `塗り足し:${r.edge} ${Math.round(r.from)}-${Math.round(r.to)}`;
  const a0 = r.from === 0 ? -b : r.from, a1 = r.to >= (r.edge === 'top' || r.edge === 'bottom' ? cb.width : cb.height) ? (r.edge === 'top' || r.edge === 'bottom' ? cb.width : cb.height) + b : r.to;
  if (r.edge === 'top') { rect.resize(a1 - a0, b + CONFIG.INSET); rect.x = ox + a0; rect.y = 0; }
  if (r.edge === 'bottom') { rect.resize(a1 - a0, b + CONFIG.INSET); rect.x = ox + a0; rect.y = oy + cb.height - CONFIG.INSET; }
  if (r.edge === 'left') { rect.resize(b + CONFIG.INSET, a1 - a0); rect.x = 0; rect.y = oy + a0; }
  if (r.edge === 'right') { rect.resize(b + CONFIG.INSET, a1 - a0); rect.x = ox + cb.width - CONFIG.INSET; rect.y = oy + a0; }
  rect.fills = [{ type: 'SOLID', color: rgb(r.color) }];
  wrap.insertChild(0, rect); bleeds.push(rect.id);
}
const unknown = runs.filter(r => r.color[0] !== '#').map(r => `${r.edge} ${Math.round(r.from)}-${Math.round(r.to)} ${r.color}`);

// (4) 縮小と寸法確認
wrap.rescale(CONFIG.SCALE);
const after = [Math.round(wrap.width * 100) / 100, Math.round(wrap.height * 100) / 100];
const E = CONFIG.EXPECT;
const fit = (v, e, tol) => (Math.abs(v[0] - e[0]) <= tol && Math.abs(v[1] - e[1]) <= tol) || (Math.abs(v[0] - e[1]) <= tol && Math.abs(v[1] - e[0]) <= tol);  // 横型(2392×1691)も可
const p1 = {
  before, after,
  beforeOk: fit(before, E.before, E.tolBefore),
  afterOk: fit(after, E.after, E.tolAfter),
  mm: [Math.round(after[0] / 72 * 25.4 * 10) / 10, Math.round(after[1] / 72 * 25.4 * 10) / 10],
};
return { page: page.id, createdPage, removed, wrapper: wrap.id, clone: c.id, createdNodeIds: [wrap.id, ...bleeds], major, bleeds: runs.filter(r => r.color !== major).slice(0, 20).map(r => `${r.edge} ${Math.round(r.from)}-${Math.round(r.to)} ${r.color}`), unknown: unknown.slice(0, 10), edgeNodes: [...used].slice(0, 12), p1 };
