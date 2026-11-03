"""四个策划角色：创意 / 预算 / 物料 / 宣传。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    role: str
    summary: str
    data: dict = field(default_factory=dict)


@dataclass
class Role:
    name: str
    duty: str

    def work(self, brief: dict, prior: list[Result]) -> Result:
        raise NotImplementedError


class CreativeRole(Role):
    """创意：给出活动主题、形式与流程骨架。"""

    def __init__(self) -> None:
        super().__init__("创意", "定主题、定形式、排流程")

    def work(self, brief: dict, prior: list[Result]) -> Result:
        theme = brief.get("theme", "校园活动")
        audience = brief.get("audience", "全校学生")
        scale = brief.get("scale", 100)
        agenda = [
            ("签到 & 破冰", 20),
            ("主题分享", 30),
            ("分组互动", 60),
            ("成果展示", 30),
            ("颁奖 & 合影", 20),
        ]
        return Result(self.name,
                      f"主题「{theme}」面向{audience}，预计 {scale} 人，总时长 {sum(m for _, m in agenda)} 分钟",
                      {"theme": theme, "audience": audience, "scale": scale,
                       "agenda": [{"segment": s, "minutes": m} for s, m in agenda]})


class BudgetRole(Role):
    """预算：按人数与规模测算各项开销并给总预算。"""

    def __init__(self) -> None:
        super().__init__("预算", "测算开销、控总预算")

    def work(self, brief: dict, prior: list[Result]) -> Result:
        creative = next((r for r in prior if r.role == "创意"), None)
        scale = (creative.data.get("scale") if creative else brief.get("scale", 100)) or 100
        venue = 800
        material = round(scale * 6)
        prize = 1500
        promo = 600
        misc = round((venue + material + prize + promo) * 0.1)
        total = venue + material + prize + promo + misc
        return Result(self.name, f"总预算 ¥{total}（人均 ¥{total / scale:.1f}）",
                      {"breakdown": {"场地": venue, "物料": material, "奖品": prize,
                                     "宣传": promo, "机动": misc},
                       "total": total, "per_capita": round(total / scale, 1)})


class MaterialRole(Role):
    """物料：列清单与数量。"""

    def __init__(self) -> None:
        super().__init__("物料", "列清单、定数量")

    def work(self, brief: dict, prior: list[Result]) -> Result:
        creative = next((r for r in prior if r.role == "创意"), None)
        scale = (creative.data.get("scale") if creative else brief.get("scale", 100)) or 100
        items = [
            {"item": "签到表/二维码", "qty": 2},
            {"item": "桌牌", "qty": 8},
            {"item": "饮用水", "qty": scale},
            {"item": "纪念品", "qty": scale},
            {"item": "投影/音响", "qty": 1},
            {"item": "横幅", "qty": 2},
        ]
        return Result(self.name, f"{len(items)} 类物料，按 {scale} 人备量",
                      {"items": items, "scale": scale})


class PromoRole(Role):
    """宣传：给渠道与时间节奏。"""

    def __init__(self) -> None:
        super().__init__("宣传", "定渠道、排节奏")

    def work(self, brief: dict, prior: list[Result]) -> Result:
        creative = next((r for r in prior if r.role == "创意"), None)
        theme = creative.data.get("theme") if creative else brief.get("theme", "校园活动")
        channels = ["校园公众号", "班级群", "海报栏", "短视频号"]
        timeline = [
            {"phase": "预热", "when": "活动前 7 天", "action": f"发布主题「{theme}」悬念海报"},
            {"phase": "报名", "when": "活动前 5 天", "action": "开放报名表单，设置限额"},
            {"phase": "倒计时", "when": "活动前 1 天", "action": "群内提醒 + 流程预告"},
            {"phase": "复盘", "when": "活动后 2 天", "action": "发图文回顾，收集反馈"},
        ]
        return Result(self.name, f"{len(channels)} 个渠道，4 个节奏点",
                      {"channels": channels, "timeline": timeline})
