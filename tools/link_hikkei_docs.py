# -*- coding: utf-8 -*-
"""抜き出した必携PDFを equipment.json の docs に結び付ける

   006・007・008 は従来「救助技術必携」として本人が撮影したPDFが貼ってあった。
   同じファイル名で必携からの抜き出しに差し替え済みなので、ラベルだけ具体名にする。
   docs が無い項目には、"sources" 配列の直後に docs を新設する。

   docs は1行オブジェクト形式で書かれているので、それに合わせる。
     { "label": "…", "file": "data/pdf/….pdf" }

   実行： python tools/link_hikkei_docs.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

LINK = {
    "001": ("救助技術必携（ホルマトロカッター）", "油圧カッター_救助技術必携.pdf"),
    "002": ("救助技術必携（ホルマトロスプレッダー）", "油圧スプレッダー_救助技術必携.pdf"),
    "003": ("救助技術必携（アルゴス3・4）", "熱画像直視装置_救助技術必携.pdf"),
    "004": ("救助技術必携（マット型空気ジャッキ）", "マット型空気ジャッキ_救助技術必携.pdf"),
    "005": ("救助技術必携（三連はしご）", "三連はしご_救助技術必携.pdf"),
    "006": ("救助技術必携（空気鋸 タイガーエアーソー）", "エアソー_救助技術必携.pdf"),
    "007": ("救助技術必携（エンジンカッター パートナー）", "エンジンカッター_救助技術必携.pdf"),
    "008": ("救助技術必携（可搬式ウインチ チルホール）", "チルホール_救助技術必携.pdf"),
    "009": ("救助技術必携（かぎ付はしご）", "かぎ付きはしご_救助技術必携.pdf"),
    "014": ("救助技術必携（空気呼吸器 K2P・A-1）", "空気呼吸器_救助技術必携.pdf"),
}

LINE = '      {{ "label": {0}, "file": "data/pdf/{1}" }}'


def main():
    src = io.open(PATH, encoding="utf-8").read()
    items = {x["id"]: x for x in json.loads(src)}

    missing = [f for _, f in LINK.values()
               if not os.path.exists(os.path.join(HERE, "data", "pdf", f))]
    assert not missing, "PDFが無い: %s" % missing

    lines = src.split("\n")
    out = []
    cur = None
    replaced = added = 0

    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)

        # 既存の「救助技術必携」行をラベルごと差し替え
        if cur in LINK and '"label": "救助技術必携"' in line:
            label, f = LINK[cur]
            tail = "," if line.rstrip().endswith(",") else ""
            out.append(LINE.format(json.dumps(label, ensure_ascii=False), f) + tail)
            replaced += 1
            continue

        out.append(line)

        # docs が無い項目は、sources 配列の閉じ "]," の直後に docs を新設
        if cur in LINK and not items[cur].get("docs") and line.strip() == "],":
            # 直前が sources 配列かどうかを、積んだ行をさかのぼって確認
            for prev in reversed(out[:-1]):
                if '": [' in prev:
                    is_sources = '"sources": [' in prev
                    break
            else:
                is_sources = False
            if is_sources:
                label, f = LINK[cur]
                out.append('    "docs": [')
                out.append(LINE.format(json.dumps(label, ensure_ascii=False), f))
                out.append('    ],')
                added += 1

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    print("  ラベル差し替え %d件 / docs新設 %d件\n" % (replaced, added))
    ng = 0
    for it in result:
        for d in (it.get("docs") or []):
            ok = os.path.exists(os.path.join(HERE, d["file"]))
            if not ok:
                ng += 1
            print("  %s %-22s %-38s %s" % (it["id"], it["name"][:20], d["label"][:36],
                                           "OK" if ok else "★無し"))
    print("\n  参照切れ %d件 / 全%d件" % (ng, len(result)))


if __name__ == "__main__":
    main()
