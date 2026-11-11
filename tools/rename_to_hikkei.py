# -*- coding: utf-8 -*-
"""アプリの項目名を、救助技術必携（教科書）の名称に合わせる

   方針（本人の判断）：現場では色々な呼び名があるが、アプリのタイトルは教科書に合わせる。

   出典：消防救助技術必携 一般救助編（名古屋市消防局）第Ⅲ編 救助用器具基礎知識

   変えないもの
     003 熱画像直視装置 … 必携は「（アルゴス3）」「（アルゴス4）」と機種名付き。
                        当隊の機種が不明なので基本名のまま。
     007 エンジンカッター … 必携は「（パートナー）」「（ハスクバーナ）」。
                        当隊は STIHL TS500i で必携に無い機種。基本名のまま。
     014 空気呼吸器 … 必携は「(K2P型)」「(A-1型)」。当隊の型が不明なので基本名のまま。
     005 三連はしご、010〜013 … 既に一致、または必携に対応する節が無い。

   旧称は notes に残す。現場で別の呼び方をされても引けるようにするため。

   実行： python tools/rename_to_hikkei.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

# id : (新しい名前, 必携の節, 旧称を残す注記)
RENAME = {
    "001": ("大型油圧切断機（ホルマトロカッター）", "3-7",
            "現場では「油圧カッター」「ホルマトロのカッター」とも呼ぶ。必携の名称は大型油圧切断機"),
    "002": ("大型油圧スプレッダー（ホルマトロスプレッダー）", "2-11",
            "現場では「油圧スプレッダー」「ホルマトロ」とも呼ぶ。必携の名称は大型油圧スプレッダー"),
    "004": ("マット型空気ジャッキ", "2-7",
            "現場では「エアーバッグ」「空気式救助マット」とも呼ぶ。必携の名称はマット型空気ジャッキ。"
            "なお必携の「空気式救助マット（スーパーソフトランディング）」は落下救助用の別器具で、"
            "持ち上げには使わない"),
    "006": ("空気鋸（タイガーエアーソー）", "3-4",
            "現場では「エアソー」と呼ぶ。必携の名称は空気鋸"),
    "008": ("可搬式ウインチ（チルホール TU-16型）", "2-2",
            "現場では「チルホール」と呼ぶ。必携の名称は可搬式ウインチ。TU-16型は当隊の型式"),
    "009": ("かぎ付はしご", "1-1",
            "必携の表記は「かぎ付はしご」（送り仮名なし）"),
}


def main():
    src = io.open(PATH, encoding="utf-8").read()
    items = {x["id"]: x for x in json.loads(src)}

    done = [i for i, (n, _, _) in RENAME.items() if '"name": "%s"' % n in src]
    if done:
        print("既に改名済み: %s" % done)
        return

    lines = src.split("\n")
    out = []
    cur = None
    renamed = 0
    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)

        mn = re.match(r'^(\s*)"name": "(.+)",\s*$', line)
        if mn and cur in RENAME:
            new, _, _ = RENAME[cur]
            out.append('%s"name": %s,' % (mn.group(1), json.dumps(new, ensure_ascii=False)))
            renamed += 1
            continue

        out.append(line)

        # 旧称の注記を notes の先頭に足す
        if cur in RENAME and re.match(r'^\s*"notes": \[\s*$', line):
            out.append('      %s,' % json.dumps(RENAME[cur][2], ensure_ascii=False))

    s = "\n".join(out)
    io.open(PATH, "w", encoding="utf-8", newline="\n").write(s)

    result = {x["id"]: x for x in json.load(io.open(PATH, encoding="utf-8"))}
    print("  改名 %d件\n" % renamed)
    print("  %-4s %-30s → %s" % ("id", "旧", "新（必携の名称）"))
    for i, (new, sec, _) in RENAME.items():
        print("  %-4s %-30s → %s  [必携 %s]" % (i, items[i]["name"], result[i]["name"], sec))
    print()
    nonote = [i for i in RENAME if not result[i].get("notes")]
    if nonote:
        print("  ★ notes が無く注記を入れられなかった: %s" % nonote)
    else:
        print("  旧称の注記はすべて notes に入れた")


if __name__ == "__main__":
    main()
