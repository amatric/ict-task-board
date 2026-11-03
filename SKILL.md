---
name: office-mail-sender
description: |
  帮用户在办公场景发送邮件：日报/周报、会议纪要、通知公告、附件投递。当用户说"把这封邮件发给…""帮我发周报""把产物作为附件寄出去"时使用。
  支持 SMTP/SSL、纯文本与 HTML 正文、附件、抄送、模板变量替换；凭证只从环境变量读取。
metadata:
  tags: office,email,smtp,skill,agent
  version: 1.0.0
---

# 办公邮件发送技能

把"发一封格式正确、附件齐全的办公邮件"固化成一条命令，避免每次手写 SMTP 代码。

## 何时使用

| 场景 | 用本技能 |
|:--|:--|
| 发日报/周报/会议纪要 | ✅ 有现成模板 |
| 把构建产物/报告作为附件发出 | ✅ 支持多附件 |
| 群发通知，需要抄送 | ✅ 支持 cc |
| 需要收件人已读回执/定时发送 | ❌ 本技能不覆盖，请用邮件系统 |
| 只是本地保存草稿 | ❌ 直接写文件 |

## 前置凭证（只从环境读）

```bash
export MAIL_HOST=smtp.example.com
export MAIL_PORT=465
export MAIL_USER=me@example.com
export MAIL_PASS=<授权码，不是登录密码>
export MAIL_FROM_NAME=张三
```

> 企业邮箱通常要用**授权码**而非登录密码；错误提示里也只会说"鉴权失败"，不会回显密码。

## 命令

```bash
# 纯文本
python3 scripts/send_mail.py --to a@x.com --subject "周报" --body "本周完成…"

# HTML 正文 + 附件 + 抄送
python3 scripts/send_mail.py \
  --to a@x.com,b@x.com --cc boss@x.com \
  --subject "第 45 周周报" \
  --html reports/week45.html \
  --attach reports/week45.pdf --attach data.csv

# 用模板 + 变量
python3 scripts/send_mail.py --to a@x.com \
  --template templates/weekly.md \
  --var name=张三 --var week=45 --var done="完成 A/B" --var todo="推进 C"
```

## 内置模板

`templates/` 下有三个，直接改或用 `--var` 填充：

| 模板 | 用途 | 变量 |
|:--|:--|:--|
| `weekly.md` | 周报 | `name` `week` `done` `todo` |
| `meeting.md` | 会议纪要 | `title` `date` `attendees` `decisions` `actions` |
| `notice.md` | 通知公告 | `title` `deadline` `content` |

## 输出约定

成功：一行 JSON，含 `ok` 与 `message_id`（部分服务端不返回 msgId，则为 `null`）。

```json
{"ok": true, "to": ["a@x.com"], "subject": "周报", "attachments": 2, "elapsed_ms": 860}
```

失败：`ok=false` + `error` + `hint`，退出码非 0。

## 安全约定

1. 凭证只从环境变量读，**代码、日志、错误信息都不回显**
2. 附件路径做 `..` 越界检查，避免 Agent 被诱导发出敏感文件
3. 默认走 SSL(465)；用 587 时自动 STARTTLS
4. 收件人做基本格式校验，非法地址直接拒绝，不发半截

## 参考

- `scripts/send_mail.py` —— 实现（SMTP/SSL、HTML、附件、模板）
- `templates/*.md` —— 三个办公模板
