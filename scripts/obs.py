#!/usr/bin/env python3
"""华为云 OBS 操作脚本（零依赖，OBS V2 签名）。

子命令：put / get / ls / sign
凭证：OBS_AK / OBS_SK / OBS_SECURITY_TOKEN（可选）/ OBS_ENDPOINT
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CHUNK = 8 * 1024 * 1024
MAX_RETRY = 3


def out(**kw) -> None:
    print(json.dumps(kw, ensure_ascii=False))


def creds() -> tuple[str, str, str, str]:
    ak = os.environ.get("OBS_AK", "")
    sk = os.environ.get("OBS_SK", "")
    tok = os.environ.get("OBS_SECURITY_TOKEN", "")
    ep = os.environ.get("OBS_ENDPOINT", "https://obs.cn-north-4.myhuaweicloud.com")
    return ak, sk, tok, ep


def sign(method: str, bucket: str, key: str, content_md5: str = "",
         content_type: str = "", date: str = "", sk: str = "", token: str = "") -> str:
    """OBS V2 签名。"""
    resource = f"/{bucket}/{key}" if key else f"/{bucket}/"
    string_to_sign = "\n".join([method, content_md5, content_type, date,
                                ("x-obs-security-token:" + token + "\n" if token else "") + resource])
    sig = base64.b64encode(hmac.new(sk.encode(), string_to_sign.encode(), hashlib.sha1).digest()).decode()
    return sig


def parse_obs_url(u: str) -> tuple[str, str]:
    if not u.startswith("obs://"):
        raise ValueError("路径需形如 obs://bucket/key")
    rest = u[len("obs://"):]
    bucket, _, key = rest.partition("/")
    return bucket, key


def request(method: str, url: str, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def with_retry(fn, *a, **kw):
    last = None
    for i in range(MAX_RETRY):
        try:
            return fn(*a, **kw)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.4 * (2 ** i))
    raise last  # type: ignore[misc]


def do_put(ak, sk, tok, ep, src: Path, dst_url: str, recursive: bool) -> None:
    bucket, key = parse_obs_url(dst_url)
    files: list[tuple[Path, str]] = []
    if src.is_dir():
        if not recursive:
            out(ok=False, action="put", error="源是目录，请加 --recursive")
            sys.exit(1)
        base = key.rstrip("/")
        for f in sorted(src.rglob("*")):
            if f.is_file():
                rel = f.relative_to(src).as_posix()
                files.append((f, f"{base}/{rel}" if base else rel))
    else:
        files.append((src, key or src.name))

    total = 0
    t0 = time.time()
    for f, k in files:
        body = f.read_bytes()
        md5 = base64.b64encode(hashlib.md5(body).digest()).decode()
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        sig = sign("PUT", bucket, k, md5, ctype, date, sk, tok)
        headers = {"Authorization": f"OBS {ak}:{sig}", "Content-MD5": md5,
                   "Content-Type": ctype, "Date": date}
        if tok:
            headers["x-obs-security-token"] = tok
        url = f"{ep}/{bucket}/{urllib.parse.quote(k)}"
        with_retry(request, "PUT", url, body, headers)
        total += len(body)

    out(ok=True, action="put", objects=len(files), bytes=total,
        elapsed_ms=int((time.time() - t0) * 1000), bucket=bucket, prefix=key)


def do_get(ak, sk, tok, ep, src_url: str, dst: str) -> None:
    bucket, key = parse_obs_url(src_url)
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    sig = sign("GET", bucket, key, "", "", date, sk, tok)
    headers = {"Authorization": f"OBS {ak}:{sig}", "Date": date}
    if tok:
        headers["x-obs-security-token"] = tok
    url = f"{ep}/{bucket}/{urllib.parse.quote(key)}"
    t0 = time.time()
    _, body = with_retry(request, "GET", url, None, headers)
    Path(dst).write_bytes(body)
    out(ok=True, action="get", bytes=len(body), dst=dst, elapsed_ms=int((time.time() - t0) * 1000))


def do_ls(ak, sk, tok, ep, prefix_url: str) -> None:
    bucket, key = parse_obs_url(prefix_url)
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    sig = sign("GET", bucket, "", "", "", date, sk, tok)
    headers = {"Authorization": f"OBS {ak}:{sig}", "Date": date}
    if tok:
        headers["x-obs-security-token"] = tok
    url = f"{ep}/{bucket}?prefix={urllib.parse.quote(key)}&max-keys=100"
    _, body = with_retry(request, "GET", url, None, headers)
    import re
    keys = re.findall(r"<Key>(.*?)</Key>", body.decode("utf-8", "ignore"))
    sizes = re.findall(r"<Size>(.*?)</Size>", body.decode("utf-8", "ignore"))
    out(ok=True, action="ls", bucket=bucket, count=len(keys),
        objects=[{"key": k, "size": int(s)} for k, s in zip(keys, sizes)])


def do_sign(ak, sk, tok, ep, url: str, expires: int) -> None:
    bucket, key = parse_obs_url(url)
    exp = int(time.time()) + expires
    resource = f"/{bucket}/{key}"
    string_to_sign = "\n".join(["GET", "", "", str(exp), resource])
    sig = base64.b64encode(hmac.new(sk.encode(), string_to_sign.encode(), hashlib.sha1).digest()).decode()
    share = (f"{ep}/{bucket}/{urllib.parse.quote(key)}"
             f"?AccessKeyId={ak}&Expires={exp}&Signature={urllib.parse.quote(sig)}")
    if tok:
        share += f"&x-obs-security-token={urllib.parse.quote(tok)}"
    out(ok=True, action="sign", url=share, expires_in=expires)


def main() -> int:
    ap = argparse.ArgumentParser(description="华为云 OBS 操作")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("put"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--recursive", action="store_true")
    g = sub.add_parser("get"); g.add_argument("src"); g.add_argument("dst")
    l = sub.add_parser("ls"); l.add_argument("prefix")
    s = sub.add_parser("sign"); s.add_argument("url"); s.add_argument("--expires", type=int, default=3600)

    a = ap.parse_args()
    ak, sk, tok, ep = creds()
    if not ak or not sk:
        out(ok=False, action=a.cmd, error="缺少凭证",
            hint="设置 OBS_AK/OBS_SK，STS 场景再加 OBS_SECURITY_TOKEN")
        return 1

    try:
        if a.cmd == "put":
            do_put(ak, sk, tok, ep, Path(a.src), a.dst, a.recursive)
        elif a.cmd == "get":
            do_get(ak, sk, tok, ep, a.src, a.dst)
        elif a.cmd == "ls":
            do_ls(ak, sk, tok, ep, a.prefix)
        elif a.cmd == "sign":
            do_sign(ak, sk, tok, ep, a.url, a.expires)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:200]
        out(ok=False, action=a.cmd, error=f"HTTP {e.code}", detail=body,
            hint="403 多为桶策略/凭证无权限；STS 需带 security_token")
        return 1
    except Exception as e:  # noqa: BLE001
        out(ok=False, action=a.cmd, error=str(e))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
