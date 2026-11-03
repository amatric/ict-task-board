# GitHub 热门项目定时抓取与分析（Report + Dashboard）

华为 ICT 大赛云赛道 **赛题6（Scheduler-定时任务抓取与分析 GitHub 热门）** 的参评作品。

一个**只依赖 Python 标准库**的定时任务：按 cron 周期抓取 GitHub 近期热门仓库，做语言分布 / 星标总量 / 主题标签的统计分析，产出 Markdown 报表与 JSON 数据。

## 产物一：看板 Dashboard

```bash
python3 -m http.server 8000
# 打开 http://localhost:8000/dashboard.html
```

`dashboard.html` 读取 `output/latest.json`，渲染四张指标卡、语言分布条形图、星标总量 TOP 语言、高频主题标签、热门仓库 TOP 10 表格。纯 HTML + CSS + 原生 JS，无图表库依赖。

**Report 与 Dashboard 的关系**：`fetch_trending.py` 一次运行同时产出
- `output/report-<时间戳>.md` / `.json` —— **报表**，适合归档、diff、发到群里
- `output/latest.json` —— **看板数据源**，`dashboard.html` 实时读取渲染

两者同一份数据，两个消费形态：report 面向记录与传播，dashboard 面向交互查看。

## 产物二：为什么是"定时任务"而不是"跑一次脚本"

```bash
crontab crontab.example     # 每 6 小时自动抓一次
```

`run_cron.sh` 做了三件 cron 场景该做的事：

1. **日志落盘**：每次执行写 `logs/cron-<时间戳>.log`
2. **失败重试**：首次失败等 10 秒重试一次，避免偶发网络抖动丢数据
3. **工作目录固定**：`cd "$(dirname "$0")"`，cron 的环境没有你 shell 的 cwd

## 实际产出（真实数据）

```
样本数量：30 个仓库，合计 64,164 stars
语言分布：JavaScript 9 | Python 7 | TypeScript 3 | Kotlin 2 | HTML 2 ...
```

报表长这样（`output/latest.md`）：

```
## 语言分布（按仓库数）
| 语言       | 仓库数 | 占比  | 分布                   |
| JavaScript | 9      | 30.0% | ██████████████████████ |
| Python     | 7      | 23.3% | █████████████████      |
```

用等宽方块字符画分布条，**终端和 Markdown 里都能直接看**，不依赖图表库。

## 分析维度

| 维度 | 说明 |
|:--|:--|
| 语言分布 | 按仓库数统计，带占比与分布条 |
| 星标总量 TOP 语言 | 按语言汇总 stars，看哪个语言最"吸星" |
| 高频主题标签 | 聚合 `topics`，反映当下热点方向 |
| 热门仓库 TOP 10 | 名称、语言、stars、简介，附可点链接 |

## 用法

```bash
# 默认：最近 7 天创建、stars>100、取前 30
python3 fetch_trending.py

# 自定义窗口与数量
python3 fetch_trending.py --days 30 --top 50

# 带 token 提高 API 限额（未认证 10 次/分钟）
GITHUB_TOKEN=ghp_xxx python3 fetch_trending.py
```

## 产出文件

```
output/
├── report-<时间戳>.md     # 每次运行的快照
├── report-<时间戳>.json
├── latest.md              # 永远指向最新一次
└── latest.json
```

## 目录结构

```
.
├── fetch_trending.py     # 抓取 + 分析 + 渲染报表
├── dashboard.html        # 可视化看板（读 latest.json）
├── run_cron.sh           # cron 包装（日志 + 重试）
├── crontab.example       # 定时配置示例
├── output/               # 报表产出
└── README.md
```

## 技术说明

- **纯标准库**：`urllib` 请求、`json` 序列化、`collections.Counter` 聚合，无第三方依赖
- **搜索接口**：`GET /search/repositories?q=created:>YYYY-MM-DD stars:>100&sort=stars`
- **可重复运行**：每次生成带时间戳的快照，`latest.*` 保持最新，便于历史对比
- **失败可见**：API 错误码、异常原因都打到 stderr，cron 日志里能直接定位
