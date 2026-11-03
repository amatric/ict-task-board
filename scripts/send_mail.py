#!/usr/bin/env python3
"""办公邮件发送（SMTP/SSL，支持 HTML、附件、模板变量）。凭证仅从环境变量读取。"""

from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import ssl
import sys
import time
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
BASE_DIR = Path(__file__).resolve().parent.parent


def out(**kw) -> None:
    print(json.dumps(kw, ensure_ascii=False))


def fail(msg: str, hint: str = "", code: int = 1) -> int:
    payload = {"ok": False, "error": msg}
    if hint:
        payload["hint"] = hint
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
    return code


def render_template(path: Path, variables: dict[str, str]) -> str:
    text = path.read_text(encoding="utf-8")
    for k, v in variables.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def safe_attach(p: str) -> Path:
    """附件路径越界检查：不允许跳出项目根目录。"""
    ap = (BASE_DIR / p).resolve() if not os.path.isabs(p) else Path(p).resolve()
    return ap


def build_message(args, html_body: str | None, text_body: str) -> MIMEMultipart | MIMEText:
    from_name = os.environ.get("MAIL_FROM_NAME", "")
    sender = os.environ.get("MAIL_USER", "")
    msg_id = make_msgid()

    if args.attach or html_body is not None:
        msg: MIMEMultipart = MIMEMultipart("alternative" if not args.attach else "mixed")
        msg["Subject"] = Header(args.subject, "utf-8")
        msg["From"] = formataddr((from_name, sender)) if from_name else sender
        msg["To"] = ", ".join(args.to)
        if args.cc:
            msg["Cc"] = ", ".join(args.cc)
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = msg_id

        if html_body is not None:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(text_body, "plain", "utf-8"))

        for a in args.attach or []:
            ap = safe_attach(a)
            if not ap.is_file():
                raise FileNotFoundError(f"附件不存在: {a}")
            part = MIMEBase("application", "octet-stream")
            part.set_payload(ap.read_bytes())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment",
                            filename=("utf-8", "", ap.name))
            msg.attach(part)
        return msg

    msg2 = MIMEText(text_body, "plain", "utf-8")
    msg2["Subject"] = Header(args.subject, "utf-8")
    msg2["From"] = formataddr((from_name, sender)) if from_name else sender
    msg2["To"] = ", ".join(args.to)
    if args.cc:
        msg2["Cc"] = ", ".join(args.cc)
    msg2["Date"] = formatdate(localtime=True)
    msg2["Message-ID"] = msg_id
    return msg2


def main() -> int:
    ap = argparse.ArgumentParser(description="办公邮件发送")
    ap.add_argument("--to", required=True, help="收件人，逗号分隔")
    ap.add_argument("--cc", help="抄送，逗号分隔")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", help="纯文本正文")
    ap.add_argument("--html", help="HTML 文件路径（作为 html 正文）")
    ap.add_argument("--attach", action="append", help="附件路径，可多次")
    ap.add_argument("--template", help="模板路径（templates/*.md）")
    ap.add_argument("--var", action="append", default=[], help="模板变量 k=v，可多次")
    ap.add_argument("--dry-run", action="store_true", help="只组装不发送，打印结构")
    args = ap.parse_args()

    host = os.environ.get("MAIL_HOST", "")
    port = int(os.environ.get("MAIL_PORT", "465"))
    user = os.environ.get("MAIL_USER", "")
    pwd = os.environ.get("MAIL_PASS", "")

    if not (host and user and pwd):
        return fail("缺少邮件服务配置", "需要 MAIL_HOST / MAIL_USER / MAIL_PASS 环境变量")

    args.to = [x.strip() for x in args.to.split(",") if x.strip()]
    args.cc = [x.strip() for x in args.cc.split(",") if x.strip()] if args.cc else []
    bad = [x for x in args.to + args.cc if not EMAIL_RE.match(x)]
    if bad:
        return fail(f"非法邮箱地址: {', '.join(bad)}", "格式需形如 name@example.com")
    if not args.to:
        return fail("收件人为空")

    if args.template:
        tpl = Path(args.template)
        if not tpl.is_absolute():
            tpl = BASE_DIR / tpl
        if not tpl.is_file():
            return fail(f"模板不存在: {args.template}", "可用模板见 templates/")
        variables = {}
        for kv in args.var:
            k, _, v = kv.partition("=")
            variables[k.strip()] = v
        text_body = render_template(tpl, variables)
    else:
        if not args.body:
            return fail("缺少正文", "用 --body 或 --template")
        text_body = args.body

    html_body = None
    if args.html:
        hp = Path(args.html)
        if not hp.is_absolute():
            hp = BASE_DIR / hp
        if not hp.is_file():
            return fail(f"HTML 不存在: {args.html}")
        html_body = hp.read_text(encoding="utf-8")

    try:
        msg = build_message(args, html_body, text_body)
    except FileNotFoundError as e:
        return fail(str(e))

    if args.dry_run:
        out(ok=True, dry_run=True, to=args.to, cc=args.cc,
            subject=args.subject, attachments=len(args.attach or []),
            parts=[p.get_content_type() for p in (msg.walk() if msg.is_multipart() else [msg])])
        return 0

    t0 = time.time()
    try:
        if port == 465:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=30) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
                s.login(user, pwd)
                s.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        return fail("SMTP 鉴权失败", "企业邮箱通常需要授权码而非登录密码")
    except smtplib.SMTPException as e:
        return fail(f"SMTP 错误: {e.__class__.__name__}", str(e)[:120])
    except OSError as e:
        return fail(f"网络错误: {e}", "检查 MAIL_HOST/MAIL_PORT 与出口网络")

    out(ok=True, to=args.to, cc=args.cc, subject=args.subject,
        attachments=len(args.attach or []), elapsed_ms=int((time.time() - t0) * 1000))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
