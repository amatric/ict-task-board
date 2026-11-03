#!/usr/bin/env python3
"""智能行程规划 MCP Server（stdio JSON-RPC 2.0，零第三方依赖）。

实现 MCP 协议的三个方法：
  - initialize    握手，返回 serverInfo 与 capabilities
  - tools/list    暴露可用工具
  - tools/call    执行工具

工具：
  1. search_attractions  按城市/偏好检索景点（内置样例库）
  2. plan_itinerary      按天数与偏好生成逐日行程
  3. estimate_budget     按人数/天数/档位估算预算并给出分类明细
  4. plan_trip           编排：检索 → 排程 → 预算，一次给出完整方案（组合工具）

启动：
    python3 server.py            # 从 stdin 读 JSON-RPC，逐行
也可被 MCP 客户端以 command/args 方式拉起，见 README。
"""

from __future__ import annotations

import json
import sys
from typing import Any

SERVER_INFO = {"name": "trip-planner-mcp", "version": "1.0.0"}
PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------- 数据

ATTRACTIONS: dict[str, list[dict[str, Any]]] = {
    "北京": [
        {"name": "故宫博物院", "tags": ["历史", "人文"], "hours": 4, "price": 60, "area": "东城"},
        {"name": "八达岭长城", "tags": ["自然", "历史"], "hours": 5, "price": 40, "area": "延庆"},
        {"name": "颐和园", "tags": ["自然", "人文"], "hours": 3, "price": 30, "area": "海淀"},
        {"name": "南锣鼓巷", "tags": ["美食", "街区"], "hours": 2, "price": 0, "area": "东城"},
        {"name": "798 艺术区", "tags": ["艺术", "街区"], "hours": 3, "price": 0, "area": "朝阳"},
    ],
    "上海": [
        {"name": "外滩", "tags": ["街区", "夜景"], "hours": 2, "price": 0, "area": "黄浦"},
        {"name": "上海博物馆", "tags": ["人文", "历史"], "hours": 3, "price": 0, "area": "黄浦"},
        {"name": "迪士尼乐园", "tags": ["亲子", "娱乐"], "hours": 8, "price": 475, "area": "浦东"},
        {"name": "田子坊", "tags": ["美食", "街区"], "hours": 2, "price": 0, "area": "黄浦"},
        {"name": "豫园", "tags": ["人文", "美食"], "hours": 2, "price": 40, "area": "黄浦"},
    ],
    "成都": [
        {"name": "大熊猫繁育研究基地", "tags": ["自然", "亲子"], "hours": 4, "price": 55, "area": "成华"},
        {"name": "宽窄巷子", "tags": ["美食", "街区"], "hours": 2, "price": 0, "area": "青羊"},
        {"name": "武侯祠", "tags": ["历史", "人文"], "hours": 2, "price": 50, "area": "武侯"},
        {"name": "都江堰", "tags": ["自然", "历史"], "hours": 5, "price": 80, "area": "都江堰"},
        {"name": "锦里", "tags": ["美食", "夜景"], "hours": 2, "price": 0, "area": "武侯"},
    ],
}

BUDGET_TIERS = {
    "经济": {"hotel": 200, "meal": 80, "transport": 40, "ticket": 1.0},
    "舒适": {"hotel": 500, "meal": 150, "transport": 80, "ticket": 1.0},
    "豪华": {"hotel": 1200, "meal": 300, "transport": 200, "ticket": 1.0},
}

# ---------------------------------------------------------------- 工具实现


def search_attractions(city: str, preference: str = "", limit: int = 8) -> dict[str, Any]:
    pool = ATTRACTIONS.get(city)
    if not pool:
        return {"ok": False, "error": f"暂未收录城市「{city}」，可选：{', '.join(ATTRACTIONS)}"}
    items = pool
    if preference:
        items = [a for a in pool if any(preference in t for t in a["tags"])] or pool
    items = sorted(items, key=lambda a: (-a["hours"], a["name"]))[:limit]
    return {"ok": True, "city": city, "count": len(items), "attractions": items}


def plan_itinerary(city: str, days: int, preferences: list[str] | None = None) -> dict[str, Any]:
    preferences = preferences or []
    found = search_attractions(city, "", limit=50)
    if not found["ok"]:
        return found
    pool = found["attractions"]

    # 偏好打分：命中 tag 越多排越前
    def score(a: dict[str, Any]) -> int:
        return sum(1 for p in preferences if any(p in t for t in a["tags"]))

    pool = sorted(pool, key=lambda a: (-score(a), -a["hours"]))

    per_day_hours = 7
    plan: list[dict[str, Any]] = []
    idx = 0
    for d in range(1, days + 1):
        today: list[dict[str, Any]] = []
        used = 0
        while idx < len(pool) and used + pool[idx]["hours"] <= per_day_hours:
            a = pool[idx]
            today.append({"name": a["name"], "hours": a["hours"], "price": a["price"], "area": a["area"]})
            used += a["hours"]
            idx += 1
        if not today and idx < len(pool):  # 单个景点就超时长，也要放一个
            a = pool[idx]
            today.append({"name": a["name"], "hours": a["hours"], "price": a["price"], "area": a["area"]})
            used = a["hours"]
            idx += 1
        plan.append({"day": d, "total_hours": used, "items": today})

    total_ticket = sum(it["price"] for day in plan for it in day["items"])
    return {"ok": True, "city": city, "days": days, "preferences": preferences,
            "plan": plan, "total_ticket": total_ticket}


def estimate_budget(days: int, people: int = 1, tier: str = "舒适", ticket: int = 0) -> dict[str, Any]:
    conf = BUDGET_TIERS.get(tier)
    if not conf:
        return {"ok": False, "error": f"未知档位「{tier}」，可选：{', '.join(BUDGET_TIERS)}"}
    hotel = conf["hotel"] * max(0, days - 1) * (1 if people <= 2 else 2)  # 3 人以上开两间
    meal = conf["meal"] * days * people
    transport = conf["transport"] * days * people
    total = hotel + meal + transport + ticket * people
    return {
        "ok": True,
        "tier": tier, "days": days, "people": people,
        "breakdown": {"住宿": hotel, "餐饮": meal, "市内交通": transport, "门票": ticket * people},
        "total": total,
        "per_person": round(total / people, 2) if people else total,
        "currency": "CNY",
    }


def plan_trip(city: str, days: int, people: int = 1, tier: str = "舒适",
              preferences: list[str] | None = None) -> dict[str, Any]:
    it = plan_itinerary(city, days, preferences)
    if not it["ok"]:
        return it
    budget = estimate_budget(days, people, tier, it["total_ticket"])
    return {
        "ok": True,
        "city": city, "days": days, "people": people, "tier": tier,
        "itinerary": it["plan"],
        "budget": budget,
        "summary": (f"{city} {days} 天 {people} 人（{tier}档）"
                    f"共 {sum(d['total_hours'] for d in it['plan'])} 小时游览，"
                    f"预算约 ¥{budget['total']}，人均 ¥{budget['per_person']}"),
    }


# ---------------------------------------------------------------- MCP 协议

TOOLS = [
    {
        "name": "search_attractions",
        "description": "按城市与偏好检索景点，返回名称、标签、建议时长、门票、所在区域",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名，如 北京/上海/成都"},
                "preference": {"type": "string", "description": "偏好关键词，如 历史/自然/美食"},
                "limit": {"type": "integer", "description": "返回数量上限", "default": 8},
            },
            "required": ["city"],
        },
    },
    {
        "name": "plan_itinerary",
        "description": "按天数与偏好生成逐日行程（每天不超过约 7 小时游览）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "days": {"type": "integer", "minimum": 1},
                "preferences": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["city", "days"],
        },
    },
    {
        "name": "estimate_budget",
        "description": "按人数、天数、档位（经济/舒适/豪华）估算预算并给出分类明细",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "minimum": 1},
                "people": {"type": "integer", "minimum": 1, "default": 1},
                "tier": {"type": "string", "enum": ["经济", "舒适", "豪华"], "default": "舒适"},
                "ticket": {"type": "integer", "description": "人均门票合计", "default": 0},
            },
            "required": ["days"],
        },
    },
    {
        "name": "plan_trip",
        "description": "组合工具：一次生成完整方案（行程 + 预算 + 一句话结论）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "days": {"type": "integer", "minimum": 1},
                "people": {"type": "integer", "minimum": 1, "default": 1},
                "tier": {"type": "string", "enum": ["经济", "舒适", "豪华"], "default": "舒适"},
                "preferences": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["city", "days"],
        },
    },
]

HANDLERS = {
    "search_attractions": search_attractions,
    "plan_itinerary": plan_itinerary,
    "estimate_budget": estimate_budget,
    "plan_trip": plan_trip,
}


def handle(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {}},
        }}
    if method in ("notifications/initialized", "initialized"):
        return None  # 通知无需响应
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        fn = HANDLERS.get(name)
        if not fn:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32601, "message": f"未知工具: {name}"}}
        try:
            data = fn(**args)
        except TypeError as e:
            return {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32602, "message": f"参数错误: {e}"}}
        is_error = not data.get("ok", True)
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}],
            "isError": is_error,
        }}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}

    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"不支持的方法: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"jsonrpc": "2.0", "id": None,
                              "error": {"code": -32700, "message": "JSON 解析失败"}}), flush=True)
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
