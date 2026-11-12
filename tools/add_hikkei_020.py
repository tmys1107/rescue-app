# -*- coding: utf-8 -*-
"""必携から 020 つるべ式引き上げ救助 を補強する（従来型＋都市型）

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         第I編 10-6 つるべ式引き上げ救助       本文 p.155 ／ PDF 167
         第Ⅱ編  8-4 つるべ式引き上げ救助（都市型） 本文 p.247 ／ PDF 259

   「結着点と固定滑車の距離が0.5m以内だとロープがねじれる」という具体的な数字と、
   誘導ロープが効く場面がQ&Aで示されている。どちらもアプリに無かった。

   実行： python tools/add_hikkei_020.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC = "消防救助技術必携 一般救助編（名古屋市消防局）p.155・247"

NOTES = [
    "【必携】使用資器材：人員4名以上、ロープ（救助用1本・誘導用1本・小綱3本）、"
    "縛帯等1個、滑車2個、カラビナ8個",
    "【必携】救助ロープの結着点と固定滑車の距離があまり近い（0.5m以内）と、"
    "救助ロープがねじれやすい。逆に遠いと要救助者が高い位置まで上がりにくい",
    "【必携】誘導ロープが有効なのは次の2つ。①要救助者の救助時に要救助者が壁体等に接触する場合 "
    "②救助ロープがねじれる場合（誘導ロープがあるとねじれない）",
    "【必携】要救助者を救助した後は、再び救助ロープを利用して脱出する",
    "【必携・都市型】都市型のつるべ式は、各支点にテープスリング、メインロープに1/4滑車システム、"
    "バックアップロープにセミスタティックロープ、確保器具にジェットマンを使う",
    "【必携・都市型】メインロープは1/4滑車システムを設定して後方で確保する。"
    "バックアップロープはテープスリングで支点を作成したのち、ジェットマンを設定して確保する",
]

QUIZ = [
    {
        "question": "つるべ式で、救助ロープの結着点と固定滑車の距離が近すぎる（0.5m以内）と何が起きるか？",
        "choices": [
            "救助ロープがねじれやすくなる",
            "引き上げる力が余分に要る",
            "滑車が破損しやすくなる",
            "要救助者が高い位置まで上がりすぎる",
        ],
        "answer": 0,
        "explanation": "0.5m以内だと救助ロープがねじれやすい。逆に遠すぎると要救助者が高い位置まで上がりにくくなるので、近すぎても遠すぎてもいけない。",
    },
    {
        "question": "つるべ式で誘導ロープが有効なのは、どの場面か？",
        "choices": [
            "引き上げる力を減らしたいとき",
            "要救助者が壁体等に接触する場合や、救助ロープがねじれる場合",
            "滑車を増やしたいとき",
            "確保員の人数が足りないとき",
        ],
        "answer": 1,
        "explanation": "誘導ロープは、①要救助者が壁体等に接触する場合 ②救助ロープがねじれる場合 に有効。誘導ロープがあるとねじれない。",
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
        if cur == "020" and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur == "020" and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SRC, ensure_ascii=False))
        if cur == "020" and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ:
                q = dict(qid=next_qid(work, "020"), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    it = [x for x in result if x["id"] == "020"][0]
    print("  020 %s" % it["name"])
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
