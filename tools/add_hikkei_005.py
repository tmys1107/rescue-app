# -*- coding: utf-8 -*-
"""消防救助技術必携（一般救助編・名古屋市消防局）から 005 三連はしご を補強する

   出典：P:\\消防\\訓練資料\\三宅資料\\消防救助技術必携. 一般救助編 [名古屋市].pdf
         1-2 三連はしご（本文 p.267 ／ PDF 279ページ）

   やったこと
     ・「35 kg（要確認）」を確定値にした。必携の主要諸元表で チタン製3.5-8.7m＝35kg を確認
     ・材質別の諸元、取扱方法、セーフティポイントを知見に追加

   注意
     必携は名古屋市消防局のもの。材質別の表は「一般にこういう型がある」という
     参考であって、自分の隊のはしごがどれかは銘板で確認すること。
     ただし 3.5-8.7m・チタン製という条件は一致しているので、35kg は確度が高い。

   json.load → json.dump で書き戻すと手書きの整形が崩れるため、行単位で挿入する。

   実行： python tools/add_hikkei_005.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC = "消防救助技術必携 一般救助編（名古屋市消防局）p.267"

OLD_MASS = '"質量": "35 kg（要確認）"'
NEW_MASS = '"質量": "35 kg"'

ADD_NOTES = [
    "【必携】主要諸元は材質で異なる。銅製 3.1〜7.3m・32kg／チタン製 3.5〜8.7m・35kg／"
    "チタン製 3.2〜7.7m・29kg／アルミ製 3.5〜8.7m・24kg。最大許容荷重はいずれも二人又は1.8kN",
    "【必携】最大許容荷重（二人又は1.8kN）は、立てかけ（75°）のときの分散荷重の値",
    "【必携】架ていするときは、左右の傾斜のない場所を選ぶ",
    "【必携】伸てい及び縮ていは、はしごを垂直にして行う",
    "【必携】必要な長さに伸ていしたら、掛金が完全に作動しているか確認し、"
    "引き綱をたるみなく引っ張って一連目の横さんに結着する",
    "【必携】架てい時はてい体を支持し、状況に応じて先端を地物に固定する",
    "【必携】縮ていするときは、一旦引き綱を引いて掛金を外してから、引き綱を緩める",
    "【必携】縮ていは静かに行い、引き綱を一気に緩めない。滑車から引き綱が外れたり、"
    "衝撃によるはしごの変形が起きる",
    "【必携】通常は横さんを交互に握り一段ずつ登るが、資器材等を携行する場合は"
    "裏主かんを引きつけながら登る",
]

ADD_QUIZ = [
    {
        "question": "三連はしごの最大許容荷重「二人又は1.8kN」は、どの状態での値か？",
        "choices": [
            "水平に架ていしたときの集中荷重",
            "立てかけ（75°）のときの分散荷重",
            "垂直に立てたときの最大荷重",
            "角度に関係なく一定",
        ],
        "answer": 1,
        "explanation": "最大許容荷重は立てかけ（75°）の分散である。極端な低角度や水平状態では原則として使用しない。荷重をかけすぎると接合部の主かんが折損する。",
    },
    {
        "question": "三連はしごを縮ていするときの正しい手順はどれか？",
        "choices": [
            "引き綱をそのまま一気に緩める",
            "一旦引き綱を引いて掛金を外してから、静かに緩める",
            "はしごを傾けたまま引き綱を緩める",
            "掛金を外さずに押し下げる",
        ],
        "answer": 1,
        "explanation": "一旦引き綱を引いて掛金を外してから緩める。一気に緩めると滑車から引き綱が外れたり、衝撃ではしごが変形する。伸てい・縮ていははしごを垂直にして行う。",
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
    if "【必携】" in src:
        print("既に取り込み済み。何もしない")
        return
    assert OLD_MASS in src, "質量の（要確認）が見つからない"

    src = src.replace(OLD_MASS, NEW_MASS, 1)

    lines = src.split("\n")
    out = []
    cur = None
    work = src
    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)
        if cur == "005" and re.match(r'^\s*"notes": \[\s*$', line):
            for v in ADD_NOTES:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur == "005" and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in ADD_QUIZ:
                q = dict(qid=next_qid(work, "005"), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")
        if cur == "005" and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SRC, ensure_ascii=False))

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    items = json.load(io.open(PATH, encoding="utf-8"))
    it = [x for x in items if x["id"] == "005"][0]
    print("005 三連はしご")
    print("  質量 : %s" % it["spec"]["質量"])
    print("  知見 : %d件（+%d）" % (len(it["notes"]), len(ADD_NOTES)))
    print("  問題 : %d問（+%d） %s" % (len(it["quiz"]), len(ADD_QUIZ), [q["qid"] for q in it["quiz"]][:2]))
    print("  出典 : %s" % " / ".join(it["sources"]))
    qids = [q["qid"] for x in items for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(items), len(qids)))


if __name__ == "__main__":
    main()
