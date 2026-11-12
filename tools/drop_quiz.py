# -*- coding: utf-8 -*-
"""equipment.json から、指定した qid の設問ブロックだけを安全に取り除く

   正規表現の .*? で消そうとすると、閉じ括弧の対応を見ないので
   隣の項目まで巻き込んで消える（実際に 28件→27件 になった）。
   そのため、qid の行を見つけてから波括弧を数えてブロックの終わりを決める。

   使い方： python tools/drop_quiz.py 002-q4 020-q5
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HERE, "data", "equipment.json")


def drop(lines, qid):
    """qid を含む { … } のブロックを、直前の行から閉じ括弧まで消す"""
    idx = next((i for i, l in enumerate(lines) if '"qid": "%s"' % qid in l), None)
    if idx is None:
        return None
    # 開き括弧はその1行上
    start = idx - 1
    assert lines[start].strip() == "{", lines[start]
    depth = 0
    for i in range(start, len(lines)):
        depth += lines[i].count("{") - lines[i].count("}")
        if depth == 0:
            end = i
            break
    else:
        return None
    # 末尾のカンマを前後どちらで帳尻合わせするか
    if lines[end].strip() == "},":
        del lines[start:end + 1]
    else:                       # 配列の最後の要素だった場合
        assert lines[end].strip() == "}", lines[end]
        del lines[start:end + 1]
        if lines[start - 1].rstrip().endswith(","):
            lines[start - 1] = lines[start - 1].rstrip()[:-1]
    return True


def main():
    targets = sys.argv[1:]
    if not targets:
        print("qid を指定してください")
        return
    before = json.load(io.open(PATH, encoding="utf-8"))
    lines = io.open(PATH, encoding="utf-8").read().split("\n")
    for q in targets:
        ok = drop(lines, q)
        print("  %s … %s" % (q, "削除" if ok else "見つからない"))
    io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(lines))

    after = json.load(io.open(PATH, encoding="utf-8"))
    nb = sum(len(x.get("quiz") or []) for x in before)
    na = sum(len(x.get("quiz") or []) for x in after)
    print("\n  項目 %d → %d ／ 問題 %d → %d" % (len(before), len(after), nb, na))
    assert len(after) == len(before), "項目数が変わった"
    assert na == nb - len(targets), "問題数の減り方がおかしい"
    qids = [q["qid"] for x in after for q in (x.get("quiz") or [])]
    assert len(qids) == len(set(qids))
    print("  JSON妥当 ／ 項目数そのまま ／ qid重複なし")


if __name__ == "__main__":
    main()
