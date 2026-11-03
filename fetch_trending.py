#!/usr/bin/env python3
"""定时抓取 GitHub 热门仓库并按语言/星标分析，生成 Markdown + JSON 报表。

用法：
    python3 fetch_trending.py                 # 抓最近 7 天新建且高星的项目
    python3 fetch_trending.py --days 30 --top 15
    python3 fetch_trending.py --token $GITHUB_TOKEN

只依赖标准库，无需 pip install。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://api.github.com/search/repositories"
OUT_DIR = Path(__file__).resolve().parent / "output"


def search_repos(days: int, top: int, token: str | None) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"created:>{since} stars:>100"
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": str(min(top, 100)),
    })
    req = urllib.request.Request(f"{API}?{params}", headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "gh-trend-scheduler/1.0",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("items", [])


def analyze(items: list[dict], days: int) -> dict:
    langs = Counter((i.get("language") or "Unknown") for i in items)
    by_lang: dict[str, int] = {}
    for it in items:
        lang = it.get("language") or "Unknown"
        by_lang[lang] = by_lang.get(lang, 0) + int(it.get("stargazers_count", 0))

    topics = Counter()
    for it in items:
        for t in (it.get("topics") or []):
            topics[t] += 1

    created_span = [i for i in items if i.get("created_at")]

    return {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "window_days": days,
        "total": len(items),
        "total_stars": sum(int(i.get("stargazers_count", 0)) for i in items),
        "languages": langs.most_common(),
        "stars_by_language": sorted(by_lang.items(), key=lambda kv: -kv[1]),
        "top_topics": topics.most_common(10),
        "top_repos": [
            {
                "name": i.get("full_name"),
                "stars": int(i.get("stargazers_count", 0)),
                "language": i.get("language") or "Unknown",
                "url": i.get("html_url"),
                "description": (i.get("description") or "").strip(),
                "created_at": i.get("created_at"),
            }
            for i in items
        ],
        "_created_span": created_span,
    }


def bar(value: int, maxv: int, width: int = 22) -> str:
    if maxv <= 0:
        return ""
    n = max(1, round(value / maxv * width))
    return "█" * n


def render_markdown(a: dict) -> str:
    lines: list[str] = []
    lines.append(f"# GitHub 热门项目分析报表\n")
    lines.append(f"- 生成时间：`{a['generated_at']}`")
    lines.append(f"- 统计窗口：最近 **{a['window_days']}** 天创建的项目")
    lines.append(f"- 样本数量：**{a['total']}** 个仓库，合计 **{a['total_stars']:,}** stars\n")

    lines.append("## 语言分布（按仓库数）\n")
    maxc = a["languages"][0][1] if a["languages"] else 0
    lines.append("| 语言 | 仓库数 | 占比 | 分布 |")
    lines.append("|:--|--:|--:|:--|")
    for lang, c in a["languages"]:
        pct = f"{c / a['total'] * 100:.1f}%" if a["total"] else "-"
        lines.append(f"| {lang} | {c} | {pct} | `{bar(c, maxc)}` |")

    lines.append("\n## 星标总量 TOP 语言\n")
    maxs = a["stars_by_language"][0][1] if a["stars_by_language"] else 0
    lines.append("| 语言 | 星标合计 | 分布 |")
    lines.append("|:--|--:|:--|")
    for lang, s in a["stars_by_language"][:8]:
        lines.append(f"| {lang} | {s:,} | `{bar(s, maxs)}` |")

    if a["top_topics"]:
        lines.append("\n## 高频主题标签\n")
        lines.append(" ".join(f"`#{t}`×{c}" for t, c in a["top_topics"]))

    lines.append("\n## 热门仓库 TOP 10\n")
    lines.append("| # | 仓库 | 语言 | Stars | 说明 |")
    lines.append("|--:|:--|:--|--:|:--|")
    for idx, r in enumerate(a["top_repos"][:10], 1):
        desc = (r["description"] or "")[:48].replace("|", "\\|")
        lines.append(f"| {idx} | [{r['name']}]({r['url']}) | {r['language']} | {r['stars']:,} | {desc} |")

    lines.append("\n---\n")
    lines.append("> 由 `fetch_trending.py` 定时任务自动生成。")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取并分析 GitHub 热门项目")
    ap.add_argument("--days", type=int, default=7, help="统计最近多少天内创建的项目")
    ap.add_argument("--top", type=int, default=30, help="抓取仓库数量")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub Token（可选，提高限额）")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        items = search_repos(args.days, args.top, args.token)
    except urllib.error.HTTPError as e:
        print(f"[ERROR] GitHub API 返回 {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 请求失败: {e}", file=sys.stderr)
        return 1

    data = analyze(items, args.days)
    data.pop("_created_span", None)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (OUT_DIR / f"report-{stamp}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_markdown(data)
    (OUT_DIR / f"report-{stamp}.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "latest.md").write_text(md, encoding="utf-8")
    (OUT_DIR / "latest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 抓取 {data['total']} 个仓库，已生成 output/report-{stamp}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
