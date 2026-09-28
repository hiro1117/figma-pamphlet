// recolor.js — Step 3-3 色の置換(use_figma にそのまま貼る。先頭 CONFIG だけ書き換える)
// (1) 濃淡 2 群の置換: テンプレの系統色(MAP)→ #tone の役割色。fills / strokes / グラデーションの stop / 文字のセグメント。IMAGE は対象外
// (2) 電話・申込の色: 表紙面の #電話:* の文字と、#CTA:見出し のうち main 色の文字を cta 色に
// (3) 白い文字が載る main 色の面(電話予約パネルなど。1 面の 20% 以下の大きさ)を cta 色に(main のままだと白文字が 7:1 に届かない)
// #バッジ には accent_decor を当てない(B.1 v2 の Hiro 判断)。MITT 系(brand_palette 固定)は何もしない。

const CONFIG = {
  PAGE_ID: '7:2',
  FRAME_IDS: ['0:0'],            // 表紙と中面を 1 回で(2 枚まで)
  TONE_FRAME_ID: null,           // #tone を持つフレーム(null = FRAME_IDS[0])
  FAMILY: 'aitoma',
  MAP_BY_FAMILY: {               // テンプレの色 → tone の役割(template-and-assets.md「カラーの適用」)
    aitoma:        { '#EB6EA5': 'main', '#F6BED1': 'main_tint', '#FFD8E3': 'ground' },
    nachikatsuura: { '#1B98D0': 'main', '#76C1E3': 'main_tint' },
    noboribetsu:   { '#D7835F': 'main' },
    mitt:          {},
    spot:          { '#EB6EA5': 'main', '#DE4891': 'main' },
  },
  TOL: 1.5 / 255,                // 色一致の許容差(チャンネルごと)
  WHITE_LUM: 0.85,               // 白い文字とみなす相対輝度
  COVER: 0.9,                    // 文字の箱をこの割合以上覆う面を「文字の下の面」とみなす
  MAX_FACE_RATIO: 0.2,           // (3) の対象はパネル・帯の大きさまで(1 面 = 563.7×1196 の 20% 以下)。面全体の背景は変えない
  CTA_TEXT: [/^#電話:/, /^#CTA:見出し/],   // cta 色にする文字(表紙面のみ。#CTA:見出し は main 色の部分だけ)
};

const page = await figma.getNodeByIdAsync(CONFIG.PAGE_ID);
await figma.setCurrentPageAsync(page);
const holder = await figma.getNodeByIdAsync(CONFIG.TONE_FRAME_ID || CONFIG.FRAME_IDS[0]);
const toneNode = holder && holder.findOne(n => n.name === '#tone' && n.type === 'TEXT');
if (!toneNode) return { error: '#tone が見つからない' };
const tone = JSON.parse(toneNode.characters);
if (tone.meta.locked && tone.meta.locked.brand_palette) return { skipped: 'brand_palette 固定の系統(色は替えない)' };
const R = tone.palette.roles;
const rgb = h => ({ r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255, b: parseInt(h.slice(5, 7), 16) / 255 });
const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v * 255).toString(16).padStart(2, '0')).join('').toUpperCase();
const same = (a, b) => Math.abs(a.r - b.r) <= CONFIG.TOL && Math.abs(a.g - b.g) <= CONFIG.TOL && Math.abs(a.b - b.b) <= CONFIG.TOL;
const lum = c => { const f = v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
const MAP = Object.entries(CONFIG.MAP_BY_FAMILY[CONFIG.FAMILY] || {}).map(([from, role]) => ({ from: rgb(from), to: rgb(R[role]), role })).filter(m => !same(m.from, m.to));
const MAIN = rgb(R.main), CTA = rgb(R.cta);
const swap = c => { for (const m of MAP) if (same(c, m.from)) return m; return null; };
function swapPaints(paints, count) {
  if (!Array.isArray(paints)) return null; let hit = false;
  const next = paints.map(p => {
    if (p.type === 'SOLID') { const m = swap(p.color); if (m) { hit = true; count[m.role] = (count[m.role] || 0) + 1; return Object.assign({}, p, { color: m.to }); } }
    if (p.type && p.type.startsWith('GRADIENT')) { let g = false; const stops = p.gradientStops.map(s => { const m = swap(s.color); if (m) { g = true; return Object.assign({}, s, { color: Object.assign({}, m.to, { a: s.color.a }) }); } return s; }); if (g) { hit = true; count.gradient = (count.gradient || 0) + 1; return Object.assign({}, p, { gradientStops: stops }); } }
    return p;
  });
  return hit ? next : null;
}
const fontLoaded = new Set();
async function loadSegFonts(n) { for (const s of n.getStyledTextSegments(['fontName'])) { const k = s.fontName.family + '|' + s.fontName.style; if (!fontLoaded.has(k)) { await figma.loadFontAsync(s.fontName); fontLoaded.add(k); } } }
function onCoverFace(n, frame) { let p = n.parent; while (p && p !== frame) { if ((p.name || '').startsWith('面:表紙面')) return true; p = p.parent; } return false; }
const inter = (a, b) => { const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x); const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y); return (w > 0 && h > 0) ? w * h : 0; };

const report = [];
for (const fid of CONFIG.FRAME_IDS) {
  const frame = await figma.getNodeByIdAsync(fid);
  const count = { fills: 0, strokes: 0, textSegs: 0, cta: 0, ctaFaces: 0, errors: [] };
  const nodes = [frame, ...frame.findAll(() => true)];
  // (1) 濃淡 2 群
  for (const n of nodes) {
    if (n.type === 'TEXT') {
      try {
        const segs = n.getStyledTextSegments(['fills']); let loaded = false;
        for (const s of segs) { const nf = swapPaints(s.fills, count); if (nf) { if (!loaded) { await loadSegFonts(n); loaded = true; } n.setRangeFills(s.start, s.end, nf); count.textSegs++; } }
      } catch (e) { count.errors.push(n.name.slice(0, 16) + ': ' + String(e).slice(0, 40)); }
      const ns = swapPaints(n.strokes, count); if (ns) { n.strokes = ns; count.strokes++; }
      continue;
    }
    if ('fills' in n && n.fills !== figma.mixed) { const nf = swapPaints(n.fills, count); if (nf) { n.fills = nf; count.fills++; } }
    if ('strokes' in n) { const ns = swapPaints(n.strokes, count); if (ns) { n.strokes = ns; count.strokes++; } }
  }
  // (2) 電話・CTA 見出しの文字
  for (const n of nodes) {
    if (n.type !== 'TEXT' || !onCoverFace(n, frame) || !CONFIG.CTA_TEXT.some(re => re.test(n.name))) continue;
    await loadSegFonts(n);
    const isPhone = /^#電話:/.test(n.name);
    for (const s of n.getStyledTextSegments(['fills'])) {
      const f = s.fills && s.fills[s.fills.length - 1];
      if (!f || f.type !== 'SOLID') continue;
      if (isPhone ? lum(f.color) < CONFIG.WHITE_LUM : same(f.color, MAIN)) { n.setRangeFills(s.start, s.end, [Object.assign({}, f, { color: CTA })]); count.cta++; }
    }
  }
  // (3) 白い文字が載る main 色の面 → cta
  const order = nodes.filter(n => n.visible !== false && n.absoluteBoundingBox);
  const maxArea = (Math.min(frame.width, frame.height) / 3) * (Math.max(frame.width, frame.height) / 2) * CONFIG.MAX_FACE_RATIO;
  const faces = order.map((n, i) => ({ n, i })).filter(({ n }) => n.type !== 'TEXT' && n.absoluteBoundingBox.width * n.absoluteBoundingBox.height <= maxArea && 'fills' in n && Array.isArray(n.fills) && n.fills.some(p => p.type === 'SOLID' && p.visible !== false && (p.opacity == null || p.opacity > 0.99) && same(p.color, MAIN)));
  const changed = new Set();
  order.forEach((t, ti) => {
    if (t.type !== 'TEXT' || !(t.characters || '').trim()) return;
    const segs = t.getStyledTextSegments(['fills']);
    if (!segs.every(s => { const f = s.fills && s.fills[s.fills.length - 1]; return f && f.type === 'SOLID' && lum(f.color) >= CONFIG.WHITE_LUM; })) return;
    const tb = t.absoluteBoundingBox, ta = tb.width * tb.height;
    let top = null; for (const f of faces) if (f.i < ti && inter(f.n.absoluteBoundingBox, tb) / ta >= CONFIG.COVER) top = f;
    if (top && !changed.has(top.n.id)) {
      top.n.fills = top.n.fills.map(p => p.type === 'SOLID' && same(p.color, MAIN) ? Object.assign({}, p, { color: CTA }) : p);
      changed.add(top.n.id); count.ctaFaces++;
    }
  });
  count.ctaFaceNames = [...changed].slice(0, 8).map(id => order.find(n => n.id === id).name.slice(0, 20));
  count.errors = count.errors.slice(0, 8);
  report.push(Object.assign({ frame: frame.name }, count));
}
return { tone: tone.meta.library.base_id, map: MAP.map(m => `${hex(m.from)}→${hex(m.to)}(${m.role})`), cta: R.cta, report };
