# -*- coding: utf-8 -*-
"""操法14件を、使う資器材と場面でサブカテゴリに分ける（1回だけ実行する移行スクリプト）

   それまでは全14件が「操法・救助方法」1つだったため、絞り込みが効かなかった。

   分け方は本文に出てくる語の数で裏を取っている（tools/ でなく会議の記録は
   ~/.claude/agents/カカシ_experience.md 参照）。例：
     018 背負い救出  … 梯×5 / ロープ×2、purpose も「2階等からの背負い搬送」→ はしご救助
     027 車上伸梯    … 梯×8 / 車両×3、車上で梯子を扱う操法          → はしご救助
     017 立坑救助    … 呼吸器×4、purpose が「酸素欠乏危険場所での進入」→ 検索・進入

   json.load → json.dump で書き戻すと手書きの整形が崩れるので、行単位で置換する。

   実行： python tools/set_ops_category.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")

OLD = "操法・救助方法"

MAP = {
    "015": "はしご救助",   # 応急はしご救助
    "018": "はしご救助",   # 背負い救出（2階等から梯子で背負い搬送）
    "021": "はしご救助",   # はしごクレーン救助
    "024": "はしご救助",   # はしご水平救助 第1法
    "025": "はしご救助",   # はしご水平救助 第2法
    "026": "はしご救助",   # 逆伸梯
    "027": "はしご救助",   # 車上伸梯
    "019": "ロープ救助",   # ロープ展張（渡過ロープ）
    "020": "ロープ救助",   # つるべ式引き上げ救助
    "022": "ロープ救助",   # 一箇所吊り水平救助
    "023": "ロープ救助",   # 斜めロープブリッジ救出
    "016": "検索・進入",   # 検索救助（一法）
    "017": "検索・進入",   # 立坑救助（マンホール救助）
    "011": "車両事故",     # 車両破壊（ドア・屋根の開放）
}

ID_LINE = re.compile(r'^\s*"id"\s*:\s*"([^"]+)"')
CAT_LINE = re.compile(r'^(\s*)"category"\s*:\s*"([^"]+)"(,?)\s*$')


def main():
    with open(PATH, encoding="utf-8") as f:
        src = f.read()

    if OLD not in src:
        print("「%s」が無い。既に分類済みとみて何もしない" % OLD)
        return

    out = []
    cur = None
    changed = []
    for line in src.split("\n"):
        m = ID_LINE.match(line)
        if m:
            cur = m.group(1)
        c = CAT_LINE.match(line)
        if c and c.group(2) == OLD:
            if cur not in MAP:
                print("★ %s に対応表が無い。そのままにする" % cur)
            else:
                line = '%s"category": "%s"%s' % (c.group(1), MAP[cur], c.group(3))
                changed.append((cur, MAP[cur]))
        out.append(line)

    with open(PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    # 書き戻した結果を必ず読み直して確かめる
    with open(PATH, encoding="utf-8") as f:
        items = json.load(f)

    print("%d件を付け替え / JSON再読込 OK（%d件）\n" % (len(changed), len(items)))

    import collections
    for t in ("資器材", "操法・訓練"):
        grp = collections.Counter(it["category"] for it in items if it.get("type") == t)
        print("【%s】%d件" % (t, sum(grp.values())))
        for k, v in grp.most_common():
            n = sum(len(it.get("quiz") or []) for it in items
                    if it.get("type") == t and it["category"] == k)
            print("    %-14s %2d件（問題 %2d問）" % (k, v, n))
        print()

    left = [it["id"] for it in items if it.get("category") == OLD]
    print("未分類の残り: %s" % (", ".join(left) if left else "なし"))


if __name__ == "__main__":
    main()
