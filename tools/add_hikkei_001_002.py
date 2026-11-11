# -*- coding: utf-8 -*-
"""消防救助技術必携から 001 油圧カッター / 002 油圧スプレッダー を補強する

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         3-7 大型油圧切断機（ホルマトロカッター）  本文 p.327 ／ PDF 339
         2-11 大型油圧スプレッダー（ホルマトロスプレッダー） 本文 p.302 ／ PDF 314

   判断
     002 … 必携の SP4240C と、最大開幅686mm・最大展開力18.8t・最小展開力4.4t・
            最大引張力9.2t・最大押し潰し力6.6t・作動圧力72MPa が全て一致した。
            同型とみて質量を 16kg（誤り）→ 18.1kg に訂正し、型式と寸法を補う。
     001 … 必携は CU4050C NCTⅡ（927kN・181mm）。当隊の 580kN・210mm と合わず
            別型式。数値は上書きせず「要確認」のまま、必携の値は参考として残す。

   どちらもセーフティポイントは型式に依らないので取り込む。

   実行： python tools/add_hikkei_001_002.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SRC_CUT = "消防救助技術必携 一般救助編（名古屋市消防局）p.327"
SRC_SPR = "消防救助技術必携 一般救助編（名古屋市消防局）p.302"

SPEC_FIX = (
    '      "質量": "16 kg（要確認）",',
    '      "型式": "SP4240C",\n'
    '      "質量": "18.1 kg",\n'
    '      "寸法": "長さ771 × 幅316 × 高さ206 mm",',
)

NOTES = {
    "001": [
        "【必携】必携に載っているのは CU4050C NCTⅡ（質量18.1kg・刃先開き幅181mm・"
        "最大切断力927kN＝95t・作動圧力72MPa・寸法775×270×218mm）。"
        "当隊の値（580kN・210mm）とは合わないので別型式。諸元は銘板で確認する",
        "【必携】切断物体と刃先が90°になるようにして、最も持ちやすい位置で保持する。"
        "機器に体を持っていかれないようしっかり保持する",
        "【必携】ホースを極端に曲げたり、ねじったりしてはいけない（最小曲げ半径70mm）",
        "【必携】安全弁からオイルが吹き出すことがあるが、これは機器の故障ではない。"
        "多くはポンプからカッターに至る接続部のいずれかが接合不完全なときに起こる",
        "【必携】ハンドル軸は切断可能だが、ハンドルが勢いよく飛ぶことがあるため注意する。"
        "特殊強化鋼で作られたペダル・スプリング等は切断不可",
        "【必携】カッターは切断する物体が最奥部のくぼみに当たるときに最高の能力を発揮する。"
        "丸棒鋼では41mm程度まで切断可能",
        "【必携】切断中、刃先の広がりが5mm程度になるとほぼ能力の限界",
        "【必携】カップリングが接続できないときは、前回取り外したホース内に油圧が"
        "残っている場合がある。排圧用リリースバルブでホースから圧を抜く",
    ],
    "002": [
        "【必携】必携の SP4240C と諸元が完全に一致した（最大開幅686mm・最大展開力18.8t・"
        "最小展開力4.4t・最大引張力9.2t・最大押し潰し力6.6t・作動圧力72MPa）。"
        "質量はメモにあった16kgではなく18.1kgが正しい",
        "【必携】滑り止めのある先端のスプレッドチップ部を使用する。"
        "アーム部での作業は危険を伴うので行ってはならない",
        "【必携】スプレッダーでの持ち上げ操作は原則として行わない。やむを得ず行う場合は、"
        "持ち上げる重量物の落下防止の措置を当て木等で行う",
        "【必携】ホースを極端に曲げたり、ねじったりしてはいけない（最小曲げ半径70mm）",
        "【必携】作動油の温度が60℃以上の状態で使用すると、油漏れを起こすことがある",
        "【必携】ポンプへの還流ラインがつまった場合、安全弁から油が出る。"
        "重要な役割をしているので、いかなる場合でも安全弁には触らない",
        "【必携】カップリングが接続できないときは、前回取り外したホース内に油圧が"
        "残っている場合がある。排圧用リリースバルブでホースから圧を抜く",
    ],
}

QUIZ = {
    "001": [
        {
            "question": "油圧カッターで丸棒鋼を切断する場合、切断可能な太さの目安はどれか？",
            "choices": ["21mm程度", "31mm程度", "41mm程度", "51mm程度"],
            "answer": 2,
            "explanation": "丸棒鋼では41mm程度まで切断可能。カッターは切断する物体が最奥部のくぼみに当たるときに最高の能力を発揮する。刃先の広がりが5mm程度になるとほぼ限界。",
        },
        {
            "question": "カップリングが接続できないとき、まず疑うことはどれか？",
            "choices": [
                "前回取り外したホース内に油圧が残っている",
                "ポンプの燃料が切れている",
                "刃が摩耗している",
                "作動油が不足している",
            ],
            "answer": 0,
            "explanation": "前回取り外したホース内に油圧が残っている場合がある。排圧用リリースバルブを使ってホースから圧を抜く。",
        },
    ],
    "002": [
        {
            "question": "油圧スプレッダーで作業してはならない部位はどれか？",
            "choices": [
                "先端のスプレッドチップ部",
                "アーム部",
                "操作ハンドル",
                "高圧ホースの接続部",
            ],
            "answer": 1,
            "explanation": "滑り止めのある先端のスプレッドチップ部を使用する。アーム部での作業は危険を伴うので行ってはならない。",
        },
        {
            "question": "スプレッダーでの持ち上げ操作について正しいものはどれか？",
            "choices": [
                "能力が高いので積極的に持ち上げに使う",
                "原則として行わない。やむを得ない場合は当て木等で落下防止措置をとる",
                "2台同時なら持ち上げてよい",
                "展開力の半分までなら持ち上げてよい",
            ],
            "answer": 1,
            "explanation": "スプレッダーでの持ち上げ操作は原則として行わない。やむを得ず行う場合は、持ち上げる重量物の落下防止の措置を当て木等で行う。",
        },
    ],
}

SOURCES = {"001": SRC_CUT, "002": SRC_SPR}


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
    if SRC_CUT in src:
        print("既に取り込み済み。何もしない")
        return

    assert SPEC_FIX[0] in src, "002 の質量行が見つからない"
    src = src.replace(SPEC_FIX[0], SPEC_FIX[1], 1)

    lines = src.split("\n")
    out = []
    cur = None
    work = src
    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)
        if cur in NOTES and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES[cur]:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur in QUIZ and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ[cur]:
                q = dict(qid=next_qid(work, cur), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")
        if cur in SOURCES and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SOURCES[cur], ensure_ascii=False))

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    items = json.load(io.open(PATH, encoding="utf-8"))
    for i in ("001", "002"):
        it = [x for x in items if x["id"] == i][0]
        print("%s %s" % (i, it["name"]))
        print("   質量 : %s" % it["spec"].get("質量"))
        print("   知見 : %d件 ／ 問題 %d問 ／ 出典 %d件"
              % (len(it["notes"]), len(it["quiz"]), len(it.get("sources") or [])))
    qids = [q["qid"] for x in items for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(items), len(qids)))


if __name__ == "__main__":
    main()
