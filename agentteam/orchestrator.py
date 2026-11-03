"""主控：按 「规划 → 检索 → 写作 → 审校 → (必要时回炉)」 编排四个 Agent。"""

from __future__ import annotations

from .agents import (Agent, Message, PlannerAgent, RetrieverAgent,
                     ReviewerAgent, WriterAgent)


class Orchestrator:
    def __init__(self, max_rounds: int = 2) -> None:
        self.planner: Agent = PlannerAgent()
        self.retriever: Agent = RetrieverAgent()
        self.writer: Agent = WriterAgent()
        self.reviewer: Agent = ReviewerAgent()
        self.max_rounds = max_rounds

    def run(self, task: str, trace: bool = True) -> dict:
        context: list[Message] = []
        rounds = 0
        history: list[dict] = []

        while rounds < self.max_rounds:
            rounds += 1
            # 每轮都重新走 检索→写作→审校；首轮才需要规划
            if rounds == 1:
                for ag in (self.planner, self.retriever, self.writer, self.reviewer):
                    msg = ag.act(task, context)
                    context.append(msg)
                    history.append({"round": rounds, "agent": msg.sender,
                                    "role": msg.role, "summary": msg.content})
                    if trace:
                        print(f"[R{rounds}] {msg.role:<4} → {msg.content}")
            else:
                for ag in (self.writer, self.reviewer):
                    msg = ag.act(task, context)
                    context.append(msg)
                    history.append({"round": rounds, "agent": msg.sender,
                                    "role": msg.role, "summary": msg.content})
                    if trace:
                        print(f"[R{rounds}] {msg.role:<4} → {msg.content}")

            review = context[-1]
            if review.meta.get("verdict") == "通过":
                break

        final = context[-1]
        plan = next(m for m in context if m.sender == "planner")
        writer = [m for m in context if m.sender == "writer"][-1]
        return {
            "task": task,
            "rounds": rounds,
            "topic": plan.meta.get("topic"),
            "outline": plan.meta.get("outline"),
            "total_words": writer.meta.get("total_words"),
            "verdict": final.meta.get("verdict"),
            "issues": final.meta.get("issues", []),
            "history": history,
        }
