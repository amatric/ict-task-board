"""主控：并行→串行的分阶段编排。

阶段一（可并行）：创意定规模
阶段二（依赖创意）：预算 / 物料 / 宣传 三条线
"""

from __future__ import annotations

from .roles import BudgetRole, CreativeRole, MaterialRole, PromoRole, Result


class CampusTeam:
    def __init__(self) -> None:
        self.creative = CreativeRole()
        self.budget = BudgetRole()
        self.material = MaterialRole()
        self.promo = PromoRole()

    def plan(self, brief: dict, trace: bool = True) -> dict:
        results: list[Result] = []

        r1 = self.creative.work(brief, results)
        results.append(r1)
        if trace:
            print(f"[阶段1] {r1.role} → {r1.summary}")

        for role in (self.budget, self.material, self.promo):
            r = role.work(brief, results)
            results.append(r)
            if trace:
                print(f"[阶段2] {r.role} → {r.summary}")

        return {
            "brief": brief,
            "stages": [
                {"stage": 1, "roles": [r1.role]},
                {"stage": 2, "roles": [r.role for r in results[1:]]},
            ],
            "results": [{"role": r.role, "summary": r.summary, "data": r.data} for r in results],
        }
