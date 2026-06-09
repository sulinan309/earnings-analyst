"""硬门槛检查（文档第四节）

硬门槛回答"状态是否有资格成立"，而非"状态有多强"。
高总分不能绕过硬门槛（文档第三节第 5 小节、第五节优先级）。
"""

from .states import State, BASE_WEIGHTS
from .market_data import Features
from .checkboxes import LayerEvidence, _strong_red_flag


def core_layer(state: State) -> str:
    """核心层 = 该状态基础权重最高的层（用于"核心层<60则状态无效"）"""
    weights = BASE_WEIGHTS[state]
    return max(weights, key=weights.get)


def has_a_class_trigger(layers: dict[str, LayerEvidence]) -> bool:
    """通用硬门槛：状态进入至少需 1 个 A 类数据触发（price/volume/index）"""
    for name in ("price", "volume", "index"):
        ev = layers.get(name)
        if ev and ev.available and any(c.triggered for c in ev.checks):
            return True
    return False


def check_hard_gate(
    state: State,
    f: Features,
    layers: dict[str, LayerEvidence],
    intraday_confirmed: bool,
) -> tuple[bool, str | None]:
    """检查某状态硬门槛，返回 (是否通过, 未通过原因)"""

    # ── 通用硬门槛 ──
    if not has_a_class_trigger(layers):
        return False, "无 A 类数据触发（B 类不能单独触发状态）"

    cl = core_layer(state)
    if layers[cl].available and layers[cl].score < 60:
        return False, f"核心层({cl})得分 {layers[cl].score:.0f} < 60"

    price = layers["price"].score
    strong_red = _strong_red_flag(f)

    # ── 各状态专属硬门槛 ──
    if state == State.DOWN_ACCEL:
        broke = f.breaks_prior_low or f.below_core_level or f.making_new_low
        confirm = f.vol_expansion or f.index_new_low or f.index_weakening
        if not (broke and confirm):
            return False, "需价位破位 且（成交放大 或 指数同步恶化）"

    elif state == State.DOWN_EXHAUST:
        if not f.no_new_low:
            return False, "仍在创新低，不能判定为下跌衰竭"
        if f.vol_expansion and f.breaks_prior_low:
            return False, "出现放量破位，不能判定为下跌衰竭"

    elif state == State.WEAK_REBOUND:
        if not f.no_break_prior_low:
            return False, "已跌破前低，弱反弹无效"
        if strong_red:
            return False, "成交层出现强红旗，弱反弹无效"

    elif state == State.VALID_REBOUND:
        if price < 60:
            return False, f"价位层 {price:.0f} < 60，有效反弹无效"
        if strong_red:
            return False, "成交层出现强红旗，有效反弹无效"
        if f.index_new_low:
            return False, "指数层系统性破位，有效反弹无效"

    elif state == State.TREND_REPAIR:
        if f.consec_above_core < 2:
            return False, "未连续站稳核心位，趋势修复无效"
        if price < 50:
            return False, "价位层不足，疑似仅由资金层驱动，趋势修复无效"

    elif state == State.UP_EXHAUST:
        stalling = f.upper_shadow or f.lower_high or f.fail_break_prior_high or not f.close_upper_third
        if not stalling:
            return False, "价位未滞涨/冲高回落，不能仅凭资金流减弱判断"

    elif state == State.DISTRIBUTION:
        if not f.vol_strong_expansion:
            return False, "成交未显著放大，不能判定为放量派发"
        if not (f.upper_shadow or f.break_short_support or f.below_core_level or f.close_near_low):
            return False, "价位未冲高回落/未跌破关键位，不能判定为放量派发"

    elif state == State.TREND_BREAK:
        if not (f.breaks_prior_low or f.below_core_level):
            return False, "未跌破核心支撑或前低，不能判定为趋势破坏"
        if not intraday_confirmed:
            return False, "仅盘中跌破，需收盘或次日确认"

    return True, None
