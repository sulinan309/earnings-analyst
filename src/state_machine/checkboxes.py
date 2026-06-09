"""各状态四层 checkbox 判定（文档第二节各状态"进入条件"）

每个 checkbox 把业务文档的自然语言条件映射为 Features 上的可计算判据。
layer 得分 = 满足比例 × 100（文档第三节）。

数据等级：价位/成交/指数三层为 A 类；资金层为 B 类。
- 价位/成交层永远可评估（来自 OHLCV）。
- 指数层仅在提供指数数据时可评估。
- 资金层仅在提供 B 类资金数据时可评估，否则整层不可用、得分 0、数据质量下降。
"""

from dataclasses import dataclass
from typing import Callable

from .states import State
from .market_data import Features


@dataclass
class CheckResult:
    name: str
    triggered: bool
    available: bool
    data_class: str  # "A" / "B"


@dataclass
class LayerEvidence:
    layer: str                      # price/volume/index/flow
    checks: list[CheckResult]
    available: bool                 # 该层是否可评估
    score: float                    # 0-100，满足比例×100（不可用时为 0）

    @property
    def triggered_names(self) -> list[str]:
        return [c.name for c in self.checks if c.triggered]


# ── 复合判据 ──

def _strong_red_flag(f: Features) -> bool:
    """成交层强红旗：显著放量且冲高回落或收盘弱于均价线"""
    return f.vol_strong_expansion and (f.upper_shadow or f.close_below_vwap)


# 每个 (name, predicate) —— predicate: Features -> bool
Check = tuple[str, Callable[[Features], bool]]

# 各状态各层的 checkbox 定义
STATE_CHECKS: dict[State, dict[str, list[Check]]] = {
    State.DOWN_ACCEL: {
        "price": [
            ("连续创新低", lambda f: f.consec_new_lows >= 2),
            ("跌破前低", lambda f: f.breaks_prior_low),
            ("跌破关键平台", lambda f: f.below_core_level),
            ("收盘接近日内低点", lambda f: f.close_near_low),
        ],
        "volume": [
            ("放量下跌", lambda f: f.vol_expansion and f.down_day),
            ("成交额显著高于均值", lambda f: f.vol_strong_expansion),
            ("收盘低于开盘", lambda f: f.close_below_open),
            ("下跌日成交放大", lambda f: f.down_day and f.vol_expansion),
        ],
        "index": [
            ("本地指数同步破位", lambda f: f.index_new_low),
            ("行业指数走弱", lambda f: f.industry_weak or f.index_down),
            ("跨市场压力继续恶化", lambda f: f.index_weakening or f.index_down),
        ],
        "flow": [
            ("主动卖盘增加", lambda f: f.active_sell_up),
            ("资金净流出扩大", lambda f: f.net_outflow_expanding),
            ("大单净流出扩大", lambda f: f.big_order_outflow),
        ],
    },
    State.DOWN_EXHAUST: {
        "price": [
            ("不再创新低", lambda f: f.no_new_low),
            ("收盘高于日内低点", lambda f: not f.close_near_low),
            ("下影线变多", lambda f: f.lower_shadow),
            ("低点开始抬高", lambda f: f.higher_low),
        ],
        "volume": [
            ("缩量", lambda f: f.vol_contraction),
            ("下跌时成交开始减少", lambda f: f.down_day and f.vol_contraction),
            ("放量但价格不再下破", lambda f: f.vol_expansion and f.no_break_prior_low),
            ("卖压释放后成交回落", lambda f: f.vol_contraction),
        ],
        "index": [
            ("本地指数不创新低", lambda f: f.index_no_new_low),
            ("行业指数跌幅收敛", lambda f: f.index_converging or not f.industry_weak),
            ("外部压力不再恶化", lambda f: not f.index_weakening),
        ],
        "flow": [
            ("主动卖盘减少", lambda f: not f.active_sell_up),
            ("资金流出收窄", lambda f: f.net_inflow_improving),
            ("大单卖出减少", lambda f: not f.big_order_outflow),
        ],
    },
    State.WEAK_REBOUND: {
        "price": [
            ("收复第一关键位", lambda f: f.reclaim_first_level),
            ("但未站稳核心位", lambda f: f.below_core_level),
            ("不破前低", lambda f: f.no_break_prior_low),
            ("反抽存在但结构不强", lambda f: f.reclaim_first_level and not f.holds_core_level),
        ],
        "volume": [
            ("温和放量", lambda f: f.mild_expansion),
            ("没有明显冲高回落", lambda f: not f.upper_shadow),
            ("成交未出现强红旗", lambda f: not _strong_red_flag(f)),
            ("量能不足以确认主动买盘", lambda f: not f.vol_strong_expansion),
        ],
        "index": [
            ("本地指数小幅企稳", lambda f: f.index_stabilizing),
            ("行业指数不再恶化", lambda f: not f.industry_weak),
            ("外部压力边际缓和", lambda f: f.index_converging or f.index_stabilizing),
        ],
        "flow": [
            ("净流入由负转正", lambda f: f.net_inflow_turning_positive),
            ("主动买盘略有恢复", lambda f: f.active_buy_recovering),
            ("低位有承接但未主动扫货", lambda f: not f.active_buy_increasing),
        ],
    },
    State.VALID_REBOUND: {
        "price": [
            ("收盘收复第一关键位", lambda f: f.reclaim_first_level),
            ("日内回踩不破前低", lambda f: f.no_break_prior_low),
            ("收盘位于日内振幅上1/3", lambda f: f.close_upper_third),
            ("原压力位开始转为支撑", lambda f: f.holds_core_level or f.reclaim_first_level),
        ],
        "volume": [
            ("放量上涨", lambda f: f.vol_expansion and f.up_day),
            ("缩量止跌后次日放量上攻", lambda f: f.vol_expansion and f.up_day),
            ("没有放量冲高回落", lambda f: not (f.vol_expansion and f.upper_shadow)),
            ("收盘不低于日内均价线", lambda f: f.close_above_vwap),
        ],
        "index": [
            ("本地指数不再创新低", lambda f: f.index_no_new_low),
            ("行业指数同步企稳", lambda f: f.index_stabilizing or not f.industry_weak),
            ("外部压力不继续恶化", lambda f: not f.index_weakening),
            ("主风险定价链条停止恶化", lambda f: not f.index_new_low),
        ],
        "flow": [
            ("主动买盘增加", lambda f: f.active_buy_increasing),
            ("资金净流入改善", lambda f: f.net_inflow_improving),
            ("上方卖墙被吃后价格站稳", lambda f: f.close_upper_third and f.up_day),
            ("低位承接转为主动上攻", lambda f: f.active_buy_increasing),
        ],
    },
    State.TREND_REPAIR: {
        "price": [
            ("连续2日站稳核心关键位", lambda f: f.consec_above_core >= 2),
            ("突破前期压力位", lambda f: f.breaks_prior_high),
            ("形成上升结构", lambda f: f.higher_low and f.up_day),
            ("回踩不破", lambda f: f.holds_core_level),
        ],
        "volume": [
            ("持续放量", lambda f: f.vol_expansion),
            ("没有量价背离", lambda f: not f.vol_price_divergence),
            ("量能温和扩大", lambda f: f.mild_expansion or f.vol_expansion),
            ("上涨成交健康下跌成交收缩", lambda f: f.healthy_volume),
        ],
        "index": [
            ("本地指数同步修复", lambda f: f.index_repairing),
            ("行业指数同步修复", lambda f: f.industry_repairing or not f.industry_weak),
            ("跨市场压力缓和", lambda f: not f.index_weakening),
            ("同板块核心标的同步走强", lambda f: f.index_up),
        ],
        "flow": [
            ("主动买盘持续", lambda f: f.active_buy_increasing),
            ("资金流入稳定", lambda f: f.net_inflow_improving),
            ("南向北向机构类资金改善", lambda f: f.net_inflow_improving),
            ("不再只是低位被动承接", lambda f: not f.flow_passive_only),
        ],
    },
    State.UP_EXHAUST: {
        "price": [
            ("冲高回落", lambda f: f.upper_shadow),
            ("无法突破前高", lambda f: f.fail_break_prior_high or not f.breaks_prior_high),
            ("收盘低于日内振幅上1/3", lambda f: not f.close_upper_third),
            ("高点不再抬高", lambda f: f.lower_high),
        ],
        "volume": [
            ("放量但涨不动", lambda f: f.vol_expansion and not f.up_day),
            ("量价背离", lambda f: f.vol_price_divergence),
            ("上涨成交放大但收盘质量差", lambda f: f.vol_expansion and f.close_below_vwap),
            ("多次冲高回落", lambda f: f.upper_shadow),
        ],
        "index": [
            ("本地指数转弱", lambda f: f.index_weakening),
            ("行业指数转弱", lambda f: f.industry_weak),
            ("同板块分化加剧", lambda f: f.index_down),
            ("主线资金切换", lambda f: f.index_weakening),
        ],
        "flow": [
            ("主动买盘减弱", lambda f: not f.active_buy_increasing),
            ("净流入收窄", lambda f: not f.net_inflow_improving),
            ("大单买入下降", lambda f: f.big_order_outflow or not f.active_buy_increasing),
            ("只剩低位承接缺少主动上攻", lambda f: f.flow_passive_only),
        ],
    },
    State.DISTRIBUTION: {
        "volume": [
            ("成交显著放大", lambda f: f.vol_strong_expansion),
            ("收盘低于开盘", lambda f: f.close_below_open),
            ("收盘低于日内均价线", lambda f: f.close_below_vwap),
            ("成交放大但价格涨不动", lambda f: f.vol_expansion and not f.up_day),
        ],
        "price": [
            ("跌破短线支撑", lambda f: f.break_short_support),
            ("冲高回落形态", lambda f: f.upper_shadow),
            ("收盘接近日内低点", lambda f: f.close_near_low),
            ("前高突破失败", lambda f: f.fail_break_prior_high),
        ],
        "index": [
            ("本地指数同步走弱", lambda f: f.index_weakening or f.index_down),
            ("行业指数同步走弱", lambda f: f.industry_weak),
            ("板块核心标的集体冲高回落", lambda f: f.index_down),
        ],
        "flow": [
            ("主动卖盘出现", lambda f: f.active_sell_up),
            ("大单净流出", lambda f: f.big_order_outflow),
            ("资金流入明显收窄", lambda f: not f.net_inflow_improving),
            ("上方卖压明显", lambda f: f.active_sell_up),
        ],
    },
    State.TREND_BREAK: {
        "price": [
            ("跌破前低", lambda f: f.breaks_prior_low),
            ("跌破核心支撑", lambda f: f.below_core_level),
            ("支撑变压力", lambda f: f.below_core_level),
            ("反抽失败", lambda f: f.fail_break_prior_high or f.upper_shadow),
        ],
        "volume": [
            ("放量下跌", lambda f: f.vol_expansion and f.down_day),
            ("次日无法修复", lambda f: f.down_day),
            ("收盘低于日内均价线", lambda f: f.close_below_vwap),
            ("收盘接近日内低点", lambda f: f.close_near_low),
        ],
        "index": [
            ("本地指数同步破位", lambda f: f.index_new_low),
            ("行业指数同步破位", lambda f: f.industry_weak),
            ("外部压力重新恶化", lambda f: f.index_weakening),
        ],
        "flow": [
            ("主动卖盘明显", lambda f: f.active_sell_up),
            ("资金净流出加速", lambda f: f.net_outflow_expanding),
            ("大单净流出扩大", lambda f: f.big_order_outflow),
        ],
    },
}

# 层 → 数据等级
LAYER_DATA_CLASS = {"price": "A", "volume": "A", "index": "A", "flow": "B"}


def _layer_available(layer: str, f: Features) -> bool:
    if layer in ("price", "volume"):
        return True
    if layer == "index":
        return f.has_index
    if layer == "flow":
        return f.has_flow
    return False


def evaluate_layers(state: State, f: Features) -> dict[str, LayerEvidence]:
    """评估某状态四层 checkbox，返回各层证据与得分"""
    result: dict[str, LayerEvidence] = {}
    for layer, checks in STATE_CHECKS[state].items():
        available = _layer_available(layer, f)
        data_class = LAYER_DATA_CLASS[layer]
        check_results: list[CheckResult] = []
        for name, pred in checks:
            triggered = bool(pred(f)) if available else False
            check_results.append(
                CheckResult(name=name, triggered=triggered, available=available, data_class=data_class)
            )
        triggered_count = sum(1 for c in check_results if c.triggered)
        score = (triggered_count / len(check_results) * 100) if available and check_results else 0.0
        result[layer] = LayerEvidence(
            layer=layer, checks=check_results, available=available, score=score
        )
    return result
