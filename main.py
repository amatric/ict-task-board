#!/usr/bin/env python3
"""演示：校园活动策划多 Agent 协作。"""

from __future__ import annotations

import json
import sys

from team.orchestrator import CampusTeam


def main() -> int:
    brief = {
        "theme": sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "AI 创意市集",
        "audience": "全校学生",
        "scale": 120,
        "budget_cap": 6000,
    }
    print(f"活动简报：{json.dumps(brief, ensure_ascii=False)}\n" + "=" * 60)
    out = CampusTeam().plan(brief)
    print("=" * 60)

    for r in out["results"]:
        print(f"\n■ {r['role']}")
        print(f"  {r['summary']}")
        if r["role"] == "预算":
            for k, v in r["data"]["breakdown"].items():
                print(f"    {k}: ¥{v}")
        if r["role"] == "物料":
            for it in r["data"]["items"]:
                print(f"    - {it['item']} ×{it['qty']}")
        if r["role"] == "宣传":
            for t in r["data"]["timeline"]:
                print(f"    - {t['when']} {t['phase']}：{t['action']}")

    if "--json" in sys.argv:
        print("\n" + json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
