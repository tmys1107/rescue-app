# -*- coding: utf-8 -*-
"""必携から 022 一箇所吊り担架水平救助 を補強する

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         第Ⅱ編 8-6 一箇所吊り担架水平救助 本文 p.251〜252 ／ PDF 263〜264

   この操法は必携では都市型（第Ⅱ編）にしか載っていない。従来型に対応する節はない。

   021 はしごクレーンでは「隊員の介添えは厳禁」だが、ここでは
   「強固な支点であれば介添えは可能」とある。支点の種類で扱いが変わる点が要注意。

   追加のたびに、同じ項目内で質問文が似すぎている設問が出ていないか検査する。
   過去に 002 と 020 で完全重複を作ったため。

   実行： python tools/add_hikkei_022.py
"""
import difflib
import io
import itertools
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC = "消防救助技術必携 一般救助編（名古屋市消防局）p.251〜252"

NOTES = [
    "【必携・都市型】必携ではこの操法は都市型にしか載っていない。必要資器材はメインロープ／"
    "バックアップロープ／バスケットストレッチャー等／カラビナ・テープスリング・ジェットマン等／"
    "10mランヤード付きグリヨン",
    "【必携・都市型】全体のポイントは、各支点にテープスリングを使用、メインロープと"
    "バックアップロープにセミスタティックロープを使用、確保器具にジェットマンを使用の3点",
    "【必携・都市型】上階から支点を設定する場合、器具の長さ調節機能を活かして"
    "10mランヤード付きグリヨンを支点に活用できる",
    "【必携・都市型】グリヨンで支点の高さ調整をした後は、端末をふた結びにして"
    "誤操作および緩みを防止する",
    "【必携・都市型】鋭利な角には当て布等を利用する。手が届きにくく当て布が設定しづらい場所では"
    "スライド式プロテクターを活用する",
    "【必携・都市型】強固な支点であれば隊員の介添えは可能。ただし荷重がかかった際の"
    "ロープの伸びによる支点の沈み込みに十分留意する。"
    "（はしごクレーンでは介添えは厳禁。支点が何かで扱いが変わる）",
]

QUIZ = [
    {
        "question": "10mランヤード付きグリヨンで支点の高さを調整した。この後にとる措置はどれか？",
        "choices": [
            "端末をふた結びにして誤操作と緩みを防ぐ",
            "端末を切り落とす",
            "そのままにして荷重をかける",
            "端末をカラビナで支点に掛ける",
        ],
        "answer": 0,
        "explanation": "支点の高さ調整をした後、端末はふた結びにより誤操作および緩み防止の措置をする。",
    },
    {
        "question": "一箇所吊り担架水平救助で、隊員の介添えについて正しいものはどれか？",
        "choices": [
            "はしごクレーンと同じく厳禁",
            "強固な支点であれば可能。ただし荷重時のロープの伸びによる支点の沈み込みに留意する",
            "担架が揺れるときだけ行う",
            "確保員が2名いれば無条件に行える",
        ],
        "answer": 1,
        "explanation": "強固な支点であれば介添えは可能。ただし荷重がかかった際のロープの伸びで支点が沈み込むことに留意する。三連はしごを支点にするはしごクレーンでは、安定度を考慮して介添えは厳禁。",
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
        if cur == "022" and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur == "022" and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SRC, ensure_ascii=False))
        if cur == "022" and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ:
                q = dict(qid=next_qid(work, "022"), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    it = [x for x in result if x["id"] == "022"][0]
    print("  022 %s" % it["name"])
    print("     知見 %d件（+%d）／ 問題 %d問（+%d）／ 出典 %d件"
          % (len(it["notes"]), len(NOTES), len(it["quiz"]), len(QUIZ), len(it["sources"])))

    PAT = re.compile(r"(特に.*ない|基準はない|^自由|どちらでもよい|どれでもよい|いつでもよい|"
                     r"どこでもよい|決まりはなく|決まりはない|関係しない)")
    bad = [q["qid"] for q in it["quiz"] for i, c in enumerate(q["choices"])
           if i != q["answer"] and PAT.search(c)]
    print("     選ばれにくい誤答: %s" % (bad if bad else "なし"))

    norm = lambda t: re.sub(r"[\s　。、（）()「」？?・]", "", t)
    rows = [(x["id"], q["qid"], q["question"]) for x in result for q in (x.get("quiz") or [])]
    dup = [(a[1], b[1], round(r, 2)) for a, b in itertools.combinations(rows, 2)
           if a[0] == b[0]
           for r in [difflib.SequenceMatcher(None, norm(a[2]), norm(b[2])).ratio()]
           if r >= 0.85]
    print("     質問文が似すぎている組（0.85以上）: %s" % (dup if dup else "なし"))

    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n  合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(result), len(qids)))


if __name__ == "__main__":
    main()
