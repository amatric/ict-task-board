"""四个角色 Agent：规划 / 检索 / 写作 / 审校。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Message:
    sender: str
    role: str
    content: str
    meta: dict = field(default_factory=dict)


@dataclass
class Agent:
    name: str
    role: str
    system: str

    def act(self, task: str, context: list[Message]) -> Message:
        raise NotImplementedError


class PlannerAgent(Agent):
    """规划：把「写毕业论文」拆成可执行大纲。"""

    def __init__(self) -> None:
        super().__init__("planner", "规划", "负责把目标拆解为大纲与章节任务")

    def act(self, task: str, context: list[Message]) -> Message:
        topic = task.replace("帮我写一篇", "").replace("的毕业论文", "").strip() or task
        outline = [
            f"第1章 绪论（研究背景、问题定义、本文贡献）",
            f"第2章 相关工作（{topic} 的技术路线对比）",
            f"第3章 方法设计（总体架构、关键模块、算法细节）",
            f"第4章 实验与分析（数据集、指标、消融）",
            f"第5章 结论与展望",
        ]
        return Message(self.name, self.role,
                       "已生成 5 章大纲", {"topic": topic, "outline": outline})


class RetrieverAgent(Agent):
    """检索：为每章给出要点与需要引用的材料类型。"""

    def __init__(self) -> None:
        super().__init__("retriever", "检索", "负责为每章准备论据与参考方向")

    def act(self, task: str, context: list[Message]) -> Message:
        plan = next((m for m in context if m.sender == "planner"), None)
        outline = plan.meta.get("outline", []) if plan else []
        keys = {
            "绪论": ["3 篇近三年综述", "1 组行业数据", "明确研究缺口"],
            "相关工作": ["按技术路线分组", "每组 2-3 篇代表作", "指出差异"],
            "方法设计": ["架构图", "关键公式", "复杂度分析"],
            "实验与分析": ["基线选择依据", "主实验+消融", "统计显著性"],
            "结论与展望": ["回扣贡献", "局限性", "未来方向"],
        }
        briefs = []
        for ch in outline:
            for k, v in keys.items():
                if k in ch:
                    briefs.append({"chapter": ch, "evidence": v})
                    break
        return Message(self.name, self.role, f"为 {len(briefs)} 章准备了论据清单",
                       {"briefs": briefs})


class WriterAgent(Agent):
    """写作：按大纲与论据产出章节草稿。"""

    def __init__(self) -> None:
        super().__init__("writer", "写作", "负责成文，保证逻辑连贯")

    def act(self, task: str, context: list[Message]) -> Message:
        plan = next((m for m in context if m.sender == "planner"), None)
        ret = next((m for m in context if m.sender == "retriever"), None)
        outline = plan.meta.get("outline", []) if plan else []
        briefs = {b["chapter"]: b["evidence"] for b in (ret.meta.get("briefs", []) if ret else [])}
        drafts = []
        for ch in outline:
            ev = briefs.get(ch, [])
            drafts.append({
                "chapter": ch,
                "draft": f"【{ch}】本节围绕主题展开，需覆盖：{'；'.join(ev)}。"
                         f"写作要求：先给结论句，再展开论证，最后给出与下一章的衔接。",
                "words": 1200,
            })
        total = sum(d["words"] for d in drafts)
        return Message(self.name, self.role, f"产出 {len(drafts)} 章草稿，目标 {total} 字",
                       {"drafts": drafts, "total_words": total})


class ReviewerAgent(Agent):
    """审校：挑问题并给出修改意见（这里是规则化检查）。"""

    def __init__(self) -> None:
        super().__init__("reviewer", "审校", "负责挑逻辑漏洞与格式问题")

    def act(self, task: str, context: list[Message]) -> Message:
        writer = next((m for m in context if m.sender == "writer"), None)
        drafts = writer.meta.get("drafts", []) if writer else []
        issues = []
        for d in drafts:
            if "结论" not in d["draft"]:
                issues.append({"chapter": d["chapter"], "issue": "缺少结论句"})
            if d["words"] < 800:
                issues.append({"chapter": d["chapter"], "issue": "篇幅不足，建议补充案例"})
        if len(drafts) < 5:
            issues.append({"chapter": "整体", "issue": "章节数量偏少，需补充讨论章"})
        verdict = "通过" if not issues else "需修改"
        return Message(self.name, self.role, f"审校结论：{verdict}（{len(issues)} 条意见）",
                       {"verdict": verdict, "issues": issues})
