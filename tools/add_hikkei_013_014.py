# -*- coding: utf-8 -*-
"""必携から 013 カラビナ / 014 空気呼吸器 を補強する

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         3-1 カラビナ等        本文 p.53〜56 ／ PDF 65〜68
         4-1 空気呼吸器(K2P型)  本文 p.345   ／ PDF 357

   013 の「1.3kN は低すぎる、1.3t の誤記では」という疑義が解けた。
   必携の強度表では
       メーカーの許容荷重      縦 1.3kN ／ 横 保証しない
       引張強度試験の実測値    縦 20.0〜22.0kN ／ 横 4.0kN未満（破損箇所はピン部）
   とあり、1.3kN は破断強度ではなく許容荷重。数値は正しかったので要確認を外す。

   014 の当隊のボンベ（8.4L/14.7MPa、4.7L/29.4MPa）は必携のK2P型（5L/30MPa）と
   別仕様。諸元は上書きせず、点検・着装の要領だけ取り込む。

   実行： python tools/add_hikkei_013_014.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

SOURCES = {
    "013": "消防救助技術必携 一般救助編（名古屋市消防局）p.53〜56",
    "014": "消防救助技術必携 一般救助編（名古屋市消防局）p.345",
}

# (置換前, 置換後)
REPLACE = [
    ('      "耐荷重（縦方向）": "1.3 kN（要確認）",',
     '      "許容荷重（縦方向）": "1.3 kN（メーカー許容荷重）",\n'
     '      "引張強度 実測値（縦）": "20.0〜22.0 kN",\n'
     '      "引張強度 実測値（横）": "4.0 kN未満（破損箇所はピン部）",\n'
     '      "質量": "160 g",\n'
     '      "寸法": "縦109 × 横56 mm（ゲート開き19mm・線径10φ）",'),
    ('"各部名称": "本体・キャッチ・開閉かん・ゲート・パーラー鋲"',
     '"各部名称": "本体・キャッチ・開閉かん・安全環・ピン・パーカービョウ"'),
    ('      "耐荷重のメモ原文は1.3kNだが、ロープ（2.8kN）より低い値になり不自然。'
     '単位の誤記（1.3t）の可能性があるため銘板で要確認",',
     '      "【必携】1.3kNはメーカーの許容荷重であって破断強度ではない。'
     '引張強度試験の実測値は縦20.0〜22.0kN。許容荷重（使用条件を考慮して算出した安全に使用可能な最大荷重）と'
     '破壊する荷重には差が生じる。ロープの2.8kNより小さく見えるのはこのため",'),
]

NOTES = {
    "013": [
        "【必携】縦方向に引っ張った場合、①縦方向に伸びる → ②ピン部の破損"
        "（ピンが折れる・ピンが外れる）の順で壊れる",
        "【必携】横方向はメーカーが強度を保証していない。実測でも4.0kN未満で、縦方向に比べて極めて小さい",
        "【必携】使用時は必ず安全環を締める。締めない場合は約15.0kNで破壊し、"
        "締めた場合と比べて約5.0kNの強度低下になる",
        "【必携】認定基準では、14.0kNで縦方向に引っ張っても使用上支障のある永久変形等がなく、"
        "最大引張荷重が20.0kN以上であることとされている",
        "【必携】D型はO型より強度が高い。力が加わる点からピンまでの距離が長いため",
        "【必携】材質は、本体・キャッチ・安全環が一般構造用圧延鋼材SS41、開閉かんがいおう快削鋼SUM23、"
        "ピンがステンレス鋼SUS430、パーカービョウが炭素鋼線SWCH15R。表面は一般にニッケルクロムメッキ",
    ],
    "014": [
        "【必携】そく止弁は全開してから圧力を確認し、半回転〜1回転戻す。そく止弁の破損を防止するため",
        "【必携】背負うときは、吸気管と肩バンドを一緒に持つ",
        "【必携】ボンベ装着時の点検：連結ナットのOリングを点検し（傷んでいれば交換）、"
        "高圧導管の連結ナットが締まっていることを確認する",
        "【必携】陽圧機能の点検：そく止弁を開放し、陽圧ロックレバーを OFF → ON → OFF と切り替え、"
        "ONのとき面体から勢いよく空気が噴出することを確認する。空気の消費を抑えるため切替えは素早く行う",
        "【必携】機能性の点検：そく止弁を閉じ、調整器の圧力指示計の針の変化を確認する。"
        "約1分間実施して約1目盛程度の変化であればおおむね良好",
        "【必携】必携のK2P型は 空気量1500L・ボンベ5L・30MPa・着装質量12.6kg・"
        "使用時間24分（呼吸量毎分50L、残圧6MPa）・警報器始動圧6MPa。"
        "当隊のボンベ（8.4L/14.7MPa、4.7L/29.4MPa）とは別仕様",
    ],
}

QUIZ = {
    "013": [
        {
            "question": "カラビナの「1.3kN」は何を表す値か？",
            "choices": [
                "破断強度",
                "メーカーの許容荷重",
                "横方向の強度",
                "認定基準の最低値",
            ],
            "answer": 1,
            "explanation": "1.3kNはメーカーの許容荷重であって破断強度ではない。引張強度試験の実測値は縦20.0〜22.0kN。許容荷重と破壊する荷重には差が生じる。",
        },
        {
            "question": "安全環を締めずにカラビナを使うと、強度はどうなるか？",
            "choices": [
                "変わらない",
                "約15.0kNで破壊し、締めた場合より約5.0kN低下する",
                "半分以下になる",
                "横方向と同じ強度になる",
            ],
            "answer": 1,
            "explanation": "引張強度試験の実測値によれば、安全環を締めない場合は約15.0kNの力で破壊する。締めた場合（20.0〜22.0kN）と比べて約5.0kNの強度低下になる。",
        },
    ],
    "014": [
        {
            "question": "そく止弁を全開したあと半回転〜1回転戻すのはなぜか？",
            "choices": [
                "空気の流量を絞るため",
                "そく止弁の破損を防止するため",
                "残圧を調整するため",
                "警報器を作動させるため",
            ],
            "answer": 1,
            "explanation": "全開のまま固着させると破損するおそれがあるため、圧力を確認した後に半回転〜1回転戻す。",
        },
        {
            "question": "機能性の点検で、そく止弁を閉じて圧力指示計を見る。良好と判断できるのはどれか？",
            "choices": [
                "針がまったく動かない",
                "約1分間で約1目盛程度の変化",
                "約1分間で半分まで下がる",
                "針が振れ続ける",
            ],
            "answer": 1,
            "explanation": "そく止弁を閉じ、約1分間実施して約1目盛程度の変化であればおおむね良好。大きく下がる場合はどこかで漏れている。",
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
    if SOURCES["013"] in src:
        print("既に取り込み済み。何もしない")
        return

    for a, b in REPLACE:
        assert a in src, "見つからない: %s" % a[:50]
        src = src.replace(a, b, 1)

    items = {x["id"]: x for x in json.loads(src)}
    lines = src.split("\n")
    out, cur, work = [], None, src
    need_src = {i for i in SOURCES if not items[i].get("sources")}

    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)

        if cur in NOTES and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES[cur]:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur in SOURCES and cur not in need_src and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SOURCES[cur], ensure_ascii=False))

        if cur in need_src and re.match(r'^\s*"quiz": \[\s*$', line):
            out.pop()
            out.append('    "sources": [')
            out.append('      %s' % json.dumps(SOURCES[cur], ensure_ascii=False))
            out.append('    ],')
            out.append(line)

        if cur in QUIZ and re.match(r'^\s*"quiz": \[\s*$', line):
            for q in QUIZ[cur]:
                q = dict(qid=next_qid(work, cur), **q)
                work += '"qid": "%s"' % q["qid"]
                out.append("      " + j(q, 6) + ",")

    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))

    result = json.load(io.open(PATH, encoding="utf-8"))
    for i in ("013", "014"):
        it = [x for x in result if x["id"] == i][0]
        print("  %s %-14s 知見%2d 問題%d 出典%d"
              % (i, it["name"], len(it.get("notes") or []), len(it["quiz"]),
                 len(it.get("sources") or [])))
        for k, v in (it.get("spec") or {}).items():
            if "許容" in k or "引張" in k:
                print("        %s = %s" % (k, v))
    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    left = sum(1 for x in result for v in (x.get("spec") or {}).values() if "要確認" in str(v))
    print("\n  合計 %d件 / 問題 %d問 ／ 要確認の残り %d件" % (len(result), len(qids), left))


if __name__ == "__main__":
    main()
