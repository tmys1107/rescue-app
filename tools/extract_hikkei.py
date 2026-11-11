# -*- coding: utf-8 -*-
"""消防救助技術必携から、資器材ごとのページを抜き出して data/pdf/ に置く

   元：P:\\消防\\訓練資料\\三宅資料\\消防救助技術必携. 一般救助編 [名古屋市].pdf
       566ページ・145MB。1ページあたり 1666x2477 のJPEGスキャン（約300dpi）＋OCRの文字層。

   そのまま抜き出すと1ページ約220KB。4ページで約870KBになり、
   資器材10件ぶんでは重すぎるので、グレースケール150dpiのJPEGに描き直す。

   pymupdf の rewrite_images は使わない。画像を差し替えると配置行列が合わず、
   拡大・ずれた状態で描画される不具合が出た（2.1 で確認）。
   そのため自前で描き直し、OCRの文字層は不可視テキストとして入れ直す。

   実行： python tools/extract_hikkei.py
"""
import io
import os
import sys

import pymupdf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = r"P:\消防\訓練資料\三宅資料\消防救助技術必携. 一般救助編 [名古屋市].pdf"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "data", "pdf")

DPI = 150
QUALITY = 65

# 出力名 : (開始ページ, 終了ページ)  ※PDF上の通しページ番号
SECTIONS = {
    "かぎ付きはしご_救助技術必携.pdf": (277, 278),
    "三連はしご_救助技術必携.pdf": (279, 280),
    "チルホール_救助技術必携.pdf": (287, 290),
    "マット型空気ジャッキ_救助技術必携.pdf": (301, 308),
    "油圧スプレッダー_救助技術必携.pdf": (313, 316),
    "エンジンカッター_救助技術必携.pdf": (323, 326),
    "エアソー_救助技術必携.pdf": (331, 334),
    "油圧カッター_救助技術必携.pdf": (339, 340),
    "空気呼吸器_救助技術必携.pdf": (353, 368),
    "熱画像直視装置_救助技術必携.pdf": (395, 398),
}


def build(src, first, last, path):
    out = pymupdf.open()
    kept_text = 0
    for i in range(first - 1, last):
        sp = src[i]
        rect = sp.rect
        pix = sp.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
        img = pix.tobytes("jpg", jpg_quality=QUALITY)

        np = out.new_page(width=rect.width, height=rect.height)
        np.insert_image(rect, stream=img)

        # OCRの文字層を不可視（render_mode=3）で入れ直し、検索できる状態を保つ
        for x0, y0, x1, y1, word, *_ in sp.get_text("words"):
            size = max(4.0, (y1 - y0) * 0.86)
            try:
                np.insert_text((x0, y1 - (y1 - y0) * 0.18), word,
                               fontname="japan", fontsize=size, render_mode=3)
                kept_text += len(word)
            except Exception:
                pass

    out.save(path, garbage=4, deflate=True)
    out.close()
    return kept_text


def main():
    os.makedirs(OUT, exist_ok=True)
    src = pymupdf.open(SRC)
    total = 0
    print("  %-34s %4s %8s  %s" % ("ファイル", "頁", "サイズ", "文字層"))
    for name, (a, b) in SECTIONS.items():
        path = os.path.join(OUT, name)
        n = build(src, a, b, path)
        kb = os.path.getsize(path) / 1024
        total += kb
        chk = pymupdf.open(path)
        got = sum(len(p.get_text().strip()) for p in chk)
        print("  %-34s %4d %7.0fKB  %s" % (name, b - a + 1, kb,
                                           "%d字" % got if got else "なし"))
    print("\n  合計 %.1f MB" % (total / 1024))


if __name__ == "__main__":
    main()
