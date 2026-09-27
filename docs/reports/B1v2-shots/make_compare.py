"""raw_<key>.png(get_screenshot、180° 回転フレーム)→ 正立の表紙面 <key>_face.png と比較画像 compare_before_A_B_C.png"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
keys = sys.argv[1:] or ['A','B','C']
def face_of(key):
    im = Image.open(f'raw_{key}.png').convert('RGB').rotate(180)   # フレームは 180° 回転 → 正立化
    ox = im.width - 1691                                            # 塗り足し分(回転後は左側)
    face = im.crop((ox + 1127, 0, ox + 1691, 1196))
    return face, im
for k in keys:
    face, im = face_of(k)
    face.save(f'case{k}_face.png'); im.save(f'case{k}_sheet.png')
faces = {'before': Image.open('before-71-2_face.png')}
for k in ['A','B','C']:
    if os.path.exists(f'case{k}_face.png'): faces[k] = Image.open(f'case{k}_face.png')
W = 564; gap = 24; sheet = Image.new('RGB', (W * 4 + gap * 3 + 40, 1196 + 70), 'white'); d = ImageDraw.Draw(sheet)
try: f = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', 30)
except Exception: f = ImageFont.load_default()
for i, (key, label) in enumerate([('before', '改修前(制作物 71:2)'), ('A', '案A 全幅ヒーロー+情報帯'), ('B', '案B パネル内ヒーロー'), ('C', '案C 絵の空にタイトル')]):
    x = 20 + i * (W + gap); d.text((x, 18), label, fill=(0, 0, 0), font=f)
    if key in faces: sheet.paste(faces[key], (x, 70))
sheet.save('compare_before_A_B_C.png')
sheet.resize((sheet.width // 2, sheet.height // 2)).save('/private/tmp/claude-502/-Users-hirokihashimoto-dev-work-cicac-figma-pamphlet/12f6f5c4-31aa-424d-b75e-e1ebe262dc21/scratchpad/b1v2_compare_half.png')
print('ok', keys)
