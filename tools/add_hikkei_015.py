# -*- coding: utf-8 -*-
"""必携から 015 応急はしご救助 を補強する（従来型＋都市型）

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         第I編 10-3 応急はしご救助        本文 p.145〜146 ／ PDF 157〜158
         第Ⅱ編  8-1 応急はしご救助（都市型） 本文 p.239    ／ PDF 251

   必携には同じ操法が従来型と都市型の2通り載っている。
   アプリは平田さんのメモと訓練記録が元で従来型中心なので、
   都市型との違い（セミスタティックロープ・ピタゴール・身体確保）を補う。

   実行： python tools/add_hikkei_015.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC = "消防救助技術必携 一般救助編（名古屋市消防局）p.145〜146・239"

NOTES = [
    "【必携】救助ロープは結索部をベルトに挟み込んで搬送する。ロープを折ってベルトに通すのは、"
    "救助ロープが障害物等に引っ掛かっても登てい者が転落しないため",
    "【必携】結索部は上部の横さんの間を通し、上で待機している隊員に渡す（作業姿勢をとる）",
    "【必携】三重もやい結びは、ロープが要救助者の両脇・両膝の裏に確実に当たるように縛着し、"
    "痛みを軽減させるよう心掛ける",
    "【必携】確保隊員は、はしごの基底部中央付近に足を掛ける",
    "【必携】進入隊員は要救助者を吊り上げたあと、結索部分・支点・要救助者の様子に異常がないか確認する",
    "【必携】進入隊員は、はしごの両主かんを持って前に押し出す",
    "【必携】救出時に救助ロープを急激に制動すると、要救助者の負担が増すとともに、"
    "はしご横さんが破壊するおそれがある",
    "【必携】地上1mほどの位置に近づいたら、要救助者を静かに降ろし、安全な場所に搬送する",
    "【必携・都市型】都市型の応急はしご救助は、三連はしご／セミスタティックロープ（白色）／"
    "レスキュートライアングル（ピタゴール）を使う。メインロープにセミスタティックロープ、"
    "確保は身体確保、救出器具はピタゴール。従来型（三つ打ちロープ＋三重もやい結び＋肩確保）"
    "との違いはこの3点",
]

QUIZ = [
    {
        "question": "救助ロープを折ってベルトに通して搬送するのは、なぜか？",
        "choices": [
            "ロープが汚れないようにするため",
            "障害物等に引っ掛かっても登てい者が転落しないため",
            "ロープの長さを調整するため",
            "結索部を保護するため",
        ],
        "answer": 1,
        "explanation": "救助ロープが障害物等に引っ掛かっても、登てい者が引かれて転落しないようにするため。結索部はベルトに挟み込んで搬送する。",
    },
    {
        "question": "救出時に救助ロープを急激に制動すると、何が起きるか？",
        "choices": [
            "要救助者の負担が増し、はしご横さんが破壊するおそれがある",
            "降下速度が安定する",
            "確保隊員の負担が軽くなる",
            "支点の摩擦が減る",
        ],
        "answer": 0,
        "explanation": "急激な制動は要救助者の負担を増やすうえ、荷重がはしご横さんに集中して破壊するおそれがある。「ゆるめは手をするだけ」と同じ理屈。",
    },
    {
        "question": "都市型の応急はしご救助が、従来型と違う点はどれか？",
        "choices": [
            "三連はしごを使わない",
            "セミスタティックロープ（白色）とピタゴールを使い、身体確保で確保する",
            "要救助者を縛着しない",
            "基底部を固定しない",
        ],
        "answer": 1,
        "explanation": "都市型はメインロープにセミスタティックロープ（白色）、救出器具にレスキュートライアングル（ピタゴール）、確保は身体確保。従来型は三つ打ちロープ＋三重もやい結び＋肩確保。三連はしごを使う点は共通。",
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
        if cur == "015" and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur == "015" and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SRC, ensure_ascii=False))
        if cur == "015" and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ:
                q = dict(qid=next_qid(work, "015"), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    it = [x for x in result if x["id"] == "015"][0]
    print("  015 %s" % it["name"])
    print("     知見 %d件（+%d）／ 問題 %d問（+%d）／ 出典 %d件"
          % (len(it["notes"]), len(NOTES), len(it["quiz"]), len(QUIZ), len(it["sources"])))
    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n  合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(result), len(qids)))


if __name__ == "__main__":
    main()
