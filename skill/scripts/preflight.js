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
  TIGHT_BOX: 'ignore',               // P3-a 折り返しが増えず箱だけ低い(単行バッジ等): 'ignore'|'manual'|'fail'
  P6_SKIP_FOLDS: { x: [], y: [] },   // P6 で検査しない折り線(設計座標px。例: 2面見開きの中央 x:[563.7])
  PHONE_RATIO: 3,                    // P12 電話 ≥ 本文中央値 × 3
  P6_EXCLUDE_NAME: /^(ガイド:|装飾:)/,          // P6 で無視する TEXT 名
  P7_PATTERN: /[〇○◯]{2,}|[〇○◯](?=年|月|日|時|号|地区|市|町|村)|0000|[（(]仮[)）]|ダミー|サンプル|XXX|TODO/,
  P7_EXCLUDE_NAME: /^サンプル:/,                 // テンプレの見本文言は除外
  EXCLUDE_NAME: /^#(tone|state|config)$/,      // 状態保持ノードは走査から除外
  // 役割判定: 名前が #本文 等で始まれば優先。次に名前の正規表現、最後に文字列
  ROLE_PREFIX: { '#本文': 'body', '#注記': 'note', '#見出し': 'heading', '#電話': 'phone', '#CTA': 'heading' },
  ROLE_NAME: [
    ['note',    /注記|注意|受付時間|補助金表記|発行者情報|事業主体|運行事業者|協力会社|実施主体|更新\)|^※|※/],
    ['phone',   /電話番号|(^|[^a-zA-Z])TEL($|[^a-zA-Z])|℡/],
    ['heading', /見出し|キャッチコピー|サブコピー|サービス名|タイトル|自治体名|事業名|^見出し:|^ラベル:見出し|分類\d/],
    ['body',    /本文|リード文|名称|停留所名|スポット名|乗降場所\d|リスト|説明|キャプション|手順/],
  ],
  ROLE_CHARS: [
    ['phone', /0\d{1,4}[-‐−ー–]\d{1,4}[-‐−ー–]\d{3,4}/],
    ['note',  /^※/],
  ],
  MAX_ITEMS: 20, NAME_LEN: 20, CHARS_LEN: 15, OUT_LIMIT: 20000,
  TMP_NAME: '__preflight_tmp__',
};

// ---------- 共通ユーティリティ ----------
const t0 = Date.now();
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
  for (const p in CONFIG.ROLE_PREFIX) if (name.startsWith(p)) return { role: CONFIG.ROLE_PREFIX[p], by: 'prefix' };
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
        c.textAutoResize = 'WIDTH_AND_HEIGHT'; const hNat = c.height;   // 自然高さ(明示改行のみ)
        c.textAutoResize = 'HEIGHT'; const hFit = c.height;             // 箱幅で折り返した高さ
        checked++;
        const diff = hFit - n.height;
        if (diff > CONFIG.OVERFLOW_TOL_PX) {
          const wrapped = hFit > hNat + 1;
          if (wrapped || CONFIG.TIGHT_BOX === 'fail') { fails++; items.push(item(n, { role: m.role, value: `${wrapped ? 'あふれ' : 'tight'} need ${round1(hFit)}px / box ${round1(n.height)}px (+${round1(diff)})`, limit: `+${CONFIG.OVERFLOW_TOL_PX}px`, chars: cut(n.characters, CONFIG.CHARS_LEN), fix: '文言を短くする(箱・フォントは変えない)' })); }
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
