// autofix.js — Step 4 の自動修正 1 回分(use_figma にそのまま貼る。先頭 CONFIG だけ書き換える)
// preflight.js の返り値の sev=Fail の items を ITEMS に写して実行する。機械的に直せるものだけ直し、残りは handoff に返す。
//   P3-a あふれ   → 箱の高さを文字に合わせる(一時 clone で HEIGHT 計測)。伸ばすと面境界の折り線にかかるなら戻して引き渡し
//   P2  文字が小さい → 小さいセグメントだけ limit の Fail 線(px)まで上げる → あふれたら箱の高さも合わせる
//   P6  折り線      → 箱が字面より広い場合だけ、箱の幅を字面に縮める(揃え位置は保つ)。字面がかかっているなら引き渡し
//   P4  コントラスト → 白い文字の下の面が main 色なら cta 色に。それ以外は引き渡し
//   P1・P3-b・P7・P12 ほか → 引き渡し(寸法違い・枠はみ出し・仮の文言・電話の大きさは文言や組みの判断が要る)
// 回転ノードでも本体の textAutoResize は切り替えない。位置は relativeTransform、大きさは resize だけで動かす。

const CONFIG = {
  PAGE_ID: '7:2',
  FRAME_ID: '0:0',
  KIND: 'cover',                  // 'cover' | 'inner'
  TONE_FRAME_ID: null,            // #tone を持つフレーム(null = FRAME_ID)
  ITEMS: [                        // preflight の Fail items: { check, node, limit? }
    // { check: 'P3-a', node: '123:45' }, { check: 'P2', node: '123:46', limit: '18px/20px(note)' },
  ],
  FOLD_MM: { fail: 5, warn: 8 },
  TMP_NAME: '__autofix_tmp__',
};

const page = await figma.getNodeByIdAsync(CONFIG.PAGE_ID);
await figma.setCurrentPageAsync(page);
const frame = await figma.getNodeByIdAsync(CONFIG.FRAME_ID);
const holder = await figma.getNodeByIdAsync(CONFIG.TONE_FRAME_ID || CONFIG.FRAME_ID);
const toneNode = holder && holder.findOne(n => n.name === '#tone' && n.type === 'TEXT');
const tone = toneNode ? JSON.parse(toneNode.characters) : null;
const rgb = h => ({ r: parseInt(h.slice(1, 3), 16) / 255, g: parseInt(h.slice(3, 5), 16) / 255, b: parseInt(h.slice(5, 7), 16) / 255 });
const same = (a, b) => Math.abs(a.r - b.r) <= 1.5 / 255 && Math.abs(a.g - b.g) <= 1.5 / 255 && Math.abs(a.b - b.b) <= 1.5 / 255;
const lum = c => { const f = v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
const contrast = (a, b) => { const l1 = lum(a), l2 = lum(b); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
const round1 = v => Math.round(v * 10) / 10;
const cut = (s, n) => (s || '').replace(/\s+/g, ' ').slice(0, n);
const inter = (a, b) => { const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x); const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y); return (w > 0 && h > 0) ? w * h : 0; };

// 折り線(設計座標)
const [[fa, fc, fe], [fb, fd, ff]] = frame.absoluteTransform; const det = fa * fd - fb * fc;
const toLocal = (px, py) => ({ x: (fd * (px - fe) - fc * (py - ff)) / det, y: (-fb * (px - fe) + fa * (py - ff)) / det });
const W = frame.width, H = frame.height, k = Math.min(W, H) / 297, portrait = H >= W;
const folds = portrait ? [{ axis: 'x', v: W / 3, kind: 'spread' }, { axis: 'x', v: W * 2 / 3, kind: CONFIG.KIND === 'cover' ? 'boundary' : 'spread' }, { axis: 'y', v: H / 2, kind: CONFIG.KIND === 'cover' ? 'boundary' : 'spread' }]
                       : [{ axis: 'y', v: H / 3, kind: 'spread' }, { axis: 'y', v: H * 2 / 3, kind: 'spread' }, { axis: 'x', v: W / 2, kind: 'spread' }];
function foldSev(n) {
  const b = n.absoluteBoundingBox; const p = toLocal(b.x, b.y), q = toLocal(b.x + b.width, b.y + b.height);
  const box = { x0: Math.min(p.x, q.x), x1: Math.max(p.x, q.x), y0: Math.min(p.y, q.y), y1: Math.max(p.y, q.y) };
  let sev = null;
  for (const f of folds) {
    const lo = f.axis === 'x' ? box.x0 : box.y0, hi = f.axis === 'x' ? box.x1 : box.y1;
    const cross = f.v > lo && f.v < hi, gap = cross ? 0 : Math.min(Math.abs(lo - f.v), Math.abs(hi - f.v));
    if (f.kind === 'boundary' && (cross || gap < CONFIG.FOLD_MM.fail * k)) return 'Fail';
    if ((f.kind === 'boundary' && gap < CONFIG.FOLD_MM.warn * k) || (f.kind === 'spread' && cross)) sev = 'Warn';
  }
  return sev;
}
async function loadFonts(n) { for (const s of n.getStyledTextSegments(['fontName'])) await figma.loadFontAsync(s.fontName); }
function measure(n) { let c = null; try { c = n.clone(); c.name = CONFIG.TMP_NAME; c.visible = false; c.textAutoResize = 'HEIGHT'; const hFit = c.height; c.textAutoResize = 'WIDTH_AND_HEIGHT'; return { hFit, wNat: c.width, hNat: c.height }; } finally { if (c) c.remove(); } }
function growHeight(n) { // 高さを文字に合わせる。面境界にかかるなら戻す
  if (n.textAutoResize !== 'NONE') return { ok: true, note: 'auto' };
  const m = measure(n); if (m.hFit <= n.height + 1) return { ok: true, note: 'fits' };
  const h0 = n.height; n.resize(n.width, Math.ceil(m.hFit));
  if (foldSev(n) === 'Fail') { n.resize(n.width, h0); return { ok: false, why: `箱を ${Math.ceil(m.hFit)}px に伸ばすと面境界の折り線にかかる` }; }
  return { ok: true, note: `h ${round1(h0)}→${Math.ceil(m.hFit)}` };
}
function shiftLocalX(n, dx) { const m = n.relativeTransform; n.relativeTransform = [[m[0][0], m[0][1], m[0][2] + m[0][0] * dx], [m[1][0], m[1][1], m[1][2] + m[1][0] * dx]]; }

const fixed = [], handoff = [], seen = new Set();
const all = [frame, ...frame.findAll(() => true)].filter(n => n.visible !== false);
for (const it of CONFIG.ITEMS) {
  const key = it.check + it.node; if (seen.has(key)) continue; seen.add(key);
  const n = it.node ? await figma.getNodeByIdAsync(it.node) : null;
  const label = n ? cut(n.name, 20) : '-';
  try {
    if (it.check === 'P3-a' && n && n.type === 'TEXT') {
      await loadFonts(n); const r = growHeight(n);
      (r.ok ? fixed : handoff).push({ check: it.check, node: it.node, name: label, what: r.ok ? '箱の高さを文字に合わせた ' + r.note : r.why + '。文言を短くする' });
    } else if (it.check === 'P2' && n && n.type === 'TEXT') {
      const px = parseFloat(String(it.limit || '').match(/([\d.]+)px/)[1]);
      await loadFonts(n); let raised = 0;
      for (const s of n.getStyledTextSegments(['fontSize'])) if (s.fontSize < px) { n.setRangeFontSize(s.start, s.end, px); raised++; }
      const r = growHeight(n);
      if (!r.ok) handoff.push({ check: it.check, node: it.node, name: label, what: `文字を ${px}px にしたが ` + r.why + '。文言を短くする' });
      else fixed.push({ check: it.check, node: it.node, name: label, what: `小さい文字 ${raised} か所を ${px}px に` + (r.note && r.note !== 'fits' ? '、' + r.note : '') });
    } else if (it.check === 'P6' && n && n.type === 'TEXT' && n.textAutoResize === 'NONE') {
      await loadFonts(n); const m = measure(n);
      if (m.hFit > m.hNat + 1 || m.wNat >= n.width - 2) { handoff.push({ check: it.check, node: it.node, name: label, what: '文字そのものが折り線にかかる。文言を短くするか配置を直す' }); continue; }
      const w0 = n.width, nw = Math.ceil(m.wNat) + 2, al = n.textAlignHorizontal;
      const dx = al === 'CENTER' ? (w0 - nw) / 2 : al === 'RIGHT' ? w0 - nw : 0;
      const rt0 = n.relativeTransform;
      n.resize(nw, n.height); if (dx) shiftLocalX(n, dx);
      const s2 = foldSev(n);
      if (s2 === 'Fail') { n.resize(w0, n.height); n.relativeTransform = rt0; handoff.push({ check: it.check, node: it.node, name: label, what: '箱を字面に縮めても折り線にかかる' }); }
      else fixed.push({ check: it.check, node: it.node, name: label, what: `箱の幅を字面に合わせた ${round1(w0)}→${nw}` + (s2 ? '(△は残る)' : '') });
    } else if (it.check === 'P4' && n && n.type === 'TEXT' && tone) {
      const MAIN = rgb(tone.palette.roles.main), CTA = rgb(tone.palette.roles.cta);
      const segs = n.getStyledTextSegments(['fills']);
      const white = segs.every(s => { const f = s.fills && s.fills[s.fills.length - 1]; return f && f.type === 'SOLID' && lum(f.color) >= 0.85; });
      const tb = n.absoluteBoundingBox, ta = tb.width * tb.height, ti = all.indexOf(n);
      let bg = null; for (let i = 0; i < ti; i++) { const c = all[i]; if (c.type === 'TEXT' || !c.absoluteBoundingBox || !Array.isArray(c.fills)) continue; const f = c.fills.filter(p => p.visible !== false).slice(-1)[0]; if (f && f.type === 'SOLID' && inter(c.absoluteBoundingBox, tb) / ta >= 0.9) bg = c; }
      const bgf = bg && bg.fills.filter(p => p.visible !== false).slice(-1)[0];
      if (white && bgf && same(bgf.color, MAIN) && contrast({ r: 1, g: 1, b: 1 }, CTA) >= 7) { bg.fills = bg.fills.map(p => p === bgf ? Object.assign({}, p, { color: CTA }) : p); fixed.push({ check: it.check, node: it.node, name: label, what: `下の面 ${cut(bg.name, 16)} を cta 色に` }); }
      else handoff.push({ check: it.check, node: it.node, name: label, what: '文字と背景の色の差が足りない(色の組み合わせを人が判断)' });
    } else {
      handoff.push({ check: it.check, node: it.node, name: label, what: { P1: '寸法が違う(複製からやり直し)', P7: '仮の文言が残っている(実際の内容を入れる)', P12: '電話番号が小さい(組みの判断が要る)', P6: '折り線にかかる(配置の判断が要る)', 'P3-b': '文字が枠からはみ出す(文言を短くする・改行を外す・枠を広げるのどれかを人が判断)' }[it.check] || '自動では直せない' });
    }
  } catch (e) { handoff.push({ check: it.check, node: it.node, name: label, what: 'エラー: ' + String(e).slice(0, 60) }); }
}
let tmpLeft = 0; for (const t of frame.findAllWithCriteria({ types: ['TEXT'] })) if (t.name === CONFIG.TMP_NAME) { tmpLeft++; t.remove(); }
return { frame: frame.name, fixed: fixed.slice(0, 40), handoff: handoff.slice(0, 40), tmpLeft };
