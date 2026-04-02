"""Combo J · 时间成本型（卖出信号）

1. 核心逻辑未证伪但2-3个季度未兑现
2. 管理层持续讲故事，兑现度低
3. 资金占用过久，替代机会更优
4. 市场不给估值的关键原因仍未改变
"""

from .base import ComboSignal, SubConditionResult


class ComboJ(ComboSignal):
    COMBO_NAME = "Combo J · 时间成本型"
    COMBO_TYPE = "卖出"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        quarters_without_delivery = data.get("quarters_without_delivery", 0)
        c1 = quarters_without_delivery >= 2
        results.append(SubConditionResult(
            name="逻辑2-3季未兑现",
            triggered=c1,
            detail=f"已持有 {quarters_without_delivery} 个季度未兑现核心逻辑",
            data_source="持仓记录",
        ))

        results.append(SubConditionResult(
            name="管理层兑现度低",
            triggered=data.get("management_low_delivery", False),
            detail=data.get("management_delivery_detail", "未评估"),
            data_source="业绩会纪要",
        ))

        results.append(SubConditionResult(
            name="替代机会更优",
            triggered=data.get("better_alternative_exists", False),
            detail=data.get("alternative_detail", "未评估"),
            data_source="组合分析",
        ))

        results.append(SubConditionResult(
            name="估值压制因素未改变",
            triggered=data.get("valuation_overhang_unchanged", False),
            detail=data.get("valuation_overhang_detail", "未评估"),
            data_source="市场分析",
        ))

        return results
