"""Combo F · 基本面恶化型（卖出信号）

1. OE连续2季下滑且核心业务指标同步恶化
2. FCF转负且非高回报扩张性投资
3. Capex扩张但看不到对应回报路径
4. 核心业务市场份额持续下滑
"""

from .base import ComboSignal, SubConditionResult


class ComboF(ComboSignal):
    COMBO_NAME = "Combo F · 基本面恶化型"
    COMBO_TYPE = "卖出"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 条件1: OE连续2季下滑+核心指标恶化
        quarterly_oes = data.get("quarterly_oes", [])
        core_metrics_deteriorating = data.get("core_metrics_deteriorating", False)
        oe_declining = (len(quarterly_oes) >= 3
                        and quarterly_oes[-1] < quarterly_oes[-2] < quarterly_oes[-3])
        c1 = oe_declining and core_metrics_deteriorating
        results.append(SubConditionResult(
            name="OE连续下滑+指标恶化",
            triggered=c1,
            detail=f"近3季OE: {[f'{oe:.1f}亿' for oe in quarterly_oes[-3:]]}，核心指标{'恶化' if core_metrics_deteriorating else '正常'}",
            data_source="财报",
        ))

        # 条件2: FCF转负且非高回报投资
        fcf = data.get("fcf", 0)
        high_return_expansion = data.get("high_return_expansion", False)
        c2 = fcf < 0 and not high_return_expansion
        results.append(SubConditionResult(
            name="FCF转负（非扩张投资）",
            triggered=c2,
            detail=f"FCF {fcf:.1f}亿，高回报扩张={'是' if high_return_expansion else '否'}",
            data_source="财报",
        ))

        # 条件3: Capex扩张无回报路径
        capex_expanding_no_return = data.get("capex_expanding_no_return", False)
        results.append(SubConditionResult(
            name="Capex扩张无回报路径",
            triggered=capex_expanding_no_return,
            detail=data.get("capex_return_detail", "未评估"),
            data_source="财报+管理层指引",
        ))

        # 条件4: 市场份额下滑
        market_share_declining = data.get("market_share_declining", False)
        results.append(SubConditionResult(
            name="核心业务市占率下滑",
            triggered=market_share_declining,
            detail=data.get("market_share_detail", "未获取数据"),
            data_source="行业数据",
        ))

        return results
