"""Combo A · 估值安全边际型（买入底盘）

大多数买入先过 A：
1. 市值 < 零增长OE估值 + 可分配净现金
2. 赔率达标（顶级资产>40%、中等质量>70%、高波动>100%）
3. 过去12个月OE为正且稳定（非一次性）
4. 市值/OE处于历史低分位，且当前增长质量无结构性恶化
"""

from .base import ComboSignal, SubConditionResult


class ComboA(ComboSignal):
    COMBO_NAME = "Combo A · 估值安全边际型"
    COMBO_TYPE = "买入"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 条件1: 市值 < 零增长OE估值 + 可分配净现金
        market_cap = data.get("market_cap", 0)
        intrinsic_value = data.get("intrinsic_value", 0)
        c1 = market_cap < intrinsic_value if market_cap > 0 else False
        results.append(SubConditionResult(
            name="市值 < 内在价值",
            triggered=c1,
            detail=f"市值 {market_cap:.1f}亿 vs 内在价值 {intrinsic_value:.1f}亿",
            data_source="财报+市场数据",
        ))

        # 条件2: 赔率达标
        odds = data.get("odds", 0)
        odds_threshold = data.get("odds_threshold", 0.40)
        c2 = odds >= odds_threshold
        results.append(SubConditionResult(
            name="赔率达标",
            triggered=c2,
            detail=f"赔率 {odds:.1%}，阈值 {odds_threshold:.0%}",
            data_source="估值模型",
        ))

        # 条件3: 过去12个月OE为正且稳定
        oe_stable = data.get("oe_stable", False)
        ttm_oe = data.get("ttm_oe", 0)
        c3 = oe_stable and ttm_oe > 0
        results.append(SubConditionResult(
            name="OE正且稳定",
            triggered=c3,
            detail=f"TTM OE {ttm_oe:.1f}亿，稳定性={'通过' if oe_stable else '未通过'}",
            data_source="财报",
        ))

        # 条件4: 市值/OE处于历史低分位
        oe_multiple_percentile = data.get("oe_multiple_percentile", 100)
        structural_deterioration = data.get("structural_deterioration", False)
        c4 = oe_multiple_percentile <= 30 and not structural_deterioration
        results.append(SubConditionResult(
            name="估值历史低分位",
            triggered=c4,
            detail=f"市值/OE历史分位 {oe_multiple_percentile:.0f}%，结构性恶化={'是' if structural_deterioration else '否'}",
            data_source="历史数据",
        ))

        return results
