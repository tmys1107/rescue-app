# -*- coding: utf-8 -*-
"""必携から 003 熱画像直視装置 / 004 マット型空気ジャッキ を補強する

   出典：消防救助技術必携 一般救助編（名古屋市消防局）
         6-3 熱画像直視装置（アルゴス3） p.383 ／ 6-4（アルゴス4） p.386
         2-7 マット型空気ジャッキ（マキシーフォースエアーバッグ） p.289〜291

   判断
     003 … アルゴス3（2.1kg・2時間以上）、アルゴス4（1.7kg・2時間以上）のいずれも
            当隊の 1.2kg・約4時間 と合わない。別機種なので数値は上書きしない。
            「窓越しには使用できない」等、機種に依らない事項だけ取り込む。
     004 … 安全弁0.8MPa・重ねは2枚まで・大の上に小・下から膨らます が
            平田さんのメモと完全に一致。諸元のKPI表は参考として残し、
            当隊の 12kg・430kN・450mm は銘板確認が要るので要確認のまま。

   実行： python tools/add_hikkei_003_004.py
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
    "003": "消防救助技術必携 一般救助編（名古屋市消防局）p.383・386",
    "004": "消防救助技術必携 一般救助編（名古屋市消防局）p.289〜291",
}

NOTES = {
    "003": [
        "【必携】ガラスは長い波長の赤外線を透過しないので、窓越しには使用できない",
        "【必携】必携に載っているのはアルゴス3（質量2.1kg・バッテリー2時間以上）と"
        "アルゴス4（1.7kg・2時間以上）。当隊の値（1.2kg・約4時間）とは合わないので別機種。"
        "諸元は銘板で確認する",
        "【必携】アルゴス3・4とも視野角は水平50°、モニターは4インチフルカラーLCD",
        "【必携】動作環境はアルゴス3が60℃で1時間以上・150℃で10分、"
        "アルゴス4が60℃で1時間以上・150℃で15分",
        "【必携】アルゴス3は完全充電でバッテリー表示が5本のバー。2本になると約1時間の動作容量。"
        "「LOW BATTERY」警告が出たら残り約10分",
        "【必携】アルゴス4はメモリー効果を防ぐため10回に1回はバッテリーをリフレッシュする"
        "（電池方式によるので当隊の機種では要確認）",
    ],
    "004": [
        "【必携】安全弁の設定圧力は0.8MPa。レギュレーターの圧力調整コックを右に回して"
        "低圧ゲージを0.8MPaに調整する",
        "【必携】バッグ内に余分なエアーが供給されると自動的に安全弁が作動し、"
        "空気が抜けて「シュー」という音がする。音がしたらコントロールバルブを閉じる",
        "【必携】膨らませるときは、ゆっくり徐々に膨らませる",
        "【必携】エアーバッグの中心が、対象物の真下にくるように設定する",
        "【必携】エアーバッグの接地面は曲面になるため、対象物が動いたりバッグが"
        "はじき出されることがある。慎重に作業する",
        "【必携】押し広げに使う場合、対象物がもろい材質だと割れて飛ぶことがある",
        "【必携】重ね使用は2枚まで。持ち上げ時は大きいバッグの上に小さいバッグを重ね、"
        "バッグの中心を合わせる。膨らますときは下のバッグから",
        "【必携】最大持ち上げ能力 ＝ 1cm²あたり8kg × バッグの接地面積。"
        "大きいバッグほど持ち上げ能力も揚程も大きい",
        "【必携】最大揚程は「荷重をかけない空の状態で0.8MPaをかけたときの膨らみ幅」。"
        "物体が重いほど接触面積が大きくなるため、実際の揚程はこれより小さくなる",
        "【必携】マキシーフォースの諸元（参考）KPI-17 5.0kg/164kN/揚程233mm、"
        "KPI-22 6.8kg/210.3kN/282mm、KPI-32 9.5kg/306.7kN/333mm、"
        "KPI-44 13.0kg/422.5kN/394mm、KPI-74 27.0kg/697.4kN/508mm。"
        "当隊の値（12kg・430kN・450mm）はKPI-44に近いが一致しないので銘板で確認する",
    ],
}

QUIZ = {
    "003": [{
        "question": "熱画像直視装置を窓の外から室内に向けて使いたい。正しいのはどれか？",
        "choices": [
            "ガラス越しでも問題なく使える",
            "ガラスは長い波長の赤外線を透過しないので使えない",
            "ガラスが薄ければ使える",
            "角度を変えれば使える",
        ],
        "answer": 1,
        "explanation": "ガラスは長い波長の赤外線を透過しないので、窓越しには使用できない。開口部を作るか、別の位置から測る必要がある。",
    }],
    "004": [
        {
            "question": "マット型空気ジャッキの「最大揚程」とは、どの状態で測った値か？",
            "choices": [
                "最大荷重をかけた状態",
                "荷重をかけない空の状態で0.8MPaをかけたときの膨らみ幅",
                "2枚重ねたときの合計の高さ",
                "安全弁が作動するまで膨らませた高さ",
            ],
            "answer": 1,
            "explanation": "荷重をかけない空の状態で0.8MPaをかけたときの膨らみ幅が最大揚程。物体が重いほど接触面積が大きくなるため、実際の揚程はこれより小さくなる。",
        },
        {
            "question": "バッグを膨らませていたら「シュー」という音がした。何が起きているか？",
            "choices": [
                "バッグが破損して空気が漏れている",
                "安全弁が作動して余分な空気が抜けている",
                "ホースの接続が外れかけている",
                "ボンベの残圧が切れた",
            ],
            "answer": 1,
            "explanation": "バッグ内に余分なエアーが供給されると自動的に安全弁が作動し、空気が抜けて「シュー」という音がする。音がしたらコントロールバルブを閉じる。",
        },
        {
            "question": "バッグを2枚重ねて持ち上げるときの正しい手順はどれか？",
            "choices": [
                "小さいバッグの上に大きいバッグを重ね、上から膨らます",
                "大きいバッグの上に小さいバッグを重ね、中心を合わせて下から膨らます",
                "同じ大きさを2枚重ね、同時に膨らます",
                "3枚まで重ねてよい",
            ],
            "answer": 1,
            "explanation": "重ねは2枚まで。持ち上げ時は大きいバッグの上に小さいバッグを重ね、バッグの中心を合わせる。膨らますときは下のバッグから。",
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
    if SOURCES["004"] in src:
        print("既に取り込み済み。何もしない")
        return

    items = {x["id"]: x for x in json.loads(src)}
    lines = src.split("\n")
    out, cur, work = [], None, src
    need_notes = {i for i in NOTES if not items[i].get("notes")}
    need_src = {i for i in SOURCES if not items[i].get("sources")}

    for line in lines:
        m = re.match(r'^\s*"id": "(\d+)"', line)
        if m:
            cur = m.group(1)
        out.append(line)

        if cur in NOTES and cur not in need_notes and re.match(r'^\s*"notes": \[\s*$', line):
            for v in NOTES[cur]:
                out.append('      %s,' % json.dumps(v, ensure_ascii=False))
        if cur in SOURCES and cur not in need_src and re.match(r'^\s*"sources": \[\s*$', line):
            out.append('      %s,' % json.dumps(SOURCES[cur], ensure_ascii=False))

        # notes / sources が無い項目（003）は quiz の直前にまとめて作る
        if cur in need_notes and re.match(r'^\s*"quiz": \[\s*$', line):
            out.pop()
            out.append('    "notes": [')
            for k, v in enumerate(NOTES[cur]):
                out.append('      %s%s' % (json.dumps(v, ensure_ascii=False),
                                           "," if k < len(NOTES[cur]) - 1 else ""))
            out.append('    ],')
            if cur in need_src:
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
    for i in ("003", "004"):
        it = [x for x in result if x["id"] == i][0]
        print("  %s %-24s 知見%2d 問題%d 出典%d"
              % (i, it["name"][:22], len(it.get("notes") or []), len(it["quiz"]),
                 len(it.get("sources") or [])))
    qids = [q["qid"] for x in result for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids)), "qid重複"
    print("\n  合計 %d件 / 問題 %d問 ／ qid重複なし" % (len(result), len(qids)))


if __name__ == "__main__":
    main()
