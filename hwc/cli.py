"""hwc CLI 主入口：子命令 + 结构化输出 + 统一错误处理。

命令树：
    hwc ecs list [--limit N]
    hwc ecs show <id>
    hwc evs list [--limit N]
    hwc obs ls <obs://bucket/prefix>
    hwc region                 # 显示当前区域与凭证状态
    hwc --json                 # 全部命令支持 JSON 输出（默认表格）
"""

from __future__ import annotations

import argparse
import json
import os
import sys

VERSION = "1.0.0"
DEFAULT_REGION = os.environ.get("HWC_REGION", os.environ.get("HUAWEICLOUD_SDK_REGION", "cn-north-4"))


# ---------------------------------------------------------------- 输出

def emit(data, as_json: bool, columns: list[tuple[str, str]] | None = None) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    rows = data if isinstance(data, list) else [data]
    if not rows:
        print("(空)")
        return
    if columns:
        heads = [c[0] for c in columns]
        print("  ".join(h.ljust(14) for h in heads))
        print("  ".join("-" * 14 for _ in heads))
        for r in rows:
            print("  ".join(str(r.get(k, "") or "-")[:14].ljust(14) for _, k in columns))
    else:
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))


def fail(msg: str, hint: str = "", code: int = 1) -> int:
    payload = {"ok": False, "error": msg}
    if hint:
        payload["hint"] = hint
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    return code


# ---------------------------------------------------------------- 数据层
# 为便于离线演示与自测，未配置凭证时返回内置样例数据；配置后切换到真实调用。

def _creds_ready() -> bool:
    return bool(os.environ.get("HUAWEICLOUD_SDK_AK") and os.environ.get("HUAWEICLOUD_SDK_SK"))


DEMO_ECS = [
    {"name": "web-01", "id": "8f3c...a1", "status": "ACTIVE", "flavor": "s6.large.2", "ip": "192.168.0.10"},
    {"name": "db-01", "id": "1d7e...b2", "status": "ACTIVE", "flavor": "c6.xlarge.4", "ip": "192.168.0.20"},
]
DEMO_EVS = [
    {"name": "web-01-volume-0000", "size": 40, "type": "GPSSD", "status": "in-use"},
    {"name": "data-disk", "size": 100, "type": "SSD", "status": "available"},
]


def ecs_list(limit: int) -> list[dict]:
    if _creds_ready():
        return _real_call("ecs")
    return DEMO_ECS[:limit]


def ecs_show(server_id: str) -> dict:
    for s in (ecs_list(100)):
        if s["id"].startswith(server_id) or server_id in s["id"]:
            return s
    raise LookupError(f"未找到实例 {server_id}")


def evs_list(limit: int) -> list[dict]:
    if _creds_ready():
        return _real_call("evs")
    return DEMO_EVS[:limit]


def _real_call(kind: str) -> list[dict]:
    """真实调用占位：接入官方 SDK 后替换。

    生产实现建议：
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdkecs.v2 import EcsClient, ListServersDetailsRequest
    """
    raise RuntimeError(
        "已配置 AK/SK，但本示例未内置官方 SDK。"
        "生产环境请 pip install huaweicloudsdkecs 后在此处接入；"
        "如需立即体验，请 unset HUAWEICLOUD_SDK_AK 使用内置样例数据。"
    )


# ---------------------------------------------------------------- 子命令

def cmd_region(args) -> int:
    data = {
        "region": args.region,
        "ak_configured": bool(os.environ.get("HUAWEICLOUD_SDK_AK")),
        "sk_configured": bool(os.environ.get("HUAWEICLOUD_SDK_SK")),
        "data_source": "cloud" if _creds_ready() else "builtin-demo",
        "endpoints": {
            "ecs": f"https://ecs.{args.region}.myhuaweicloud.com",
            "evs": f"https://evs.{args.region}.myhuaweicloud.com",
            "obs": f"https://obs.{args.region}.myhuaweicloud.com",
        },
    }
    emit(data, args.json)
    return 0


def cmd_ecs_list(args) -> int:
    try:
        rows = ecs_list(args.limit)
    except RuntimeError as e:
        return fail(str(e), "unset HUAWEICLOUD_SDK_AK / HUAWEICLOUD_SDK_SK 可回退到内置样例")
    emit(rows, args.json, [("NAME", "name"), ("ID", "id"), ("STATUS", "status"),
                           ("FLAVOR", "flavor"), ("IP", "ip")])
    return 0


def cmd_ecs_show(args) -> int:
    try:
        emit(ecs_show(args.id), True)
    except LookupError as e:
        return fail(str(e))
    return 0


def cmd_evs_list(args) -> int:
    try:
        rows = evs_list(args.limit)
    except RuntimeError as e:
        return fail(str(e), "unset HUAWEICLOUD_SDK_AK / HUAWEICLOUD_SDK_SK 可回退到内置样例")
    emit(rows, args.json, [("NAME", "name"), ("SIZE", "size"), ("TYPE", "type"), ("STATUS", "status")])
    return 0


def cmd_obs_ls(args) -> int:
    if not args.path.startswith("obs://"):
        return fail("路径需形如 obs://bucket/prefix", "示例：hwc obs ls obs://my-bucket/reports/")
    return fail("OBS 需 OBS AK/SK 与独立签名", "见 skill-obs-uploader 或使用 obsutil")


# ---------------------------------------------------------------- 参数

def build_parser() -> argparse.ArgumentParser:
    # 公共选项：既支持 hwc --json ecs list，也支持 hwc ecs list --json
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="以 JSON 输出（便于程序处理）")
    common.add_argument("--region", default=argparse.SUPPRESS,
                        help="区域，默认 cn-north-4")

    p = argparse.ArgumentParser(prog="hwc", description="华为云服务命令行工具")
    p.add_argument("--version", action="version", version=f"hwc {VERSION}")
    p.add_argument("--json", action="store_true", help="以 JSON 输出（便于程序处理）")
    p.add_argument("--region", default=DEFAULT_REGION, help="区域，默认 cn-north-4")
    sub = p.add_subparsers(dest="group", required=True)

    ecs = sub.add_parser("ecs", parents=[common], help="弹性云服务器")
    ecs_sub = ecs.add_subparsers(dest="action", required=True)
    l = ecs_sub.add_parser("list", parents=[common], help="列出实例")
    l.add_argument("--limit", type=int, default=20)
    l.set_defaults(func=cmd_ecs_list)
    s = ecs_sub.add_parser("show", parents=[common], help="查看实例详情")
    s.add_argument("id")
    s.set_defaults(func=cmd_ecs_show)

    evs = sub.add_parser("evs", parents=[common], help="云硬盘")
    evs_sub = evs.add_subparsers(dest="action", required=True)
    el = evs_sub.add_parser("list", parents=[common], help="列出云硬盘")
    el.add_argument("--limit", type=int, default=20)
    el.set_defaults(func=cmd_evs_list)

    obs = sub.add_parser("obs", parents=[common], help="对象存储")
    obs_sub = obs.add_subparsers(dest="action", required=True)
    ol = obs_sub.add_parser("ls", parents=[common], help="列出对象")
    ol.add_argument("path")
    ol.set_defaults(func=cmd_obs_ls)

    r = sub.add_parser("region", parents=[common], help="显示区域与凭证状态")
    r.set_defaults(func=cmd_region)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not hasattr(args, "json"):
        args.json = False
    if not hasattr(args, "region"):
        args.region = DEFAULT_REGION
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        return fail(f"未预期错误: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
