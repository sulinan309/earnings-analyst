"""Combo G · 筹码恶化型（只作减仓辅助信号，不单独构成卖出理由）

1. 南向资金连续净流出 >10个交易日
2. 大股东/管理层非计划性减持
3. 放量滞涨
4. 外资持仓比例快速下降
"""

from .base import ComboSignal, SubConditionResult


class ComboG(ComboSignal):
    COMBO_NAME = "Combo G · 筹码恶化型"
    COMBO_TYPE = "卖出"
    WEIGHT = "辅助"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        southbound_outflow_days = data.get("southbound_net_outflow_days", 0)
        c1 = southbound_outflow_days > 10
        results.append(SubConditionResult(
            name="南向连续净流出>10日",
            triggered=c1,
            detail=f"连续净流出 {southbound_outflow_days} 个交易日",
            data_source="港交所数据",
        ))

        results.append(SubConditionResult(
            name="大股东/管理层非计划减持",
            triggered=data.get("insider_unplanned_selling", False),
            detail=data.get("insider_selling_detail", "未观察到"),
            data_source="港交所公告",
        ))

        results.append(SubConditionResult(
            name="放量滞涨",
            triggered=data.get("high_volume_stagnation", False),
            detail=data.get("volume_price_detail", "正常"),
            data_source="市场数据",
        ))

        foreign_holding_drop = data.get("foreign_holding_rapid_decline", False)
        results.append(SubConditionResult(
            name="外资持仓快速下降",
            triggered=foreign_holding_drop,
            detail=data.get("foreign_holding_detail", "稳定"),
            data_source="持仓数据",
        ))

        return results
