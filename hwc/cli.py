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
REGION = DEFAULT_REGION  # 供数据层直接引用


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


# ---------------------------------------------------------------- 数据层（真实华为云 API 调用）
# 认证：X-Auth-Token（由 IAM 获取，或直接注入 HUAWEICLOUD_SDK_SECURITY_TOKEN）
# 端点：https://{service}.{region}.myhuaweicloud.com

import base64
import hashlib
import hmac
import mimetypes
import time
import urllib.error
import urllib.parse
import urllib.request


def _token() -> str:
    tok = os.environ.get("HUAWEICLOUD_SDK_SECURITY_TOKEN") or os.environ.get("HWC_TOKEN", "")
    if not tok:
        raise RuntimeError(
            "缺少 X-Auth-Token：请设置 HUAWEICLOUD_SDK_SECURITY_TOKEN"
            "（由 IAM 换取），或 unset 后使用内置样例数据演示"
        )
    return tok


def _project() -> str:
    pid = os.environ.get("HUAWEICLOUD_SDK_PROJECT_ID") or os.environ.get("HWC_PROJECT_ID", "")
    if not pid:
        raise RuntimeError(
            "缺少 project id：请设置 HUAWEICLOUD_SDK_PROJECT_ID"
            "（控制台「我的凭证」里可查）"
        )
    return pid


def _http(method: str, url: str, token: str, body: bytes | None = None,
          headers: dict | None = None) -> tuple[int, bytes]:
    h = {"Content-Type": "application/json", "X-Auth-Token": token}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read()


def ecs_list(limit: int) -> list[dict]:
    """真实调用 ECS ListServersDetails。"""
    tok, pid = _token(), _project()
    url = f"https://ecs.{REGION}.myhuaweicloud.com/v2.1/{pid}/servers/detail"
    _, raw = _http("GET", url, tok)
    servers = json.loads(raw).get("servers", [])[:limit]
    out = []
    for s in servers:
        ips = []
        for addr_list in (s.get("addresses") or {}).values():
            for a in addr_list:
                if a.get("addr"):
                    ips.append(a["addr"])
        out.append({
            "name": s.get("name"),
            "id": s.get("id"),
            "status": s.get("status"),
            "flavor": (s.get("flavor") or {}).get("id"),
            "ip": ",".join(ips),
        })
    return out


def ecs_show(server_id: str) -> dict:
    tok, pid = _token(), _project()
    url = f"https://ecs.{REGION}.myhuaweicloud.com/v2.1/{pid}/servers/{server_id}"
    _, raw = _http("GET", url, tok)
    s = json.loads(raw).get("server", {})
    return {
        "name": s.get("name"), "id": s.get("id"), "status": s.get("status"),
        "created": s.get("created"), "flavor": (s.get("flavor") or {}),
        "addresses": s.get("addresses"), "metadata": s.get("metadata"),
    }


def evs_list(limit: int) -> list[dict]:
    """真实调用 EVS ListVolumesDetails。"""
    tok, pid = _token(), _project()
    url = f"https://evs.{REGION}.myhuaweicloud.com/v2/{pid}/cloudvolumes/detail"
    _, raw = _http("GET", url, tok)
    vols = json.loads(raw).get("volumes", [])[:limit]
    return [{
        "name": v.get("name"), "size": v.get("size"), "type": v.get("volume_type"),
        "status": v.get("status"), "id": v.get("id"),
        "attached": ",".join(a.get("server_id", "") for a in (v.get("attachments") or [])),
    } for v in vols]


# ---- OBS：V2 签名，与 ECS/EVS 的 token 方式不同 ----

def _obs_creds() -> tuple[str, str, str, str]:
    ak = os.environ.get("OBS_AK") or os.environ.get("HUAWEICLOUD_SDK_AK", "")
    sk = os.environ.get("OBS_SK") or os.environ.get("HUAWEICLOUD_SDK_SK", "")
    tok = os.environ.get("OBS_SECURITY_TOKEN", "")
    ep = os.environ.get("OBS_ENDPOINT", f"https://obs.{REGION}.myhuaweicloud.com")
    if not ak or not sk:
        raise RuntimeError("OBS 需要 AK/SK：设置 OBS_AK / OBS_SK（可选 OBS_SECURITY_TOKEN）")
    return ak, sk, tok, ep


def _obs_sign(method: str, bucket: str, key: str, content_md5: str, content_type: str,
              date: str, sk: str, token: str = "") -> str:
    resource = f"/{bucket}/{key}" if key else f"/{bucket}/"
    sts = "\n".join([method, content_md5, content_type, date,
                      ("x-obs-security-token:" + token + "\n" if token else "") + resource])
    return base64.b64encode(hmac.new(sk.encode(), sts.encode(), hashlib.sha1).digest()).decode()


def obs_ls(path: str, limit: int = 100) -> list[dict]:
    """真实调用 OBS ListObjects（V2 签名 GET /?prefix=）。"""
    if not path.startswith("obs://"):
        raise ValueError("路径需形如 obs://bucket/prefix")
    rest = path[len("obs://"):]
    bucket, _, prefix = rest.partition("/")
    ak, sk, tok, ep = _obs_creds()
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    sig = _obs_sign("GET", bucket, "", "", "", date, sk, tok)
    headers = {"Authorization": f"OBS {ak}:{sig}", "Date": date}
    if tok:
        headers["x-obs-security-token"] = tok
    url = f"{ep}/{bucket}?prefix={urllib.parse.quote(prefix)}&max-keys={limit}"
    req = urllib.request.Request(url, method="GET", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read().decode("utf-8", "ignore")
    import re
    keys = re.findall(r"<Key>(.*?)</Key>", body)
    sizes = re.findall(r"<Size>(.*?)</Size>", body)
    return [{"key": k, "size": int(sz)} for k, sz in zip(keys, sizes)]


# ---------------------------------------------------------------- 子命令

def cmd_region(args) -> int:
    data = {
        "region": args.region,
        "ak_configured": bool(os.environ.get("HUAWEICLOUD_SDK_AK")),
        "sk_configured": bool(os.environ.get("HUAWEICLOUD_SDK_SK")),
        "token_configured": bool(os.environ.get("HUAWEICLOUD_SDK_SECURITY_TOKEN") or os.environ.get("HWC_TOKEN")),
        "project_configured": bool(os.environ.get("HUAWEICLOUD_SDK_PROJECT_ID") or os.environ.get("HWC_PROJECT_ID")),
        "obs_ak_configured": bool(os.environ.get("OBS_AK") or os.environ.get("HUAWEICLOUD_SDK_AK")),
        "endpoints": {
            "ecs": f"https://ecs.{args.region}.myhuaweicloud.com",
            "evs": f"https://evs.{args.region}.myhuaweicloud.com",
            "obs": f"https://obs.{args.region}.myhuaweicloud.com",
        },
    }
    emit(data, args.json)
    return 0


DEMO_ECS = [
    {"name": "web-01", "id": "8f3c...a1", "status": "ACTIVE", "flavor": "s6.large.2", "ip": "192.168.0.10"},
    {"name": "db-01", "id": "1d7e...b2", "status": "ACTIVE", "flavor": "c6.xlarge.4", "ip": "192.168.0.20"},
]
DEMO_EVS = [
    {"name": "web-01-volume-0000", "size": 40, "type": "GPSSD", "status": "in-use", "id": "v-1", "attached": "8f3c...a1"},
    {"name": "data-disk", "size": 100, "type": "SSD", "status": "available", "id": "v-2", "attached": ""},
]
DEMO_OBS = [{"key": "reports/latest.md", "size": 3122}, {"key": "builds/dist.zip", "size": 1048576}]


def cmd_ecs_list(args) -> int:
    if args.demo:
        emit(DEMO_ECS[:args.limit], args.json, [("NAME", "name"), ("ID", "id"), ("STATUS", "status"), ("FLAVOR", "flavor"), ("IP", "ip")])
        return 0
    try:
        rows = ecs_list(args.limit)
    except RuntimeError as e:
        return fail(str(e), "未配凭证时可用 --demo 查看样例数据")
    emit(rows, args.json, [("NAME", "name"), ("ID", "id"), ("STATUS", "status"),
                           ("FLAVOR", "flavor"), ("IP", "ip")])
    return 0


def cmd_ecs_show(args) -> int:
    try:
        emit(ecs_show(args.id), True)
    except RuntimeError as e:
        return fail(str(e), "未配凭证时可用 --demo 查看样例数据")
    return 0


def cmd_evs_list(args) -> int:
    if args.demo:
        emit(DEMO_EVS[:args.limit], args.json, [("NAME", "name"), ("SIZE", "size"), ("TYPE", "type"), ("STATUS", "status")])
        return 0
    try:
        rows = evs_list(args.limit)
    except RuntimeError as e:
        return fail(str(e), "未配凭证时可用 --demo 查看样例数据")
    emit(rows, args.json, [("NAME", "name"), ("SIZE", "size"), ("TYPE", "type"), ("STATUS", "status")])
    return 0


def cmd_obs_ls(args) -> int:
    if args.demo:
        emit(DEMO_OBS[:args.limit], args.json, [("KEY", "key"), ("SIZE", "size")])
        return 0
    try:
        rows = obs_ls(args.path, args.limit)
    except RuntimeError as e:
        return fail(str(e), "OBS 走 V2 签名，需 OBS_AK/OBS_SK")
    except ValueError as e:
        return fail(str(e), "示例：hwc obs ls obs://my-bucket/reports/")
    emit(rows, args.json, [("KEY", "key"), ("SIZE", "size")])
    return 0


# ---------------------------------------------------------------- 参数

def build_parser() -> argparse.ArgumentParser:
    # 公共选项：既支持 hwc --json ecs list，也支持 hwc ecs list --json
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="以 JSON 输出（便于程序处理）")
    common.add_argument("--region", default=argparse.SUPPRESS,
                        help="区域，默认 cn-north-4")
    common.add_argument("--demo", action="store_true", default=argparse.SUPPRESS,
                        help="用内置样例数据（不发真实请求）")

    p = argparse.ArgumentParser(prog="hwc", description="华为云服务命令行工具")
    p.add_argument("--version", action="version", version=f"hwc {VERSION}")
    p.add_argument("--json", action="store_true", help="以 JSON 输出（便于程序处理）")
    p.add_argument("--region", default=DEFAULT_REGION, help="区域，默认 cn-north-4")
    p.add_argument("--demo", action="store_true", help="用内置样例数据（不发真实请求）")
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
    ol.add_argument("--limit", type=int, default=100)
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
    if not hasattr(args, "demo"):
        args.demo = False
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as e:  # noqa: BLE001
        return fail(f"未预期错误: {e}")


if __name__ == "__main__":
    raise SystemExit(main())
