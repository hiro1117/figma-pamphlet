#!/usr/bin/env python3
"""単色背景(#00FF00 / #FF00FF)で生成した前景 PNG をキー抜きして実 alpha の PNG にする。

  .venv/bin/python scripts/library/keyout.py in.png out.png [--key 00FF00] [--erode 1] [--feather 1] [--trim]

手順: (1) キー色との色差で alpha を作る(近い=透明、遠い=不透明、途中は滑らか)
      (2) 縁に残るキー色のにじみ(spill)を抑える
      (3) alpha を erode ピクセルだけ収縮(P13-b の「エッジ収縮」)
      (4) --trim で透明な余白を切り落とす
Gemini 系は真の alpha を出さないため、この後処理が必須(計画書 5.1)。
"""
import argparse
import numpy as np
from PIL import Image, ImageFilter


def border_color(im: Image.Image):
    """外周 4 辺の中央値 = キー色(auto 用)"""
    a = np.asarray(im.convert("RGB"))
    edge = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    return "".join(f"{int(v):02X}" for v in np.median(edge, axis=0))


def flood_mask(im: Image.Image, key_hex: str, thresh: int):
    """外周から連結したキー色領域だけを True にするマスク(内部の同色は残す)。"""
    from PIL import ImageDraw
    work = im.convert("RGB").copy()
    marker = (1, 2, 3)
    w, h = work.size
    seeds = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]
    key = tuple(int(key_hex[i:i + 2], 16) for i in (0, 2, 4))
    for sx, sy in seeds:
        px = work.getpixel((sx, sy))
        if px != marker and sum(abs(px[i] - key[i]) for i in range(3)) <= thresh * 3:
            ImageDraw.floodfill(work, (sx, sy), marker, thresh=thresh)
    a = np.asarray(work)
    return (a[..., 0] == marker[0]) & (a[..., 1] == marker[1]) & (a[..., 2] == marker[2])


def keyout(im: Image.Image, key_hex: str, erode: int, feather: int, near: float = 40.0, far: float = 110.0, flood: bool = True):
    near_outside = None
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    key = np.array([int(key_hex[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
    # 色差(ユークリッド)。キー色に近いほど透明
    dist = np.sqrt(((rgb - key) ** 2).sum(axis=2))
    alpha = np.clip((dist - near) / (far - near), 0.0, 1.0)
    if flood:
        # 外周から連結した領域だけ透明にし、内部のキー色に近い色(白いシャツ等)は残す
        outside = flood_mask(im, key_hex, thresh=int(near))
        # 境界の半透明は色差ベース、outside から 3px 以上離れた内部は不透明
        from PIL import ImageFilter
        m = Image.fromarray((outside * 255).astype(np.uint8), "L").filter(ImageFilter.MaxFilter(7))
        near_outside = np.asarray(m) > 0
        alpha = np.where(near_outside, alpha, 1.0)
        alpha = np.where(outside, np.minimum(alpha, 0.0), alpha)
    # spill 抑制(有彩色キーのみ、外周近傍 7px だけ): キー色の支配チャンネルを他2チャンネルの最大値までクランプ
    if key.max() - key.min() > 60:
        dom = int(np.argmax(key))
        others = [c for c in range(3) if c != dom]
        lim = np.maximum(rgb[..., others[0]], rgb[..., others[1]])
        spill = (rgb[..., dom] > lim) & (near_outside if flood else True)
        rgb[..., dom] = np.where(spill, lim, rgb[..., dom])
    a = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    if erode > 0:
        a = a.filter(ImageFilter.MinFilter(2 * erode + 1))
    if feather > 0:
        a = a.filter(ImageFilter.GaussianBlur(feather))
    out = Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(a)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--key", default="auto", help="キー色 hex または auto(外周の中央値)")
    ap.add_argument("--erode", type=int, default=1)
    ap.add_argument("--feather", type=float, default=0.8)
    ap.add_argument("--trim", action="store_true")
    ap.add_argument("--crop", help="L,T,R,B px を先に切り落とす(外周の線などを除く)")
    ap.add_argument("--clear-above", type=int, help="この y(px、crop 後)より上の alpha を 0 にする(空のにじみ除去)")
    ns = ap.parse_args()
    im = Image.open(ns.src)
    if ns.crop:
        L, T, R, B = (int(v) for v in ns.crop.split(","))
        im = im.crop((L, T, im.width - R, im.height - B))
    key = border_color(im) if ns.key == "auto" else ns.key.lstrip("#").upper()
    out = keyout(im, key, ns.erode, ns.feather)
    if ns.clear_above is not None:
        a = np.asarray(out.getchannel("A")).copy(); a[:ns.clear_above, :] = 0
        out.putalpha(Image.fromarray(a, "L"))
    if ns.trim:
        bbox = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        if bbox:
            out = out.crop(bbox)
    out.save(ns.dst)
    a = np.asarray(out.getchannel("A"))
    print(f"{ns.dst}: key={key} {out.size[0]}x{out.size[1]} opaque={100*(a>250).mean():.1f}% semi={100*((a>4)&(a<=250)).mean():.1f}%")
