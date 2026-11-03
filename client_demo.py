#!/usr/bin/env python3
"""MCP stdio 客户端演示：拉起 server.py，走完整 MCP 握手并调用工具。"""

import json
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).resolve().parent / "server.py"


def main() -> int:
    proc = subprocess.Popen(
        [sys.executable, str(SERVER)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
    )

    def rpc(payload: dict) -> dict:
        proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())

    # 1) 握手
    init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    print("== initialize ==")
    print(json.dumps(init["result"], ensure_ascii=False, indent=2))
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.flush()

    # 2) 列工具
    tools = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    print("\n== tools/list ==")
    for t in tools["result"]["tools"]:
        print(f"  - {t['name']}: {t['description']}")

    # 3) 调工具
    call = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "plan_trip",
        "arguments": {"city": "成都", "days": 3, "people": 2, "tier": "舒适",
                      "preferences": ["自然", "美食"]},
    }})
    print("\n== tools/call: plan_trip ==")
    print(call["result"]["content"][0]["text"])

    proc.stdin.close()
    proc.wait(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
