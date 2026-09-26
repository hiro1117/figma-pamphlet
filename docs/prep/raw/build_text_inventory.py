#!/usr/bin/env python3
"""Normalize the raw use_figma TEXT dumps into text-inventory.json and print stats."""
import json, glob, re, collections, os

SRC = '/tmp/claude-0/-home-claude/2af90216-1dd4-55c8-83d9-b8b009fea241/scratchpad/fig'
OUT = '/mnt/user-data/outputs/fp/prep'

FRAME_NAMES = {
    '18:2': '冊子表紙/あいとま系', '20:2': '冊子表紙/那智勝浦系', '21:2': '冊子表紙/登別系', '24:2': '冊子表紙/MITT系',
    '47:2': '冊子中面/あいとま系', '48:2': '冊子中面/那智勝浦系', '48:393': '冊子中面/登別系', '48:513': '冊子中面/MITT系',
    '28:178': '乗降スポット表',
}
SERIES = {'18:2': 'あいとま', '20:2': '那智勝浦', '21:2': '登別', '24:2': 'MITT', '47:2': 'あいとま', '48:2': '那智勝浦',
          '48:393': '登別', '48:513': 'MITT', '28:178': 'スポット表'}
AR_FULL = {'N': 'NONE', 'WH': 'WIDTH_AND_HEIGHT', 'H': 'HEIGHT', 'T': 'TRUNCATE',
           'NONE': 'NONE', 'WIDTH_AND_HEIGHT': 'WIDTH_AND_HEIGHT', 'HEIGHT': 'HEIGHT', 'TRUNCATE': 'TRUNCATE'}
ALIGN = {'L': 'LEFT', 'C': 'CENTER', 'R': 'RIGHT', 'J': 'JUSTIFIED', 'LEFT': 'LEFT', 'CENTER': 'CENTER', 'RIGHT': 'RIGHT', 'JUSTIFIED': 'JUSTIFIED'}

records = []

def add(frame, row, parents=None, faces=None):
    (nid, name, chars, fam, sty, size, fills, x, y, w, h, rot, ar, parent, face, vis, miss, align, ln) = row
    if parents is not None:
        parent = parents[parent]
        face = faces[face]
    rec = {
        'frame': frame, 'frameName': FRAME_NAMES[frame], 'series': SERIES[frame],
        'id': nid, 'name': name, 'chars20': chars,
        'fontFamily': fam, 'fontStyle': sty, 'fontSize': size,
        'fills': fills, 'x': x, 'y': y, 'w': w, 'h': h, 'rotInFrame': rot,
        'textAutoResize': AR_FULL.get(ar, ar), 'parent': parent, 'face': face,
        'visible': bool(vis), 'hasMissingFont': bool(miss), 'align': ALIGN.get(align, align), 'charLen': ln,
    }
    records.append(rec)

def load(fn):
    with open(os.path.join(SRC, fn), encoding='utf-8') as f:
        return json.load(f)

def ingest(obj):
    if isinstance(obj, list):
        for o in obj:
            ingest(o)
        return
    frame = obj['frame']
    if 'rows' in obj:
        parents = obj.get('parents'); faces = obj.get('faces')
        for row in obj['rows']:
            add(frame, row, parents, faces)
    if 'full' in obj:  # 48:2 special format
        for row in obj['full']:
            add(frame, row)
        for g in obj['groups']:
            s = g['sig']
            for (nid, parentNo, chars, size, x, y, w, h, vis) in g['rows']:
                records.append({
                    'frame': frame, 'frameName': FRAME_NAMES[frame], 'series': SERIES[frame],
                    'id': nid, 'name': s['namePat'].replace('N', parentNo) if s['namePat'] != '#停留所名' else '#停留所名',
                    'chars20': chars, 'fontFamily': s['family'], 'fontStyle': s['style'], 'fontSize': size,
                    'fills': s['fills'], 'x': x, 'y': y, 'w': w, 'h': h, 'rotInFrame': s['rot'],
                    'textAutoResize': AR_FULL[s['autoResize']], 'parent': '行:停留所' + parentNo, 'face': s['face'],
                    'visible': bool(vis), 'hasMissingFont': bool(s['missingFont']), 'align': ALIGN[s['align']], 'charLen': len(chars),
                    'note': 'compressed-group',
                })

for fn in ['text_18-2.json', 'text_20-2_a.json', 'text_20-2_b.json', 'text_21-2_a.json', 'text_21-2_b.json',
           'text_24-2_a.json', 'text_24-2_b_28-178.json', 'text_47-2_a.json', 'text_47-2_b_48-393.json',
           'text_48-513_a.json', 'text_48-513_b.json', 'text_48-2.json']:
    ingest(load(fn))

# dedupe by (frame,id)
seen = set(); uniq = []
for r in records:
    k = (r['frame'], r['id'])
    if k in seen: continue
    seen.add(k); uniq.append(r)
records = uniq

# classification helpers
K = 1691 / 210.0          # px per mm  (8.052)
PX_PER_PT = K * 25.4 / 72  # 2.841

def sz(rec):
    s = rec['fontSize']
    if isinstance(s, list):
        return max(s)
    return s

def classify(rec):
    name = rec['name']; chars = rec['chars20']; s = sz(rec)
    if re.search(r'\d{2,4}-\d{2}-\d{2,4}|^0000|0:00', chars) or '電話' in name or name.startswith('#0:00'):
        if '電話' in name or re.search(r'\d{3,4}-\d{2}-\d{3,4}', chars):
            return '#電話'
    if 'QR' in name:
        return '#QR'
    if name.startswith('#') and ('注記' in name or '注意' in name or chars.startswith('※') or chars.startswith('（') or chars.startswith('(')):
        return '#注記'
    if ('補助金' in name or '発行者' in name or '事業主体' in name or '実施主体' in name or '協力会社' in name or '運行事業者' in name or '問い合わせ先' in name):
        return '#発行者'
    if name.startswith('#') and ('本文' in name or 'リード' in name or '説明' in name or 'キャプション' in name or 'リスト' in name or '内訳' in name or '合計' in name):
        return '#本文'
    if name.startswith('#') and ('見出し' in name or 'キャッチ' in name or 'サブコピー' in name or 'コピー' in name or 'タイトル' in name or 'サービス名' in name or '事業名' in name):
        return '#見出し'
    if name.startswith('見出し') or name.startswith('見出しテキスト'):
        return '見出し(固定)'
    if re.match(r'^(まずは登録|!|STEP|0[1-4]|❶|❷|❸|❹|TEL|LINE|ラベル:TEL|ラベル:LINE)$', name) or 'バッジ' in (rec['parent'] or ''):
        return 'バッジ/CTA(固定)'
    if name.startswith('ラベル'):
        return 'ラベル(固定)'
    if name.startswith('#'):
        if s < 34: return '#本文/短文(小)'
        return '#本文/短文'
    return 'その他固定'

FRAME_MIN = {'18:2':1691,'20:2':1691,'21:2':1691,'24:2':1691,'47:2':1691,'48:2':1691,'48:393':1691,'48:513':1691,'28:178':794}
for r in records:
    k = FRAME_MIN[r['frame']] / 210.0
    pxpt = k * 25.4 / 72
    r['pxPerPt'] = round(pxpt, 3)
    r['sizePt'] = round(sz(r) / pxpt, 1)
    r['class'] = classify(r)

with open(os.path.join(OUT, 'text-inventory.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'fileKey': '09Js7rndbabLAoCchqzX9j', 'page': 'テンプレート (0:1)',
        'coordinateNote': 'x,y,w,h はテンプレートフレームのローカル座標系(左上原点、フレーム自体の回転を打ち消した設計座標)でのバウンディングボックス。rotInFrame はフレーム座標系に対するテキストの回転角(180=逆さ面)。',
        'unitNote': 'fontSize は px。冊子フレーム(1691×2392)は 1691px=210mm → 8.052 px/mm、1pt=2.841px。乗降スポット表(794×1123)は 794px=210mm → 3.781 px/mm、1pt=1.334px。sizePt はフレームごとの換算値(pxPerPt 参照)。',
        'count': len(records), 'records': records}, f, ensure_ascii=False, indent=1)

# ---- stats for the md ----
byframe = collections.defaultdict(list)
for r in records: byframe[r['frame']].append(r)
print('total', len(records))
for fid in FRAME_NAMES:
    rs = byframe[fid]
    sizes = collections.Counter(sz(r) for r in rs)
    print(fid, FRAME_NAMES[fid], len(rs), 'sizes:', sorted(sizes.items()))
print()
print('class counts:', collections.Counter(r['class'] for r in records))
# small text fills
small = [r for r in records if sz(r) < 34]
print('small(<34px) count', len(small), 'fills:', collections.Counter(tuple(r['fills']) for r in small).most_common(12))
# body candidates by series
for fid in FRAME_NAMES:
    rs = [r for r in byframe[fid] if r['class'] in ('#本文',)]
    print(fid, 'body sizes', sorted(collections.Counter(sz(r) for r in rs).items()))
# missing font
print('missing:', collections.Counter((r['frame'], str(r['fontFamily'])) for r in records if r['hasMissingFont']))
