#!/usr/bin/env python3
"""Generate the per-frame tables section of text-inventory.md (collapsing repeated rows)."""
import json, re, collections

OUT = '/mnt/user-data/outputs/fp/prep'
data = json.load(open(f'{OUT}/text-inventory.json', encoding='utf-8'))
recs = data['records']

order = ['18:2', '20:2', '21:2', '24:2', '47:2', '48:2', '48:393', '48:513', '28:178']
byframe = collections.defaultdict(list)
for r in recs:
    byframe[r['frame']].append(r)

def fmt_size(s):
    if isinstance(s, list):
        return '/'.join(str(x) for x in s)
    return str(s)

def fmt_font(r):
    fam, sty = r['fontFamily'], r['fontStyle']
    if isinstance(fam, list):
        return ' + '.join(f'{a} {b}' for a, b in zip(fam, sty))
    return f'{fam} {sty}'

REPEAT_PAT = re.compile(r'^(#停留所名|装飾:停留所マーク\(\d+\)|ラベル:番号\d+|#乗降場所\d{3}名称|#乗降ポイント\d+名称|#スポット\d+名称|ラベル:写真番号\d+|\d{1,2})$')

lines = []
lines.append('## 面ごとの全TEXT一覧(フレームローカル座標・px)\n')
lines.append('列: id / 名前 / 文字(先頭) / フォント / size px(≈pt) / fill / x,y,w,h / rot / autoResize / 親 / 面 / 備考(hidden=非表示, MISSING=フォント欠落)\n')
lines.append('繰り返し行(停留所・乗降場所・番号バッジ等)は先頭1件+件数に畳んでいます。全件は text-inventory.json を参照。\n')

for fid in order:
    rs = byframe[fid]
    lines.append(f"\n### {fid} {rs[0]['frameName']} — TEXT {len(rs)}件\n")
    lines.append('| id | 名前 | 文字(先頭20) | フォント | size px(≈pt) | fill | x,y,w,h | rot | AR | 親 | 面 | 備考 |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
    # collapse
    groups = collections.OrderedDict()
    for r in rs:
        m = REPEAT_PAT.match(r['name'])
        key = None
        if m:
            key = (re.sub(r'\d+', 'N', r['name']), fmt_font(r), fmt_size(r['fontSize']), tuple(r['fills']), r['face'])
        if key and key in groups:
            groups[key]['n'] += 1
            groups[key]['ids'].append(r['id'])
            continue
        entry = {'r': r, 'n': 1, 'ids': [r['id']]}
        if key:
            groups[key] = entry
        else:
            groups[('single', r['id'])] = entry
    for entry in groups.values():
        r = entry['r']
        note = []
        if not r['visible']: note.append('hidden')
        if r['hasMissingFont']: note.append('MISSING')
        if entry['n'] > 1: note.append(f"×{entry['n']} (…{entry['ids'][-1]})")
        ar = {'NONE': 'N', 'WIDTH_AND_HEIGHT': 'WH', 'HEIGHT': 'H', 'TRUNCATE': 'T'}.get(r['textAutoResize'], r['textAutoResize'])
        chars = r['chars20'].replace('|', '｜').replace('\r', '')
        name = r['name'].replace('|', '｜')
        lines.append(f"| {r['id']} | {name} | {chars} | {fmt_font(r)} | {fmt_size(r['fontSize'])} (≈{r['sizePt']}) | {' '.join(r['fills']) or '-'} | {r['x']},{r['y']},{r['w']},{r['h']} | {r['rotInFrame']} | {ar} | {r['parent']} | {(r['face'] or '-').replace('面:', '')} | {' '.join(note)} |")

open('/tmp/claude-0/-home-claude/2af90216-1dd4-55c8-83d9-b8b009fea241/scratchpad/fig/text_tables.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('rows written', sum(1 for l in lines if l.startswith('| ') and not l.startswith('| id')))
