"""主控：驱动 面试官 → 候选人 → 评估官 的多轮闭环。"""

from __future__ import annotations

from .agents import (CandidateAgent, EvaluatorAgent, InterviewerAgent,
                     Turn)


class InterviewOrchestrator:
    def __init__(self, rounds: int = 5, trace: bool = True) -> None:
        self.rounds = rounds
        self.trace = trace
        self.interviewer = InterviewerAgent()
        self.candidate = CandidateAgent()
        self.evaluator = EvaluatorAgent()

    def run(self) -> dict:
        history: list[Turn] = []
        for rnd in range(1, self.rounds + 1):
            q = self.interviewer.ask(rnd, history)
            history.append(q)
            a = self.candidate.answer(rnd, q, history)
            history.append(a)
            e = self.evaluator.evaluate(rnd, q, a)
            history.append(e)

            if self.trace:
                print(f"\n[第{rnd}轮] {q.speaker}：{q.content}")
                print(f"          {a.speaker}：{a.content[:60]}{'…' if len(a.content) > 60 else ''}")
                print(f"          {e.speaker}：{e.content}")

        report = self.evaluator.report()
        if self.trace:
            print("\n" + "=" * 60)
            print(f"加权总分：{report['weighted_total']}    建议：{report['advice']}")
            for d in report["detail"]:
                bar = "█" * max(1, int(d["score"] / 5))
                print(f"  {d['competency']:<8} 权重{d['weight']:.2f}  {d['score']:>5}  {bar}")

        return {"rounds": self.rounds, "report": report,
                "transcript": [{"round": t.round, "speaker": t.speaker,
                                "content": t.content, "meta": t.meta} for t in history]}
