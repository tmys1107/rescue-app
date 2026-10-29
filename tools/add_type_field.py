# -*- coding: utf-8 -*-
"""equipment.json に type フィールドを追加する（1回だけ実行する移行スクリプト）

   資器材と操法はデータの形が違う。
     spec / importantSpec / image / docs / location … 資器材のみ
     usage / notes / quiz                          … 両方
   そのため一覧とメニューを分ける。その土台として type を持たせる。

   json.load → json.dump で書き戻すと、手書きの整形（短い配列を1行に畳む等）が
   全部崩れて差分が読めなくなる。そのため行単位で "category" の直前に挿入する。

   既に type がある行は触らない（再実行しても安全）。

   実行： python tools/add_type_field.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

OPS_CATEGORY = "操法・救助方法"
TYPE_EQ = "資器材"
TYPE_OPS = "操法・訓練"

CAT_LINE = re.compile(r'^(\s*)"category"\s*:\s*"([^"]+)"')


def main():
    with open(PATH, encoding="utf-8") as f:
        src = f.read()

    if '"type"' in src:
        print("既に type がある。何もしない")
        return

    out = []
    added = 0
    for line in src.split("\n"):
        m = CAT_LINE.match(line)
        if m:
            indent, cat = m.group(1), m.group(2)
            t = TYPE_OPS if cat == OPS_CATEGORY else TYPE_EQ
            out.append('%s"type": "%s",' % (indent, t))
            added += 1
        out.append(line)

    with open(PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    # 書き戻した結果が壊れていないか、必ず読み直して確かめる
    with open(PATH, encoding="utf-8") as f:
        items = json.load(f)

    eq = [it for it in items if it.get("type") == TYPE_EQ]
    ops = [it for it in items if it.get("type") == TYPE_OPS]
    missing = [it["id"] for it in items if not it.get("type")]

    print("付与 %d行 / JSON再読込 OK（%d件）" % (added, len(items)))
    print("  %s %2d件（問題 %d問）" % (TYPE_EQ, len(eq), sum(len(it.get("quiz") or []) for it in eq)))
    print("  %s %2d件（問題 %d問）" % (TYPE_OPS, len(ops), sum(len(it.get("quiz") or []) for it in ops)))
    if missing:
        print("  type が付かなかった: %s" % ", ".join(missing))

    # 裏取り：操法なのに資器材専用フィールドを持っていたら知らせる
    warn = [(it["id"], it["name"], [k for k in ("spec", "importantSpec", "image", "docs", "location") if it.get(k)])
            for it in ops]
    warn = [w for w in warn if w[2]]
    if warn:
        print("\n要確認：")
        for i, n, w in warn:
            print("  %s %s … %s" % (i, n, ", ".join(w)))
    else:
        print("\n要確認なし")


if __name__ == "__main__":
    main()
