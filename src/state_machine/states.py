"""8 个状态定义、基础权重、风险分类与动作映射

对应文档第二节（状态定义）、第三节（基础权重）、第五节（风险/普通分类）。

四层固定为：价位层 price / 成交层 volume / 指数层 index / 资金层 flow
"""

from enum import Enum


class State(str, Enum):
    """8 个基础状态"""

    DOWN_ACCEL = "下跌加速"
    DOWN_EXHAUST = "下跌衰竭"
    WEAK_REBOUND = "弱反弹"
    VALID_REBOUND = "有效反弹"
    TREND_REPAIR = "趋势修复"
    UP_EXHAUST = "上涨衰竭"
    DISTRIBUTION = "放量派发"
    TREND_BREAK = "趋势破坏"


# ── 各状态基础权重（文档第二节每个状态的"基础权重"）──
# 顺序：price 价位 / volume 成交 / index 指数 / flow 资金，合计 = 100
BASE_WEIGHTS: dict[State, dict[str, float]] = {
    State.DOWN_ACCEL:    {"price": 35, "volume": 30, "index": 25, "flow": 10},
    State.DOWN_EXHAUST:  {"price": 30, "volume": 35, "index": 20, "flow": 15},
    State.WEAK_REBOUND:  {"price": 35, "volume": 25, "index": 25, "flow": 15},
    State.VALID_REBOUND: {"price": 35, "volume": 20, "index": 30, "flow": 15},
    State.TREND_REPAIR:  {"price": 45, "volume": 20, "index": 25, "flow": 10},
    State.UP_EXHAUST:    {"price": 30, "volume": 35, "index": 20, "flow": 15},
    State.DISTRIBUTION:  {"price": 35, "volume": 40, "index": 15, "flow": 10},
    State.TREND_BREAK:   {"price": 45, "volume": 25, "index": 20, "flow": 10},
}


# ── 风险状态（仍在恶化中 + 需要立即响应，可直接覆盖，不等待防抖）──
RISK_STATES: frozenset[State] = frozenset(
    {State.DOWN_ACCEL, State.DISTRIBUTION, State.TREND_BREAK}
)

# ── 普通状态（处于过渡中 + 需要时间确认）──
NORMAL_STATES: frozenset[State] = frozenset(
    {
        State.DOWN_EXHAUST,
        State.WEAK_REBOUND,
        State.VALID_REBOUND,
        State.TREND_REPAIR,
        State.UP_EXHAUST,
    }
)


STATE_DESCRIPTIONS: dict[State, str] = {
    State.DOWN_ACCEL: "价格持续创新低、成交放大，下跌动量尚未衰竭，卖压主导，不适合抄底。",
    State.DOWN_EXHAUST: "下跌动量开始衰减但尚未确认反转，卖压边际减弱，还不是买点。",
    State.WEAK_REBOUND: "价格开始反弹但质量未确认，可能只是技术性喘息或空头回补。",
    State.VALID_REBOUND: "下跌动量结束、收复关键位且买盘具一定主动性，可考虑战术仓。",
    State.TREND_REPAIR: "反弹得到延续，连续站稳核心位、板块同步修复，进入趋势修复。",
    State.UP_EXHAUST: "上涨动量减弱但尚未确认反转，进入利润保护观察。",
    State.DISTRIBUTION: "上方资金兑现，放量但价格涨不动，常为顶部或阶段顶部信号。",
    State.TREND_BREAK: "反弹失败/上升趋势被破坏，下跌趋势恢复，战术仓应退出。",
}


# ── 状态 → 基础建议动作（文档第二节"动作"，再由评分等级/组合约束细化）──
STATE_BASE_ACTION: dict[State, str] = {
    State.DOWN_ACCEL: "禁止加仓，不接飞刀，只允许观察或减战术仓",
    State.DOWN_EXHAUST: "观察，不急于加仓，等待弱反弹或有效反弹确认",
    State.WEAK_REBOUND: "不作为强买点，可观察，极小仓试探需写 Decision Log",
    State.VALID_REBOUND: "允许小仓战术加仓，评分高可标准战术仓，仍受组合约束限制",
    State.TREND_REPAIR: "可考虑第二/三笔战术仓，不得突破组合上限",
    State.UP_EXHAUST: "提高警惕，准备利润保护，战术仓可减 30%-50%，不急于清核心仓",
    State.DISTRIBUTION: "减战术仓、启动利润保护，跌破核心支撑则清战术仓",
    State.TREND_BREAK: "清战术仓，禁止新增仓位，核心仓进入风险复盘",
}
