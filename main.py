#!/usr/bin/env python3
"""演示：让 AgentTeam 协作产出一篇毕业论文的方案。"""

from __future__ import annotations

import json
import sys

from agentteam.orchestrator import Orchestrator


def main() -> int:
    task = sys.argv[1] if len(sys.argv) > 1 else "帮我写一篇关于多智能体协作的毕业论文"
    print(f"任务：{task}\n" + "=" * 60)

    result = Orchestrator(max_rounds=2).run(task)

    print("=" * 60)
    print(f"轮次：{result['rounds']}    审校结论：{result['verdict']}")
    print(f"目标字数：{result['total_words']}")
    print("\n大纲：")
    for i, ch in enumerate(result["outline"], 1):
        print(f"  {i}. {ch}")

    if result["issues"]:
        print("\n待修改：")
        for it in result["issues"]:
            print(f"  - [{it['chapter']}] {it['issue']}")

    if "--json" in sys.argv:
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
