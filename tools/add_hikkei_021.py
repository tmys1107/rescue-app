# -*- coding: utf-8 -*-
"""必携から 021 はしごクレーン救助 を補強する（従来型＋都市型）

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         第I編 10-7 はしごクレーン救助   本文 p.156〜160 ／ PDF 168〜172
         第Ⅱ編  8-5 はしごクレーン救助（都市型） 本文 p.249 ／ PDF 261

   p.160 の Q&A「はしごクレーンを安定して行うには？」に、なぜ短い状態が安定するのかが
   モーメントで説明されている。アプリには結論も理由も無かったので取り込む。

   なお PDF 173〜174 は「座席懸垂背負い法」で、はしごクレーンとは別の操法。
   どの項目に対応するか判断がつかないため今回は見送った。

   実行： python tools/add_hikkei_021.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC = "消防救助技術必携 一般救助編（名古屋市消防局）p.156〜160・249"

NOTES = [
    "【必携】支点をとる際に地物が利用できなくても、三連はしごを利用して支点を作り救助できる。"
    "はしごクレーンは、はしごの角度と基底部の固定がポイント",
    "【必携】はしごクレーンを安定させる3点。①はしごの基底部が滑らないように地物等を利用して固定する "
    "②各支点は横さんの中央に作成する ③はしごは短い状態（縮てい状態）で使用した方が安定する",
    "【必携】はしごを2倍に伸ばすと、はしごを倒そうとする転倒モーメントも2倍になる。"
    "一方で確保できる場所は限られていて「うでの長さ」はあまり伸びないため、"
    "確保側はほぼ倍の張力を保持しなければならない。人力で確保せざるを得ない場合は特に注意",
    "【必携】はしごが長いと、はしご自体がたわむ、三つ打ちの確保ロープが長くなって荷重による"
    "伸び縮みが顕著になる、左右への転倒危険も高まる。だから短い状態のほうが安定しやすい",
    "【必携】確保ロープは、三連はしご（縮ていのまま）の両方の主かん上部にそれぞれ巻き結びで結着する。"
    "不均等とならないよう左右対称の位置に結着する",
    "【必携】確保ロープは地物に結着する。地物のほか消防車両等を利用する方法もある。"
    "どちらもできない場合は身体確保（腰確保）とする",
    "【必携】はしごをより安定させるため、基底部を小綱で固定するとよい",
    "【必携】上部固定滑車は、はしご上端から2〜3本目の横さんに小綱（2つ折りにしてダブルで使用）で"
    "巻き結び＋本結びをとり、巻き結びの内側2本にカラビナを掛けて滑車を取り付ける",
    "【必携・都市型】都市型は、メインロープに1/4滑車システム、バックアップロープに"
    "セミスタティックロープとジェットマン、メインロープの確保は身体確保、"
    "バックアップロープの確保はジェットマン、はしご確保ロープに10mランヤード付きグリヨンを使う",
    "【必携・都市型】三連はしごの安定度を考慮して、隊員の介添えは厳禁",
    "【必携・都市型】はしご確保ロープは、テープスリングを三連はしごにカウヒッチ等で結着し、"
    "10mランヤード付きグリヨン先端のカラビナと結合する。グリヨンの端末は、活動中の誤操作および"
    "ロープの緩み防止のため、ふた結びで処理する",
    "【必携・都市型】メインロープ（1/4滑車システム）の支点を三連はしごの先端に"
    "テープスリングで作成すると、揚程を多く取ることができる",
]

QUIZ = [
    {
        "question": "はしごクレーンを安定させるために、はしごの長さはどうするのがよいか？",
        "choices": [
            "できるだけ長く伸ていする",
            "短い状態（縮てい状態）で使用する",
            "全伸ていの半分にする",
            "長さは安定度に関係しない",
        ],
        "answer": 1,
        "explanation": "短い状態のほうが安定する。長いと、転倒モーメントが大きくなるうえ、はしご自体がたわみ、確保ロープの伸び縮みも顕著になり、左右への転倒危険も高まる。",
    },
    {
        "question": "はしごクレーンのはしごを2倍の長さにすると、確保側に必要な張力はどうなるか？",
        "choices": [
            "変わらない",
            "ほぼ倍の張力が必要になる",
            "半分で済む",
            "4倍になる",
        ],
        "answer": 1,
        "explanation": "転倒モーメントは2倍になるが、確保できる場所は限られていて「うでの長さ」はあまり伸びないため、確保側はほぼ倍の張力を保持することになる。人力確保のときは特に注意。",
    },
    {
        "question": "都市型のはしごクレーン救助で、厳禁とされているのはどれか？",
        "choices": [
            "基底部の固定",
            "隊員の介添え",
            "1/4滑車システムの使用",
            "グリヨンの端末処理",
        ],
        "answer": 1,
        "explanation": "三連はしごの安定度を考慮して、隊員の介添えは厳禁とされている。はしごに人の重さや動きを加えないという考え方。",
    },
]


def next_qid(src, item_id):
    used = set(int(n) for n in re.findall(r'"qid": "%s-q(\d+)"' % item_id, src))
    n = 1
    while n in used:
        n += 1
    return "%s-q%d" % (item_id, n)


def j(obj, indent):
    return json.dumps(obj, ensure_ascii=False, indent=2).replace("\n", "\n" + " " * indent)


def main():
    src = io.open(PATH, encoding="utf-8").read()
    if SRC in src:
        print("既に取り込み済み。何もしない")
        return

    lines = src.split("\n")
    out, cur, work = [], None, src
    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)
        if cur == "021" and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur == "021" and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SRC, ensure_ascii=False))
        if cur == "021" and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ:
                q = dict(qid=next_qid(work, "021"), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    it = [x for x in result if x["id"] == "021"][0]
    print("  021 %s" % it["name"])
    print("     知見 %d件（+%d）／ 問題 %d問（+%d）／ 出典 %d件"
          % (len(it["notes"]), len(NOTES), len(it["quiz"]), len(QUIZ), len(it["sources"])))

    PAT = re.compile(r"(特に.*ない|基準はない|^自由|どちらでもよい|どれでもよい|いつでもよい|"
                     r"どこでもよい|決まりはなく|決まりはない|関係しない)")
    bad = [q["qid"] for q in it["quiz"] for i, c in enumerate(q["choices"])
           if i != q["answer"] and PAT.search(c)]
    print("     選ばれにくい誤答: %s" % (bad if bad else "なし"))
    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n  合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(result), len(qids)))


if __name__ == "__main__":
    main()
