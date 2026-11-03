#!/usr/bin/env python3
"""高德开放平台 Web 服务 API 客户端（真实调用，零依赖）。

覆盖本作品需要的三个接口：
    /v3/geocode/geo          地址 → 经纬度
    /v3/direction/driving    驾车路线规划（含 polyline）
    /v3/direction/walking    步行路线规划

Key 从 config.json 或环境变量 AMAP_WEB_KEY 读取。
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://restapi.amap.com"
CONFIG = Path(__file__).resolve().parent.parent / "config.json"


def _key() -> str:
    key = os.environ.get("AMAP_WEB_KEY", "")
    if not key and CONFIG.is_file():
        try:
            data = json.loads(CONFIG.read_text(encoding="utf-8"))
            key = (data.get("amap") or {}).get("web_key", "")
        except Exception:  # noqa: BLE001
            key = ""
    if not key or key.startswith("请填入"):
        raise RuntimeError(
            "未配置高德 Web 服务 Key。请复制 config.example.json 为 config.json "
            "并填写 amap.web_key，或设置环境变量 AMAP_WEB_KEY"
        )
    return key


def _get(path: str, params: dict) -> dict:
    params = {**params, "key": _key(), "output": "JSON"}
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    if str(data.get("status")) != "1":
        raise RuntimeError(f"高德接口返回错误: {data.get('info')} ({data.get('infocode')})")
    return data


def geocode(address: str, city: str = "") -> dict:
    """地址 → 经纬度。"""
    data = _get("/v3/geocode/geo", {"address": address, "city": city})
    geos = data.get("geocodes") or []
    if not geos:
        raise LookupError(f"地址解析失败: {address}")
    g = geos[0]
    lng, lat = g["location"].split(",")
    return {"address": g.get("formatted_address"), "city": g.get("city"),
            "lng": float(lng), "lat": float(lat)}


def driving_route(origin: str, destination: str, waypoints: str = "") -> dict:
    """驾车路线规划，返回距离、耗时、路径折线点串。"""
    params = {"origin": origin, "destination": destination, "extensions": "all"}
    if waypoints:
        params["waypoints"] = waypoints
    data = _get("/v3/direction/driving", params)
    paths = (data.get("route") or {}).get("paths") or []
    if not paths:
        raise LookupError("未找到驾车路线")
    p = paths[0]
    points = []
    for step in p.get("steps", []):
        points.extend(step.get("polyline", "").split(";"))
    return {
        "distance_m": int(p.get("distance", 0)),
        "duration_s": int(p.get("duration", 0)),
        "toll": p.get("tolls"),
        "traffic_lights": p.get("traffic_lights"),
        "polyline_points": [x for x in points if x],
        "steps": [{"instruction": s.get("instruction"), "road": s.get("road"),
                   "distance": int(s.get("distance", 0))} for s in p.get("steps", [])],
    }


def walking_route(origin: str, destination: str) -> dict:
    data = _get("/v3/direction/walking", {"origin": origin, "destination": destination})
    paths = (data.get("route") or {}).get("paths") or []
    if not paths:
        raise LookupError("未找到步行路线")
    p = paths[0]
    points = []
    for step in p.get("steps", []):
        points.extend(step.get("polyline", "").split(";"))
    return {"distance_m": int(p.get("distance", 0)),
            "duration_s": int(p.get("duration", 0)),
            "polyline_points": [x for x in points if x]}


if __name__ == "__main__":
    import sys
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "geo"
        if mode == "geo":
            print(json.dumps(geocode(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""),
                             ensure_ascii=False, indent=2))
        elif mode == "driving":
            print(json.dumps(driving_route(sys.argv[2], sys.argv[3]),
                             ensure_ascii=False, indent=2)[:800])
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
