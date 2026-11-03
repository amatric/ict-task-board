---
name: huawei-cloud-skill-finder
description: |
  帮 AI 在华为云能力库中定位"该用哪个技能/服务"。当用户说"华为云怎么做 XX""有没有现成的华为云技能""帮我找个能 XX 的华为云服务"时使用。
  覆盖计算、存储、数据库、AI、容器、运维、安全等方向的技能条目，支持关键词检索、按场景推荐、给出调用入口与最小示例。
metadata:
  tags: huawei-cloud,skill-discovery,service-catalog,agent
  version: 1.0.0
---

# 华为云技能发现（Skill Finder）

当用户描述一个**目标**（而不是点明某个服务）时，先用本技能把目标映射到具体的华为云能力，再决定调什么 API / 用什么工具。

## 工作方式

1. **抽取意图**：从用户话里抽「动作 + 对象 + 约束」，例如
   - "把图片里的文字识别出来" → 动作=识别、对象=图片文字、约束=无
   - "便宜的存归档日志" → 动作=存储、对象=日志、约束=低成本长期
2. **检索**：`python3 scripts/search_skills.py "<关键词>"`，可多个关键词
3. **确认**：把命中的 2-3 个候选连同**适用边界**给用户，说明取舍
4. **落地**：读取对应条目的 `entry`（API/SDK/CLI）与 `example`，给出最小可运行示例

## 命令

```bash
# 关键词检索（支持多词，空格分隔，任一命中即返回）
python3 scripts/search_skills.py "图片 文字识别"

# 按大类浏览
python3 scripts/search_skills.py --category AI

# 列出全部条目
python3 scripts/search_skills.py --all

# 看某条详情（含最小示例）
python3 scripts/search_skills.py --id obs-lifecycle
```

## 何时不要用本技能

- 用户已经点名了具体服务（"用 OBS 上传"）→ 直接给该服务用法，不必检索
- 问的是账号、计费、备案等非技术能力 → 指到对应控制台，不要硬套技能条目
- 需要实时价格/库存 → 本技能只给能力索引，价格请查官网

## 输出约定

给用户推荐时固定三段：

```
推荐：<技能名>（id）
为什么：<一句话说明匹配点>
怎么用：<entry>  +  最小示例代码块
备选：<另一个 id> —— <在什么情况下更合适>
```

不要一次列 10 个候选，**最多 3 个**，并说明优先级。

## 参考

- `references/catalog.md` —— 技能条目的可读目录（与 `skills_index.json` 同源）
- `scripts/search_skills.py` —— 检索实现（零依赖）
