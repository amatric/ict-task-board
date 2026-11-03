#!/usr/bin/env python3
"""AI 智慧课堂工作台：备课 → 出题 → 批改 → 学情分析。

一条命令跑通一个教学闭环，零第三方依赖。

用法：
    python3 classroom.py lesson  --topic "循环与迭代" --grade 高一 --minutes 45
    python3 classroom.py quiz    --topic "循环与迭代" --count 5 --out quiz.json
    python3 classroom.py grade   --quiz quiz.json --answers ans.json
    python3 classroom.py report  --grades grades.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------- 知识库
# 真实场景可替换为教材/题库接口；这里用内置样例题库保证可离线演示。

TOPIC_BANK: dict[str, dict] = {
    "循环与迭代": {
        "objectives": [
            "能说出 for / while 两种循环的适用区别",
            "能把一个重复性任务改写成循环结构",
            "能识别并修复常见的死循环",
        ],
        "keypoints": ["循环变量", "终止条件", "遍历与索引的差别"],
        "misconceptions": ["把 for 当成必须遍历数字", "忘记更新循环变量导致死循环"],
        "questions": [
            {"q": "for 与 while 最本质的差别是什么？", "type": "简答",
             "answer": "是否已知迭代次数与终止条件的显式程度",
             "rubric": ["次数", "条件"]},
            {"q": "下面代码为什么死循环？`i=0\\nwhile i<5:\\n    print(i)`",
             "type": "诊断", "answer": "循环变量 i 没有自增",
             "rubric": ["自增", "i+="]},
            {"q": "用循环求 1..100 的和，写出核心代码。", "type": "编程",
             "answer": "s=0\\nfor i in range(1,101): s+=i",
             "rubric": ["range", "s+="]},
            {"q": "遍历列表时删除元素可能出什么问题？", "type": "简答",
             "answer": "索引位移导致漏删或越界",
             "rubric": ["索引"]},
            {"q": "range(2,10,3) 会产生哪些数？", "type": "选择",
             "answer": "2,5,8", "rubric": ["2,5,8"]},
        ],
    },
    "函数与参数": {
        "objectives": ["能定义并调用函数", "能区分位置参数与关键字参数", "理解默认值的陷阱"],
        "keypoints": ["形参与实参", "默认参数", "作用域"],
        "misconceptions": ["把可变对象当默认值"],
        "questions": [
            {"q": "默认参数为可变对象时会有什么问题？", "type": "简答",
             "answer": "默认值只求值一次，多次调用共享同一对象",
             "rubric": ["一次"]},
            {"q": "写出一个带默认参数的函数定义。", "type": "编程",
             "answer": "def f(a, b=1): return a+b", "rubric": ["def"]},
        ],
    },
}


# ---------------------------------------------------------------- 备课

def make_lesson(topic: str, grade: str, minutes: int) -> dict:
    bank = TOPIC_BANK.get(topic)
    if not bank:
        raise KeyError(f"题库暂无「{topic}」，可选：{', '.join(TOPIC_BANK)}")
    # 45 分钟课的经典切分
    plan = [
        {"phase": "导入", "minutes": round(minutes * 0.11), "activity": "用一个真实场景引出问题"},
        {"phase": "概念讲解", "minutes": round(minutes * 0.27), "activity": "讲透关键点与常见误解"},
        {"phase": "例题精讲", "minutes": round(minutes * 0.20), "activity": "板书推导一道典型题"},
        {"phase": "课堂练习", "minutes": round(minutes * 0.29), "activity": "分层练习，教师巡堂"},
        {"phase": "小结与作业", "minutes": round(minutes * 0.13), "activity": "回顾目标，布置作业"},
    ]
    drift = minutes - sum(p["minutes"] for p in plan)
    plan[-1]["minutes"] += drift
    return {
        "topic": topic, "grade": grade, "minutes": minutes,
        "objectives": bank["objectives"],
        "keypoints": bank["keypoints"],
        "misconceptions": bank["misconceptions"],
        "plan": plan,
    }


# ---------------------------------------------------------------- 出题

def make_quiz(topic: str, count: int, seed: int = 42) -> dict:
    bank = TOPIC_BANK.get(topic)
    if not bank:
        raise KeyError(f"题库暂无「{topic}」，可选：{', '.join(TOPIC_BANK)}")
    pool = bank["questions"][:]
    random.Random(seed).shuffle(pool)
    picked = pool[: max(1, min(count, len(pool)))]
    return {"topic": topic, "count": len(picked),
            "questions": [{"no": i + 1, **q} for i, q in enumerate(picked)]}


# ---------------------------------------------------------------- 批改

def grade(quiz: dict, answers: dict) -> dict:
    """answers: {"1": "学生作答文本", ...}，按 rubric 关键词命中率给分。"""
    results = []
    total = 0.0
    for q in quiz["questions"]:
        no = str(q["no"])
        ans = (answers.get(no) or "").strip()
        rubric = q.get("rubric", [])
        norm = ans.replace(" ", "").replace("\n", "").lower()
        hit = [r for r in rubric if r and (r.replace(" ", "").lower() in norm)]
        score = 100.0 * len(hit) / len(rubric) if rubric else (100.0 if ans else 0.0)
        results.append({
            "no": q["no"], "type": q["type"], "answer": ans,
            "hit": hit, "missing": [r for r in rubric if r not in hit],
            "score": round(score, 1),
        })
        total += score
    avg = round(total / len(quiz["questions"]), 1) if quiz["questions"] else 0.0
    return {"topic": quiz.get("topic"), "items": results,
            "average": avg, "count": len(results)}


# ---------------------------------------------------------------- 学情分析

def report(grades: list[dict]) -> dict:
    """grades: 多次 grade() 的结果列表。"""
    by_type: dict[str, list[float]] = {}
    weak_points: dict[str, int] = {}
    for g in grades:
        for it in g["items"]:
            by_type.setdefault(it["type"], []).append(it["score"])
            for m in it["missing"]:
                weak_points[m] = weak_points.get(m, 0) + 1
    type_avg = {k: round(sum(v) / len(v), 1) for k, v in by_type.items()}
    overall = round(sum(i["score"] for g in grades for i in g["items"]) /
                    max(1, sum(len(g["items"]) for g in grades)), 1)
    weakest = sorted(type_avg.items(), key=lambda kv: kv[1])[:1]
    advice = []
    if weakest:
        advice.append(f"题型「{weakest[0][0]}」平均分最低（{weakest[0][1]}），建议下节课专项训练")
    for point, cnt in sorted(weak_points.items(), key=lambda kv: -kv[1])[:3]:
        advice.append(f"「{point}」有 {cnt} 人次未覆盖，需回讲")
    if not advice:
        advice.append("整体掌握良好，可进入下一主题")
    return {"overall": overall, "by_type": type_avg,
            "weak_points": sorted(weak_points.items(), key=lambda kv: -kv[1])[:5],
            "advice": advice}


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="AI 智慧课堂工作台")
    sub = ap.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("lesson", help="生成备课方案")
    l.add_argument("--topic", required=True); l.add_argument("--grade", default="高一")
    l.add_argument("--minutes", type=int, default=45)

    q = sub.add_parser("quiz", help="生成随堂测验")
    q.add_argument("--topic", required=True); q.add_argument("--count", type=int, default=5)
    q.add_argument("--out"); q.add_argument("--seed", type=int, default=42)

    g = sub.add_parser("grade", help="批改答卷")
    g.add_argument("--quiz", required=True); g.add_argument("--answers", required=True)

    r = sub.add_parser("report", help="学情分析")
    r.add_argument("--grades", required=True)

    a = ap.parse_args()
    try:
        if a.cmd == "lesson":
            data = make_lesson(a.topic, a.grade, a.minutes)
            print(f"【备课方案】{data['topic']} · {data['grade']} · {data['minutes']} 分钟")
            print("目标：")
            for o in data["objectives"]:
                print(f"  · {o}")
            print("环节：")
            for p in data["plan"]:
                print(f"  {p['phase']:<8} {p['minutes']:>2} 分钟  {p['activity']}")
            print("易错点：")
            for m in data["misconceptions"]:
                print(f"  ! {m}")

        elif a.cmd == "quiz":
            data = make_quiz(a.topic, a.count, a.seed)
            if a.out:
                Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"[OK] 已生成 {a.out}（{data['count']} 题）")
            else:
                print(json.dumps(data, ensure_ascii=False, indent=2))

        elif a.cmd == "grade":
            quiz = json.loads(Path(a.quiz).read_text(encoding="utf-8"))
            ans = json.loads(Path(a.answers).read_text(encoding="utf-8"))
            res = grade(quiz, ans)
            print(f"【批改结果】{res['topic']}  平均分 {res['average']}")
            for it in res["items"]:
                flag = "✓" if it["score"] >= 60 else "✗"
                print(f"  {flag} 第{it['no']}题（{it['type']}） {it['score']} 分"
                      f"{'  缺：' + '/'.join(it['missing']) if it['missing'] else ''}")

        elif a.cmd == "report":
            gs = json.loads(Path(a.grades).read_text(encoding="utf-8"))
            rep = report(gs)
            print(f"【学情分析】整体平均 {rep['overall']}")
            print("题型均分：")
            for k, v in rep["by_type"].items():
                print(f"  {k}: {v}")
            print("教学建议：")
            for ad in rep["advice"]:
                print(f"  → {ad}")
    except KeyError as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
