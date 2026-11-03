#!/usr/bin/env python3
"""演示：多 Agent 面试协同。"""

from __future__ import annotations

import json
import sys

from team.orchestrator import InterviewOrchestrator


def main() -> int:
    print("多 Agent 面试协同 · 岗位：后端工程师\n" + "=" * 60)
    result = InterviewOrchestrator(rounds=5).run()
    if "--json" in sys.argv:
        print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
