"""面试三方：面试官 / 候选人 / 评估官，加上一个主控调度。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Turn:
    round: int
    speaker: str
    content: str
    meta: dict = field(default_factory=dict)


@dataclass
class Competency:
    """岗位能力项与权重。"""
    name: str
    weight: float


DEFAULT_COMPETENCIES = [
    Competency("编程基础", 0.25),
    Competency("系统设计", 0.25),
    Competency("问题排查", 0.20),
    Competency("沟通表达", 0.15),
    Competency("学习潜力", 0.15),
]


class InterviewerAgent:
    """面试官：按能力项出题，追问候选人的薄弱点。"""

    name = "面试官"

    def __init__(self, competencies: list[Competency] | None = None) -> None:
        self.competencies = competencies or DEFAULT_COMPETENCIES

    def ask(self, rnd: int, history: list[Turn]) -> Turn:
        comp = self.competencies[(rnd - 1) % len(self.competencies)]
        weak = [t for t in history if t.speaker == "评估官" and comp.name in t.content]
        if weak and rnd > 1:
            q = f"围绕「{comp.name}」再深入一层：请举一个你踩过坑的具体例子，并说明怎么定位的。"
        else:
            q = f"请谈谈你在「{comp.name}」方面的经验，给一个具体项目例子。"
        return Turn(rnd, self.name, q, {"competency": comp.name})


class CandidateAgent:
    """候选人：按能力项作答（规则化，可替换为真实 LLM）。"""

    name = "候选人"

    def __init__(self, answers: dict[str, tuple[str, float]] | None = None) -> None:
        # 能力项 -> (答案文本, 自评分 0~1)，用来模拟不同候选人
        self.answers = answers or {
            "编程基础": ("做过一个 3 万行的 Python 服务，负责核心调度模块，重写过一次并发模型，QPS 从 200 提到 1200。", 0.8),
            "系统设计": ("设计过一个采集-清洗-入库的流水线，用消息队列削峰，失败重试走死信队列。", 0.7),
            "问题排查": ("线上内存泄漏，用 pprof 定位到一个缓存没设上限，加了 LRU 与过期时间。", 0.75),
            "沟通表达": ("每周主持跨团队对齐会，把需求拆成可交付的里程碑。", 0.65),
            "学习潜力": ("半年内自学了 Rust 并给内部工具写了插件。", 0.8),
        }

    def answer(self, rnd: int, question: Turn, history: list[Turn]) -> Turn:
        comp = question.meta.get("competency", "")
        text, conf = self.answers.get(comp, ("这方面经验较少，但可以快速学习。", 0.4))
        return Turn(rnd, self.name, text, {"competency": comp, "confidence": conf})


class EvaluatorAgent:
    """评估官：对每轮作答打分，最后汇总加权总分与录用建议。"""

    name = "评估官"

    def __init__(self, competencies: list[Competency] | None = None,
                 threshold: float = 0.7) -> None:
        self.competencies = competencies or DEFAULT_COMPETENCIES
        self.threshold = threshold
        self.scores: dict[str, float] = {}

    def evaluate(self, rnd: int, question: Turn, answer: Turn) -> Turn:
        comp = question.meta.get("competency", "")
        base = float(answer.meta.get("confidence", 0.5))
        # 简单规则：答案过短或含"较少"降分
        # 只有明显敷衍（过短或自认经验少）才压分
        if len(answer.content) < 15 or "较少" in answer.content:
            base = min(base, 0.45)
        self.scores[comp] = round(base * 100, 1)
        verdict = "达标" if base >= self.threshold else "偏弱"
        return Turn(rnd, self.name, f"「{comp}」评分 {self.scores[comp]}，{verdict}",
                    {"competency": comp, "score": self.scores[comp], "verdict": verdict})

    def report(self) -> dict:
        total = 0.0
        detail = []
        for c in self.competencies:
            s = self.scores.get(c.name, 0.0)
            total += s * c.weight
            detail.append({"competency": c.name, "weight": c.weight, "score": s})
        if total >= 80:
            advice = "建议录用（可给 senior 岗位）"
        elif total >= 65:
            advice = "建议录用（junior/中级）"
        elif total >= 50:
            advice = "建议加面一轮"
        else:
            advice = "不建议录用"
        return {"weighted_total": round(total, 1), "detail": detail, "advice": advice,
                "threshold": self.threshold * 100}
