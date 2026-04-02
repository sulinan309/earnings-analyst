"""Combo E · 估值透支型（卖出信号）

1. 市值 > 乐观OE估值 + 净现金
2. 赔率<20%停止加仓，赔率<10%且无催化则减仓
3. 市值/OE > 历史均值130%
4. 分析师一致预期上调空间 <10%
"""

from .base import ComboSignal, SubConditionResult


class ComboE(ComboSignal):
    COMBO_NAME = "Combo E · 估值透支型"
    COMBO_TYPE = "卖出"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 条件1: 市值 > 乐观OE估值 + 净现金
        market_cap = data.get("market_cap", 0)
        optimistic_value = data.get("optimistic_intrinsic_value", 0)
        c1 = market_cap > optimistic_value if optimistic_value > 0 else False
        results.append(SubConditionResult(
            name="市值超乐观估值",
            triggered=c1,
            detail=f"市值 {market_cap:.1f}亿 vs 乐观估值 {optimistic_value:.1f}亿",
            data_source="估值模型",
        ))

        # 条件2: 赔率过低
        odds = data.get("odds", 0)
        has_catalyst = data.get("has_catalyst", False)
        c2 = odds < 0.10 and not has_catalyst
        results.append(SubConditionResult(
            name="赔率过低需减仓",
            triggered=c2,
            detail=f"赔率 {odds:.1%}，催化剂={'有' if has_catalyst else '无'}",
            data_source="估值模型",
        ))

        # 条件3: 市值/OE > 历史均值130%
        oe_multiple_vs_avg = data.get("oe_multiple_vs_historical_avg", 1.0)
        c3 = oe_multiple_vs_avg > 1.30
        results.append(SubConditionResult(
            name="估值倍数偏高",
            triggered=c3,
            detail=f"市值/OE 为历史均值的 {oe_multiple_vs_avg:.0%}",
            data_source="历史数据",
        ))

        # 条件4: 分析师上调空间 <10%
        analyst_upside = data.get("analyst_consensus_upside", 0)
        c4 = analyst_upside < 10.0
        results.append(SubConditionResult(
            name="分析师上调空间不足",
            triggered=c4,
            detail=f"一致预期上调空间 {analyst_upside:.1f}%",
            data_source="分析师数据",
        ))

        return results
