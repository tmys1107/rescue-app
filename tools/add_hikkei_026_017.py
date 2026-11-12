# -*- coding: utf-8 -*-
"""必携から 026 逆伸梯 / 017 立坑救助 を補強する

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         第I編 9-2 低所への進入法 三連はしごの逆伸ていによる進入 本文 p.135 ／ PDF 147
         第I編 9-3 低所への進入法 ロープによる進入            本文 p.138 ／ PDF 150

   PDF150 は逆伸ていではなく「ロープによる低所進入（逆さ吊り等）」。
   内容としてはマンホール・立て坑への進入なので 017 立坑救助に入れる。

   実行： python tools/add_hikkei_026_017.py
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

SOURCES = {
    "026": "消防救助技術必携 一般救助編（名古屋市消防局）p.135",
    "017": "消防救助技術必携 一般救助編（名古屋市消防局）p.138",
}

NOTES = {
    "026": [
        "【必携】伸てい準備：はしごを縮ていしたまま立て坑内へ協力して下ろす。"
        "隊員①②は確保ロープではしごを確保、隊員③は本体上部を支持、隊員④は引き綱を保持する",
        "【必携】三連目を伸ていするときは、小綱が干渉しないようにする",
        "【必携】二連目の伸てい：隊員③が二連目を引き出して掛金を掛け、小綱で一・二連目を固定する。"
        "隊員④は引き綱がはしごに食い込まないようにする",
        "【必携】三連目の伸てい：二連目の上端が隊員③の腰の位置にくるまではしごを下ろしてから行う。"
        "伸ていしたら小綱で二・三連目を固定する",
        "【必携】着てい：全員ではしごをおおむね75°に着ていし、はしごの上端を小綱で地物に結着する。"
        "確保ロープ、引き綱も地物に結着する",
        "【必携】撤収：引き綱等を解き、全員ではしごを引き寄せて持ち上げる。"
        "隊員③が二・三連目を固定していた小綱を解き、掛金を外して三連目を収納、"
        "同様に二連目を収納してから、はしごを足場に引き上げる",
    ],
    "017": [
        "【必携】逆さ吊りによる進入では、進入隊員の体重が確保ロープおよびカラビナの部分に"
        "かかるようにし、予備確保として縛帯のアタッチメントポイントにも余裕をとって結着しておく",
        "【必携】縛帯を利用せず、ロープで腰・足首を結着する方法もある",
        "【必携】逆さ吊り隊員の活動は5分程度とする。実施する場合は交代要員を待機させ、"
        "専従の連絡員を置いて連絡に当たらせる",
        "【必携】地物・施設等を利用できない場合、進入隊員の確保は複数の隊員により行う。"
        "ロープと地物が接する部分は当て布等で保護する",
        "【必携】地物・施設等を利用できる場合は、ロープを地物へ1〜2回巻き、"
        "その摩擦力を利用して隊員を安全に降下させる。状況に応じて巻く回数を調節する",
        "【必携】つるべ式による降下進入は、他の方法と比べてロープが倍の長さ必要になるが、"
        "脱出・引き上げが容易",
    ],
}

QUIZ = {
    "026": [
        {
            "question": "逆伸ていで三連目を伸ていする前に、はしごをどこまで下ろすか？",
            "choices": [
                "二連目の上端が隊員③の腰の位置にくるまで",
                "二連目の上端が地面に着くまで",
                "一連目が半分隠れるまで",
                "引き綱がたるむまで",
            ],
            "answer": 0,
            "explanation": "二連目の上端が隊員③の腰の位置にくるまではしごを下ろしてから、二連目と同様の操作で三連目を伸ていする。伸ていしたら小綱で二・三連目を固定する。",
        },
        {
            "question": "逆伸ていで着てい（おおむね75°）した後、地物に結着するものはどれか？",
            "choices": [
                "はしごの上端のみ",
                "はしごの上端（小綱）・確保ロープ・引き綱",
                "確保ロープのみ",
                "引き綱のみ",
            ],
            "answer": 1,
            "explanation": "はしごの上端を小綱で地物に結着し、確保ロープと引き綱も地物に結着する。3つとも固定する。",
        },
    ],
    "017": [
        {
            "question": "逆さ吊りで進入する隊員の活動時間の目安はどれか？",
            "choices": ["1分程度", "5分程度", "15分程度", "残圧がなくなるまで"],
            "answer": 1,
            "explanation": "逆さ吊り隊員の活動は5分程度とする。実施する場合は交代要員を待機させ、専従の連絡員を置いて連絡に当たらせる。",
        },
        {
            "question": "低所進入で地物・施設等を利用できる場合、ロープの扱いはどうするか？",
            "choices": [
                "地物へ1〜2回巻き、摩擦力を利用して降下させる",
                "地物に結着してから降下させる",
                "地物には触れさせない",
                "地物へ5回以上巻く",
            ],
            "answer": 0,
            "explanation": "ロープを地物等へ1〜2回巻き、その摩擦力を利用して隊員を安全に降下させる。状況に応じて巻く回数を調節する。地物と接する部分は当て布等で保護する。",
        },
    ],
}


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
    if SOURCES["026"] in src:
        print("既に取り込み済み。何もしない")
        return

    lines = src.split("\n")
    out, cur, work = [], None, src
    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)
        if cur in NOTES and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES[cur]:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur in SOURCES and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SOURCES[cur], ensure_ascii=False))
        if cur in QUIZ and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ[cur]:
                q = dict(qid=next_qid(work, cur), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    PAT = re.compile(r"(特に.*ない|基準はない|^自由|どちらでもよい|どれでもよい|いつでもよい|"
                     r"どこでもよい|決まりはなく|決まりはない|関係しない)")
    for i in ("026", "017"):
        it = [x for x in result if x["id"] == i][0]
        bad = [q["qid"] for q in it["quiz"] for k, c in enumerate(q["choices"])
               if k != q["answer"] and PAT.search(c)]
        print("  %s %-22s 知見%2d 問題%d 出典%d  捨て札:%s"
              % (i, it["name"], len(it["notes"]), len(it["quiz"]),
                 len(it.get("sources") or []), bad if bad else "なし"))

    norm = lambda t: re.sub(r"[\s　。、（）()「」？?・]", "", t)
    rows = [(x["id"], q["qid"], q["question"]) for x in result for q in (x.get("quiz") or [])]
    dup = [(a[1], b[1], round(r, 2)) for a, b in itertools.combinations(rows, 2)
           if a[0] == b[0]
           for r in [difflib.SequenceMatcher(None, norm(a[2]), norm(b[2])).ratio()]
           if r >= 0.85]
    print("\n  質問文が似すぎている組（0.85以上）: %s" % (dup if dup else "なし"))
    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("  合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(result), len(qids)))


if __name__ == "__main__":
    main()
