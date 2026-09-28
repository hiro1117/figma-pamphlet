// fill-text.js — Step 3-1 書体と文言の流し込み(use_figma にそのまま貼る。先頭 CONFIG だけ書き換える)
// 順序: (A1) 欠落フォントの置き換え(フレーム全体)→ (A2) 表紙面の #見出し を見出し書体に → (A3) 表紙面の #電話 を数字書体に
//       → (B) SLOTS の文言を流し込む(明示改行を外す → 箱幅で折り返し → 一時 clone で高さを測る → 足りなければ箱を伸ばす → 折り線との距離を確認)
//       電話番号は改行を外して 1 行にし、箱幅に収まらなければ文字サイズを縮める。
// 回転ノード(180° の面・180° のフレーム)で本体の textAutoResize は切り替えない。計測は一時 clone(try/finally で必ず削除)。
// 返り値: { fonts, slots:[{name,id,status,...}], handoff:[...] }。20KB 以内。

const CONFIG = {
  PAGE_ID: '7:2',
  FRAME_ID: '0:0',              // 表紙 or 中面のフレーム
  KIND: 'cover',                // 'cover' | 'inner'(折り線の種別: 表紙は x=1127.3・y=1196 が面境界、中面は全部見開き内)
  TONE_FRAME_ID: null,          // #tone を持つフレーム(null = FRAME_ID 自身。中面を処理するときは表紙の id)
  SLOTS: {                      // 名前 → 文言。同名が複数あれば全部に同じ文言。配列なら上から順に 1 つずつ。{ text, keepBreaks: true } で改行を残す
    // '#見出し:サービス名': 'のりあい号',
    // '#電話:メイン': '050-0000-0000',
  },
  KEEP_BREAKS_PREFIX: ['#見出し', '#CTA', '#STEP'], // 既定で改行を残す枠(短い見出し・手順)。本文・注記・電話は外す
  PHONE_NAME: /^#電話(?!.*(受付|時間|注記|説明))|電話番号/,  // 電話番号の枠(1 行化・縮小の対象)
  ONE_LINE: [/^#見出し:サービス名/, /^#見出し:タイトル行/, /^#見出し:中面タイトル/],    // 電話番号と同じく 1 行に収める枠(題字・中面タイトル。2 行にしない)
  MAX_RIGHT: {},                // 自動幅の枠が伸びてよい右端(設計座標 px)を枠ごとに指定。例 { '#見出し:サービス名': 1490 }(右隣のロゴを避ける)
  HEADLINE_ON_COVER: true,      // 表紙面(面:表紙面…)の #見出し:* を tone の見出し書体に(MITT = brand_palette 固定の系統は触らない)
  NUMERALS_ON_COVER: true,      // 表紙面の #電話:* を tone の数字書体に
  FORCE_MIXED: false,           // 書式が混ざった枠(サイズ・色が途中で変わる)にも文言を入れるか。入れると先頭の書式に揃う
  GROW_BOX: true,               // 高さが足りなければ箱を伸ばす(伸ばして面境界にかかるようになる場合は伸ばさず引き渡し)
  MIN_SHRINK: 0.8,              // 縮めて収めたとき、これより小さくなったら引き渡しにも載せる
  EDGE_MM: { fold: 8, trim: 5 },// 自動幅の枠が伸びてよい範囲: 面境界の折り線から 8mm、仕上がり端から 5mm 手前まで
  FOLD_MM: { fail: 5, warn: 8 },
  NOTO_STYLE: { Thin: 'Thin', ExtraLight: 'Light', Light: 'Light', DemiLight: 'DemiLight', Normal: 'Regular', Regular: 'Regular', Medium: 'Medium', SemiBold: 'Bold', Bold: 'Bold', ExtraBold: 'Black', Heavy: 'Black', Black: 'Black', W3: 'Regular', W4: 'Regular', W5: 'Medium', W6: 'Bold', W7: 'Bold', W8: 'Black', W9: 'Black' },
  TMP_NAME: '__filltext_tmp__',
};

const t0 = Date.now();
const page = await figma.getNodeByIdAsync(CONFIG.PAGE_ID);
await figma.setCurrentPageAsync(page);
const frame = await figma.getNodeByIdAsync(CONFIG.FRAME_ID);
if (!frame) return { error: 'FRAME_ID not found' };
const toneHolder = CONFIG.TONE_FRAME_ID ? await figma.getNodeByIdAsync(CONFIG.TONE_FRAME_ID) : frame;
const toneNode = toneHolder && toneHolder.findOne(n => n.name === '#tone' && n.type === 'TEXT');
const tone = toneNode ? JSON.parse(toneNode.characters) : null;
const locked = !!(tone && tone.meta && tone.meta.locked && tone.meta.locked.brand_palette);
const HEAD = tone ? { family: tone.typography.headline.family, style: tone.typography.headline.weight } : { family: 'Noto Sans JP', style: 'Black' };
const NUM = tone ? { family: tone.typography.numerals.family, style: tone.typography.numerals.weight } : { family: 'Noto Sans JP', style: 'Black' };
const round1 = v => Math.round(v * 10) / 10;
const cut = (s, n) => (s || '').replace(/\s+/g, ' ').slice(0, n);
const NL = new RegExp('[ \\t]*(\\r?\\n|' + String.fromCharCode(8232) + ')[ \\t]*', 'g');   // U+2028 はリテラルで書くと転送で壊れる

// フォントの読み込み(可否をキャッシュ)
const fontOk = new Map();
async function load(f) { const k = f.family + '|' + f.style; if (!fontOk.has(k)) { try { await figma.loadFontAsync(f); fontOk.set(k, true); } catch (e) { fontOk.set(k, false); } } return fontOk.get(k); }
async function loadAll(n) { const segs = n.getStyledTextSegments(['fontName']); for (const s of segs) await load(s.fontName); return segs; }
function onCoverFace(n) { let p = n.parent; while (p && p !== frame) { if ((p.name || '').startsWith('面:表紙面')) return true; p = p.parent; } return false; }
function isRotated(n) { let p = n; while (p) { const m = p.relativeTransform; if (Math.abs(m[0][0] - 1) > 1e-6 || Math.abs(m[0][1]) > 1e-6) return true; if (p === frame) break; p = p.parent; } return false; }
async function replaceFont(n, pickTarget) { // セグメントごとに置換先を決める(null = そのまま)
  const segs = n.getStyledTextSegments(['fontName']); const plan = []; let changed = 0, anyMissing = false;
  for (const s of segs) {
    const ok = await load(s.fontName); if (!ok) anyMissing = true;
    const target = pickTarget(s.fontName, ok) || s.fontName;
    if (!(await load(target))) return { error: 'font load failed ' + target.family + ' ' + target.style };
    if (target.family !== s.fontName.family || target.style !== s.fontName.style) changed++;
    plan.push([s.start, s.end, target]);
  }
  if (!changed) return { changed };
  // 読めない書体が残っていると一部の範囲だけは書き換えられない → 先に全体を 1 書体にしてから、範囲ごとに当て直す
  if (anyMissing) n.fontName = plan[0][2];
  for (const [a, b, f] of plan) n.setRangeFontName(a, b, f);
  return { changed };
}

// ---------- A1 欠落フォントの置き換え(フレーム全体) ----------
const fonts = { missing: 0, replaced: [], headline: 0, numerals: 0, errors: [] };
const texts = frame.findAllWithCriteria({ types: ['TEXT'] }).filter(n => !CONFIG.TMP_NAME || n.name !== CONFIG.TMP_NAME);
for (const n of texts) {
  if (!n.hasMissingFont) continue;
  fonts.missing++;
  const isHead = (n.name || '').startsWith('#見出し');
  const isPhone = CONFIG.PHONE_NAME.test(n.name || '') || /^(ラベル:)?(TEL|LINE|FAX)/i.test(n.name || '');
  const r = await replaceFont(n, (f, ok) => ok ? null : isHead ? HEAD : isPhone ? NUM : { family: 'Noto Sans JP', style: CONFIG.NOTO_STYLE[f.style] || 'Regular' });
  if (r.error) fonts.errors.push({ id: n.id, name: cut(n.name, 20), e: r.error }); else fonts.replaced.push(cut(n.name, 20));
}
// ---------- A2/A3 表紙面の見出し書体・数字書体 ----------
if (CONFIG.KIND === 'cover' && !locked) {
  for (const n of texts) {
    if (!onCoverFace(n) || !(n.characters || '').trim()) continue;
    const nm = n.name || '';
    if (CONFIG.HEADLINE_ON_COVER && nm.startsWith('#見出し')) { const r = await replaceFont(n, () => HEAD); if (r.error) fonts.errors.push({ id: n.id, e: r.error }); else if (r.changed) fonts.headline++; }
    else if (CONFIG.NUMERALS_ON_COVER && nm.startsWith('#電話')) { const r = await replaceFont(n, () => NUM); if (r.error) fonts.errors.push({ id: n.id, e: r.error }); else if (r.changed) fonts.numerals++; }
  }
}
if (fonts.replaced.length > 12) { fonts.replacedMore = fonts.replaced.length - 12; fonts.replaced = fonts.replaced.slice(0, 12); }

// ---------- 折り線(設計座標) ----------
const fbb = frame.absoluteBoundingBox;
const [[fa, fc, fe], [fb, fd, ff]] = frame.absoluteTransform;
const det = fa * fd - fb * fc;
const toLocal = (px, py) => ({ x: (fd * (px - fe) - fc * (py - ff)) / det, y: (-fb * (px - fe) + fa * (py - ff)) / det });
const W = frame.width, H = frame.height, k = Math.min(W, H) / 297;
const portrait = H >= W;
const folds = portrait ? [{ axis: 'x', v: W / 3, kind: 'spread' }, { axis: 'x', v: W * 2 / 3, kind: CONFIG.KIND === 'cover' ? 'boundary' : 'spread' }, { axis: 'y', v: H / 2, kind: CONFIG.KIND === 'cover' ? 'boundary' : 'spread' }]
                       : [{ axis: 'y', v: H / 3, kind: 'spread' }, { axis: 'y', v: H * 2 / 3, kind: 'spread' }, { axis: 'x', v: W / 2, kind: 'spread' }];
function foldCheck(n) {       // 字面(描画範囲)で見る。箱の余白は見ない
  const b = n.absoluteRenderBounds || n.absoluteBoundingBox; if (!b) return { sev: null };
  const p = toLocal(b.x, b.y), q = toLocal(b.x + b.width, b.y + b.height);
  const box = { x0: Math.min(p.x, q.x), x1: Math.max(p.x, q.x), y0: Math.min(p.y, q.y), y1: Math.max(p.y, q.y) };
  let sev = null, worst = null;
  for (const f of folds) {
    const lo = f.axis === 'x' ? box.x0 : box.y0, hi = f.axis === 'x' ? box.x1 : box.y1;
    const cross = f.v > lo && f.v < hi, gap = cross ? 0 : Math.min(Math.abs(lo - f.v), Math.abs(hi - f.v));
    let s = null;
    if (f.kind === 'boundary') s = cross || gap < CONFIG.FOLD_MM.fail * k ? 'Fail' : gap < CONFIG.FOLD_MM.warn * k ? 'Warn' : null;
    else if (cross) s = 'Warn';
    if (s && (!sev || s === 'Fail')) { sev = s; worst = `${f.axis}=${round1(f.v)} ${f.kind === 'boundary' ? '面境界' : '見開き'} ${cross ? 'またぎ' : 'gap ' + round1(gap)}`; }
  }
  return { sev, at: worst };
}
// 一時 clone で高さ(箱幅で折り返し)・自然幅を測る
function measure(n) {
  let c = null;
  try {
    c = n.clone(); c.name = CONFIG.TMP_NAME; c.visible = false;
    c.textAutoResize = 'HEIGHT'; const hFit = c.height;
    c.textAutoResize = 'WIDTH_AND_HEIGHT'; const wNat = c.width, hNat = c.height;
    return { hFit, wNat, hNat };
  } finally { if (c) c.remove(); }
}

// ---------- B 文言の流し込み ----------
const slots = [], handoff = [];
const byName = {};
for (const n of texts) if (CONFIG.SLOTS[n.name] !== undefined) (byName[n.name] = byName[n.name] || []).push(n);
for (const name of Object.keys(CONFIG.SLOTS)) {
  const nodes = byName[name];
  if (!nodes) { slots.push({ name: cut(name, 24), status: 'no-slot' }); handoff.push({ name, why: 'テンプレに枠が無い(文言は入れていない)' }); continue; }
  const isPhone = CONFIG.PHONE_NAME.test(name), oneLine = isPhone || CONFIG.ONE_LINE.some(re => re.test(name));
  const values = Array.isArray(CONFIG.SLOTS[name]) ? CONFIG.SLOTS[name] : nodes.map(() => CONFIG.SLOTS[name]);
  // 配列のときは読む順(枠自身の向きで上→下、左→右。逆さ面・180° のフレームでも見た目どおり)
  const m0 = nodes[0].absoluteTransform, pos = n => { const q = n.absoluteBoundingBox, cx = q.x + q.width / 2, cy = q.y + q.height / 2; return { x: cx * m0[0][0] + cy * m0[1][0], y: cx * m0[0][1] + cy * m0[1][1] }; };
  if (Array.isArray(CONFIG.SLOTS[name])) nodes.sort((a, b) => (Math.abs(pos(a).y - pos(b).y) > 2 ? pos(a).y - pos(b).y : pos(a).x - pos(b).x));
  for (let i = 0; i < nodes.length; i++) {
    const n = nodes[i], v = values[i];
    if (v === undefined || v === null) continue;
    const keep = typeof v === 'object' ? !!v.keepBreaks : CONFIG.KEEP_BREAKS_PREFIX.some(p => name.startsWith(p));
    let text = typeof v === 'object' ? v.text : String(v);
    if (oneLine || !keep) text = text.replace(NL, '');
    const r = { name: cut(name, 24), id: n.id };
    const segs = n.getStyledTextSegments(['fontName', 'fontSize', 'fills']);
    const mixed = new Set(segs.map(s => s.fontName.family + s.fontName.style + s.fontSize + JSON.stringify(s.fills))).size > 1;
    if (mixed && !CONFIG.FORCE_MIXED && !oneLine) { r.status = 'skip-mixed'; slots.push(r); handoff.push({ name, id: n.id, why: '書式が混ざった枠。文言を替えると書式が1つになるため入れていない' }); continue; }
    for (const s of segs) if (!(await load(s.fontName))) { r.status = 'font-missing'; break; }
    if (r.status) { slots.push(r); handoff.push({ name, id: n.id, why: 'フォントを読み込めない' }); continue; }
    const before = { h: n.height, w: n.width, size: segs[0].fontSize, fold: foldCheck(n).sev };
    n.characters = text;
    r.status = 'ok'; r.chars = cut(text, 15);
    if (n.textAutoResize === 'NONE') {
      const m = measure(n);
      if (oneLine) {                     // 1 行に収める。はみ出すなら縮小
        let size = before.size;
        if (m.wNat > n.width + 0.5) {
          size = Math.floor(before.size * n.width / m.wNat * 0.98 * 10) / 10;
          n.setRangeFontSize(0, n.characters.length, size);
          r.resized = `${before.size}→${size}px`;
        }
        const m2 = measure(n);   // 行送りが箱より高い設計があるので、高さではなく「箱幅で折り返したか」で見る
        if (m2.hFit > m2.hNat + 1) { r.status = 'overflow'; handoff.push({ name, id: n.id, why: '1 行に収まらない' }); }
        if (r.resized && size / before.size < CONFIG.MIN_SHRINK) handoff.push({ name, id: n.id, why: `文字を ${Math.round(size / before.size * 100)}% まで縮めた。文言を短くしたほうがよい` });
      } else if (m.hFit > n.height + 1) {
        r.need = round1(m.hFit); r.box = round1(n.height);
        if (CONFIG.GROW_BOX) {
          const h0 = n.height; n.resize(n.width, Math.ceil(m.hFit));
          const fc2 = foldCheck(n);
          if (fc2.sev === 'Fail' && before.fold !== 'Fail') { n.resize(n.width, h0); r.status = 'overflow'; handoff.push({ name, id: n.id, why: `文字が箱に収まらず、箱を伸ばすと折り線にかかる(${fc2.at})。文言を短くする` }); }
          else { r.status = 'grown'; r.grownTo = Math.ceil(m.hFit); if (isRotated(n)) r.rotated = true; }
        } else { r.status = 'overflow'; handoff.push({ name, id: n.id, why: `文字が箱に収まらない(need ${r.need} / box ${r.box})` }); }
      }
    } else if (n.textAutoResize === 'WIDTH_AND_HEIGHT' && n.width > before.w + 1 && portrait) {
      // 自動幅の枠(見出しなど)が伸びた → 伸びてよい右端(面境界の折り線 −8mm / 仕上がり端 −5mm / MAX_RIGHT)を超えたら文字サイズを比例で縮める
      const q = n.absoluteRenderBounds || n.absoluteBoundingBox, p0 = toLocal(q.x, q.y), p1 = toLocal(q.x + q.width, q.y + q.height);
      const x0 = Math.min(p0.x, p1.x), x1 = Math.max(p0.x, p1.x);
      let limit = CONFIG.MAX_RIGHT[name] || (W - CONFIG.EDGE_MM.trim * k);
      if (!CONFIG.MAX_RIGHT[name]) for (const f of folds) if (f.axis === 'x' && f.kind === 'boundary' && f.v > x0) limit = Math.min(limit, f.v - CONFIG.EDGE_MM.fold * k);
      if (x1 > limit) {
        const f = (limit - x0) / (x1 - x0) * 0.99;
        for (const s of n.getStyledTextSegments(['fontSize'])) n.setRangeFontSize(s.start, s.end, Math.floor(s.fontSize * f * 10) / 10);
        r.resized = `×${Math.round(f * 100) / 100}(右端 ${round1(limit)} に収める)`;
        if (f < CONFIG.MIN_SHRINK) handoff.push({ name, id: n.id, why: `文字を ${Math.round(f * 100)}% まで縮めた。文言を短くしたほうがよい` });
      }
    }
    const fc = foldCheck(n);
    if (fc.sev) { r.fold = fc.sev + ' ' + fc.at; if (fc.sev === 'Fail') handoff.push({ name, id: n.id, why: '折り線にかかる: ' + fc.at }); }
    slots.push(r);
  }
}
// 一時 clone の残骸を掃く
let tmpLeft = 0; for (const n of frame.findAllWithCriteria({ types: ['TEXT'] })) if (n.name === CONFIG.TMP_NAME) { tmpLeft++; n.remove(); }
return { frame: frame.name, tone: tone ? tone.meta.library.base_id : null, locked, fonts, slots: slots.slice(0, 60), slotsMore: Math.max(0, slots.length - 60), handoff: handoff.slice(0, 30), tmpLeft, ms: Date.now() - t0 };
