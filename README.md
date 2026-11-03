# 办公邮件发送 Skill

华为 ICT 大赛云赛道 **赛题14（基于AI 开发者空间的 Agent 办公实践邮件发送 Skill 实践）** 的参评作品。

把"发一封格式正确、附件齐全的办公邮件"固化成一条命令：支持 SMTP/SSL、HTML 正文、多附件、抄送、Markdown 模板 + 变量替换。零第三方依赖。

## 解决的问题

Agent 发邮件常见的三个坑：

1. **每次重写一遍 SMTP 代码** → 固化成技能，一次调用
2. **中文主题乱码** → 统一走 `Header(subject, "utf-8")` 与 `formataddr`
3. **凭证写进代码** → 只从环境变量读，错误信息也不回显

## 命令

```bash
# 纯文本
python3 scripts/send_mail.py --to a@x.com --subject "周报" --body "本周完成…"

# HTML + 附件 + 抄送
python3 scripts/send_mail.py \
  --to a@x.com,b@x.com --cc boss@x.com \
  --subject "第 45 周周报" \
  --html reports/week45.html \
  --attach reports/week45.pdf --attach data.csv

# 模板 + 变量
python3 scripts/send_mail.py --to a@x.com \
  --template templates/weekly.md \
  --var name=张三 --var week=45 --var done="完成 A/B" --var todo="推进 C"

# 只组装不发送（自查结构）
python3 scripts/send_mail.py --to a@x.com --subject t --body b --dry-run
```

## 三个办公模板

| 模板 | 用途 | 变量 |
|:--|:--|:--|
| `templates/weekly.md` | 周报 | `name` `week` `done` `todo` |
| `templates/meeting.md` | 会议纪要 | `title` `date` `attendees` `decisions` `actions` |
| `templates/notice.md` | 通知公告 | `title` `deadline` `content` |

## 凭证

```bash
export MAIL_HOST=smtp.example.com
export MAIL_PORT=465            # 465=SSL，587=STARTTLS，自动切换
export MAIL_USER=me@example.com
export MAIL_PASS=<授权码>
export MAIL_FROM_NAME=张三
```

> 企业邮箱用**授权码**，不是登录密码。鉴权失败时的提示会明确说这一点。

## 输出

成功：

```json
{"ok": true, "to": ["a@x.com"], "cc": [], "subject": "周报", "attachments": 2, "elapsed_ms": 860}
```

失败（退出码非 0）：

```json
{"ok": false, "error": "SMTP 鉴权失败", "hint": "企业邮箱通常需要授权码而非登录密码"}
```

## 四项安全设计

1. **凭证零回显**：代码、日志、异常信息里都不出现密码
2. **附件路径校验**：相对路径基于项目根解析，检查文件存在，避免被诱导发出敏感文件
3. **收件人先校验再发**：`bad@` 这类直接拒绝，不会发出去一半
4. **`--dry-run`**：先看组装出来的 MIME 结构（有几段、什么类型），确认无误再真发

## 自测（不需要真实邮箱）

```bash
# 缺凭证
python3 scripts/send_mail.py --to a@x.com --subject t --body b

# 组装校验
MAIL_HOST=smtp.x.com MAIL_USER=a@x.com MAIL_PASS=p \
python3 scripts/send_mail.py --to a@x.com --subject "周报" \
  --template templates/weekly.md --var week=45 --var name=张三 \
  --var done="完成A" --var todo="推进B" --dry-run

# 非法地址拦截
MAIL_HOST=smtp.x.com MAIL_USER=a@x.com MAIL_PASS=p \
python3 scripts/send_mail.py --to bad --subject t --body b
```

## 目录

```
.
├── SKILL.md
├── scripts/send_mail.py
├── templates/{weekly,meeting,notice}.md
└── README.md
```
