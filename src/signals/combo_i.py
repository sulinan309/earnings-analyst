"""Combo I · 组合再平衡型（卖出信号）

1. 单一标的仓位超过组合上限
2. 单一行业暴露过高
3. 该标的上涨后挤占更高赔率标的仓位
4. 风险收益比明显低于备选标的
"""

from .base import ComboSignal, SubConditionResult


class ComboI(ComboSignal):
    COMBO_NAME = "Combo I · 组合再平衡型"
    COMBO_TYPE = "卖出"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        position_pct = data.get("position_pct", 0)
        position_limit = data.get("position_limit", 25)
        c1 = position_pct > position_limit
        results.append(SubConditionResult(
            name="单一标的超仓位上限",
            triggered=c1,
            detail=f"仓位 {position_pct:.1f}%，上限 {position_limit:.0f}%",
            data_source="组合数据",
        ))

        sector_exposure = data.get("sector_exposure_pct", 0)
        sector_limit = data.get("sector_limit", 40)
        c2 = sector_exposure > sector_limit
        results.append(SubConditionResult(
            name="单一行业暴露过高",
            triggered=c2,
            detail=f"行业暴露 {sector_exposure:.1f}%，上限 {sector_limit:.0f}%",
            data_source="组合数据",
        ))

        results.append(SubConditionResult(
            name="挤占更高赔率标的仓位",
            triggered=data.get("crowding_better_opportunity", False),
            detail=data.get("crowding_detail", "未评估"),
            data_source="组合分析",
        ))

        results.append(SubConditionResult(
            name="风险收益比低于备选",
            triggered=data.get("inferior_risk_reward", False),
            detail=data.get("risk_reward_comparison_detail", "未评估"),
            data_source="组合分析",
        ))

        return results
