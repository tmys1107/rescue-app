# -*- coding: utf-8 -*-
"""アプリアイコンを icons/ に配置する。

   素材は sources/icon/（ChatGPTで作成）。デザインは変更しない。

   素材は「白地の上に角丸バッジ＋ドロップシャドウ」が焼き込まれている。
   iOS はホーム画面アイコンに自前の角丸マスクを掛けるので、そのまま使うと
   バッジの外側（白と影）がマスクの内側に残り、白い縁として見える。

   対策：バッジの外側を地色で塗りつぶし、バッジの外接矩形で切り出して全面化する。
   絵そのものには手を加えない。

   実装の注意（一度踏んだ）：
     PIL の ImageDraw.floodfill の thresh は「RGB3チャンネルの差の合計」。
     白(255,255,255) と 影(199,200,201) の差は合計165ある。
     thresh=60 では影に届かず、影のリングが残ったまま白い縁になった。
     そのため floodfill はやめ、明るさのマスクを自分で作って塗る。

     検証も「235以上を白とみなす」では影(199〜233)を数えられない。
     min(R,G,B) > 120 を「地色でない明るい画素」として数える。

   実行： python tools/build_icons.py
"""
import io
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageChops

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "sources", "icon")
OUT = os.path.join(HERE, "icons")

# そのまま使うもの（ブラウザのタブとAndroidの通常表示。白地のカードで問題ない）
COPY = ["favicon-16.png", "favicon-32.png", "icon-192.png", "icon-512.png"]

# 全面化して作るもの（OSが自前でマスクを掛ける用途）
FULLBLEED = [("apple-touch-icon.png", 180), ("icon-512-maskable.png", 512)]

LIGHT = 90      # min(R,G,B) がこれを超えたら「背景か影」とみなす
GROW = 5        # 塗る範囲をバッジ側へ広げる画素数（縁のアンチエイリアスを消す）


def exterior_mask(arr):
    """バッジの外側（白＋影）を True にしたマスクを返す。

    バッジは角丸正方形で凸なので、各行・各列を両端から走査して
    明るい画素が続く区間を外側とみなせば、穴を拾わずに正確に取れる。
    """
    light = arr.min(axis=2) > LIGHT
    h, w = light.shape
    ext = np.zeros_like(light)

    for y in range(h):
        row = light[y]
        i = 0
        while i < w and row[i]:
            ext[y, i] = True; i += 1
        i = w - 1
        while i >= 0 and row[i]:
            ext[y, i] = True; i -= 1

    for x in range(w):
        col = light[:, x]
        i = 0
        while i < h and col[i]:
            ext[i, x] = True; i += 1
        i = h - 1
        while i >= 0 and col[i]:
            ext[i, x] = True; i -= 1

    # 縁のアンチエイリアス（中間色）も食べるよう、内側へ少し広げる
    for _ in range(GROW):
        g = ext.copy()
        g[1:, :] |= ext[:-1, :]
        g[:-1, :] |= ext[1:, :]
        g[:, 1:] |= ext[:, :-1]
        g[:, :-1] |= ext[:, 1:]
        ext = g
    return ext


def badge_fullbleed(path):
    """白と影を地色で潰し、バッジの外接矩形で正方形に切り出す"""
    im = Image.open(path).convert("RGB")
    arr = np.array(im)

    # 地色はバッジ左端の内側から拾う
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    x0, y0, x1, y1 = bb.convert("L").point(lambda v: 255 if v > 12 else 0).getbbox()
    navy = arr[(y0 + y1) // 2, x0 + int((x1 - x0) * 0.04)].copy()

    arr[exterior_mask(arr)] = navy
    im = Image.fromarray(arr)

    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    half = max(x1 - x0, y1 - y0) // 2
    return im.crop((cx - half, cy - half, cx + half, cy + half)), tuple(int(v) for v in navy)


def edge_report(im, px=4):
    """外周px幅のリングに、地色でない明るい画素が何%あるか"""
    a = np.array(im.convert("RGB")).min(axis=2)
    ring = np.zeros(a.shape, bool)
    ring[:px, :] = ring[-px:, :] = ring[:, :px] = ring[:, -px:] = True
    return 100.0 * float((a[ring] > 120).sum()) / int(ring.sum())


def main():
    os.makedirs(OUT, exist_ok=True)

    for name in COPY:
        shutil.copyfile(os.path.join(SRC, name), os.path.join(OUT, name))
        im = Image.open(os.path.join(SRC, name))
        print("  複製  %-24s %dx%d" % (name, im.size[0], im.size[1]))

    base, navy = badge_fullbleed(os.path.join(SRC, "icon-original.png"))
    print("\n  バッジ地色 RGB%s / 全面化後 %dx%d" % (navy, base.size[0], base.size[1]))

    for name, size in FULLBLEED:
        out = base.resize((size, size), Image.LANCZOS)
        out.save(os.path.join(OUT, name), optimize=True)
        print("  全面化 %-24s %dx%d  外周の明るい画素 %.2f%%"
              % (name, size, size, edge_report(out)))

    before = Image.open(os.path.join(SRC, "apple-touch-icon.png"))
    print("\n  （素材そのままだと外周の明るい画素 %.2f%%）" % edge_report(before))


if __name__ == "__main__":
    main()
