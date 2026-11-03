#!/usr/bin/env python3
"""华为云能力索引检索（零依赖）。

用法：
    python3 search_skills.py "图片 文字识别"     # 多关键词，任一命中
    python3 search_skills.py --category AI
    python3 search_skills.py --all
    python3 search_skills.py --id obs-lifecycle
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "skills_index.json"


def load() -> list[dict]:
    return json.loads(INDEX.read_text(encoding="utf-8"))["items"]


def score(item: dict, terms: list[str]) -> int:
    hay = " ".join([
        item.get("name", ""), item.get("summary", ""), item.get("category", ""),
        " ".join(item.get("keywords", [])), item.get("id", ""),
    ]).lower()
    return sum(1 for t in terms if t and t.lower() in hay)


def show(item: dict) -> None:
    print(f"\n■ {item['name']}  [{item['id']}]  · {item['category']}")
    print(f"   {item['summary']}")
    print(f"   适用边界：{item.get('boundary', '-')}")
    print(f"   接入：{item.get('entry', '-')}")
    ex = item.get("example", "")
    if ex:
        print("   示例：")
        for line in ex.splitlines():
            print("     " + line)


def main() -> int:
    ap = argparse.ArgumentParser(description="华为云技能索引检索")
    ap.add_argument("terms", nargs="*", help="关键词，空格分隔")
    ap.add_argument("--category", help="按大类过滤")
    ap.add_argument("--id", help="查看指定条目")
    ap.add_argument("--all", action="store_true", help="列出全部")
    ap.add_argument("--limit", type=int, default=3, help="最多返回几条（默认 3）")
    args = ap.parse_args()

    # 允许 "图片 文字识别" 这种一口气传入多个词
    args.terms = [t for chunk in (args.terms or []) for t in chunk.split() if t]
    items = load()

    if args.id:
        hit = [i for i in items if i["id"] == args.id]
        if not hit:
            print(f"未找到 id={args.id}")
            return 1
        show(hit[0])
        return 0

    if args.all or args.category:
        pool = [i for i in items if not args.category or i["category"] == args.category]
        print(f"共 {len(pool)} 条：")
        for i in pool:
            print(f"  - {i['name']:28} [{i['id']}]  {i['category']}")
        return 0

    if not args.terms:
        ap.print_help()
        return 2

    ranked = sorted(((score(i, args.terms), i) for i in items), key=lambda x: -x[0])
    hits = [(s, i) for s, i in ranked if s > 0][: args.limit]

    if not hits:
        print(f"没有命中「{' '.join(args.terms)}」的条目。试试 --all 浏览，或换更宽的关键词。")
        return 1

    print(f"命中 {len(hits)} 条（按相关度降序）：")
    for s, i in hits:
        show(i)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
