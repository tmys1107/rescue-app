# -*- coding: utf-8 -*-
"""アプリアイコンを icons/ に配置する。

   素材は sources/icon/（ChatGPTで作成）。デザインは変更しない。

   ただし素材は「白地の上に角丸バッジ」が焼き込まれている。
   iOS はホーム画面アイコンに自前の角丸マスクを掛けるため、そのまま使うと
   マスクの内側に白が残り、白い枠が付いたように見える（実測17.1%）。
   そこで iOS用（apple-touch-icon）と Android のマスカブル用だけ、
   原本からバッジ部分を切り出して全面化する。絵そのものには手を加えない。

     元のまま            iOSマスク内の白 17.1%
     バッジを切り出し     → 7.9%
     外側の白を地色で埋め → 1.9%

   実行： python tools/build_icons.py
"""
import io
import os
import shutil
import sys

from PIL import Image, ImageChops, ImageDraw

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "sources", "icon")
OUT = os.path.join(HERE, "icons")

# そのまま使うもの（ブラウザのタブとAndroidの通常表示。白地のカードで問題ない）
COPY = ["favicon-16.png", "favicon-32.png", "icon-192.png", "icon-512.png"]

# 全面化して作るもの（OSが自前でマスクを掛ける用途）
FULLBLEED = [("apple-touch-icon.png", 180), ("icon-512-maskable.png", 512)]


def badge_fullbleed(path):
    """原本から白い余白を取り除き、外周をバッジの地色で埋めた正方形を返す"""
    im = Image.open(path).convert("RGB")

    # 白でない領域の外接矩形を取り、正方形に整えて切り出す
    bg = Image.new("RGB", im.size, (255, 255, 255))
    diff = ImageChops.difference(im, bg).convert("L").point(lambda v: 255 if v > 12 else 0)
    x0, y0, x1, y1 = diff.getbbox()
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    half = max(x1 - x0, y1 - y0) // 2
    crop = im.crop((cx - half, cy - half, cx + half, cy + half))

    # 角丸の外に残る白を、バッジの地色で塗りつぶす。
    # 四隅から流し込むのでバッジの縁で止まり、内側の金属色は残る。
    s = crop.size[0]
    navy = crop.getpixel((int(s * 0.06), int(s * 0.5)))
    for pt in [(0, 0), (s - 1, 0), (0, s - 1), (s - 1, s - 1)]:
        ImageDraw.floodfill(crop, pt, navy, thresh=60)
    return crop


def white_ratio_under_ios_mask(im):
    """iOSの角丸マスク（22.37%）を掛けたとき、内側に残る白の割合"""
    s = im.size[0]
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1],
                                           radius=int(s * 0.2237), fill=255)
    white = tot = 0
    step = max(1, s // 200)
    for y in range(0, s, step):
        for x in range(0, s, step):
            if mask.getpixel((x, y)) == 0:
                continue
            tot += 1
            p = im.getpixel((x, y))
            if p[0] > 235 and p[1] > 235 and p[2] > 235:
                white += 1
    return 100.0 * white / tot


def main():
    os.makedirs(OUT, exist_ok=True)

    for name in COPY:
        src = os.path.join(SRC, name)
        shutil.copyfile(src, os.path.join(OUT, name))
        im = Image.open(src)
        print("  複製  %-24s %dx%d" % (name, im.size[0], im.size[1]))

    base = badge_fullbleed(os.path.join(SRC, "icon-original.png"))
    for name, size in FULLBLEED:
        out = base.resize((size, size), Image.LANCZOS)
        out.save(os.path.join(OUT, name), optimize=True)
        print("  全面化 %-24s %dx%d  iOSマスク内の白 %.1f%%"
              % (name, size, size, white_ratio_under_ios_mask(out)))

    before = white_ratio_under_ios_mask(
        Image.open(os.path.join(SRC, "apple-touch-icon.png")).convert("RGB"))
    print("\n  （素材そのままだと %.1f%% が白だった）" % before)


if __name__ == "__main__":
    main()
