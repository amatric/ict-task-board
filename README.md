# 华为云技能发现 Skill

华为 ICT 大赛云赛道 **赛题9（Skill-让 AI 帮你找到所需的华为云技能）** 的参评作品。

一个可直接被 Agent 加载的 **Skill**：当用户说"华为云能不能做 XX""有没有现成的服务"时，把**目标**映射到**具体华为云能力**，给出接入入口与最小示例，并说明适用边界。

## 它解决什么问题

Agent 常见的失败不是"不会写代码"，而是**选错服务**。用户说"把图片里的字提出来"，直接答 ECS 部署一个 OCR 服务就绕远了——该用 OCR 的托管接口。

本 Skill 的做法是：

```
抽意图 → 检索能力索引 → 给 2-3 个候选 + 适用边界 → 落地最小示例
```

## 结构

```
.
├── SKILL.md                  # Skill 定义（Agent 加载入口）
├── skills_index.json         # 17 条华为云能力索引（结构化）
├── scripts/search_skills.py  # 检索实现（零依赖）
├── references/catalog.md     # 可读目录（与索引同源）
└── README.md
```

## 能力索引覆盖

| 大类 | 条目 |
|:--|:--|
| 计算 | ECS、函数工作流 FunctionGraph |
| 存储 | OBS + 生命周期 |
| 数据库 | RDS for MySQL、DRS 迁移、DWS 数仓、CSS 云搜索 |
| AI | ModelArts、MaaS 大模型、OCR 文字识别 |
| 容器 | CCE |
| 网络 | ELB + AS |
| 安全 | IAM 委托 + STS、WAF + DDoS |
| 运维 | COC 批量命令、AOM 监控 |
| 研发 | CodeArts 流水线 |

每条包含 `summary`（是什么）、`entry`（怎么调）、`boundary`（什么场景不该用它）、`example`（最小可跑示例）。

## 用法

```bash
# 关键词检索（支持一个参数里多个词）
python3 scripts/search_skills.py "图片 文字识别"
python3 scripts/search_skills.py "定时 轻量"
python3 scripts/search_skills.py "容器 编排"

# 按大类浏览
python3 scripts/search_skills.py --category AI

# 全量列表 / 单条详情
python3 scripts/search_skills.py --all
python3 scripts/search_skills.py --id obs-lifecycle
```

真实输出：

```
$ python3 scripts/search_skills.py "定时 轻量"
命中 2 条（按相关度降序）：

■ 函数工作流 FunctionGraph  [fgs-func]  · 计算
   按需执行的事件驱动计算，适合定时任务、Webhook、轻量 API。
   适用边界：长时任务(>15min)或常驻服务用 ECS
   接入：控制台 / API: POST /v2/{project_id}/fgs/functions
   示例：
     函数 + 定时触发器 cron: 0 */6 * * * ? 每 6 小时跑一次
```

## 设计要点

1. **`boundary` 字段是关键**：只告诉 AI"有这个服务"不够，还要告诉它"什么情况下别用"。比如 ECS 的边界写着"短任务用函数工作流更省"。
2. **检索是加权包含匹配**：name/summary/category/keywords 任一命中即计分，按命中词数排序，默认只返回 3 条——避免一次甩给用户十个候选。
3. **零依赖**：纯标准库，Agent 环境里 `python3` 在就能跑。
4. **SKILL.md 里写了「何时不要用本技能」**：用户已点名服务、或问的是计费备案这类非技术问题时不硬套，避免滥用。

## 接入 Agent

把本目录放进 skills 目录即可（例如 `~/.agents/skills/huawei-cloud-skill-finder/`）。Agent 读到 `SKILL.md` 的 frontmatter 后，会在用户描述目标而非点名服务时自动启用。

也可以直接当命令行工具用：

```bash
python3 scripts/search_skills.py "便宜的存归档日志"
```
