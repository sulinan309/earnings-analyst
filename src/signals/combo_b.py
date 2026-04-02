"""Combo B · 基本面拐点型

1. 核心业务收入增速连续2季回升
2. 经营性现金流margin同比扩张 >3pct
3. 维持性资本支出占收入比下降（业务成熟信号）
4. 核心竞争力指标改善（非仅行业景气）
"""

from .base import ComboSignal, SubConditionResult


class ComboB(ComboSignal):
    COMBO_NAME = "Combo B · 基本面拐点型"
    COMBO_TYPE = "买入"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 条件1: 核心业务收入增速连续2季回升
        rev_growth_trend = data.get("revenue_growth_trend", [])
        c1 = (len(rev_growth_trend) >= 3
               and rev_growth_trend[-1] > rev_growth_trend[-2] > rev_growth_trend[-3])
        results.append(SubConditionResult(
            name="收入增速连续2季回升",
            triggered=c1,
            detail=f"近3季增速: {[f'{g:.1f}%' for g in rev_growth_trend[-3:]]}",
            data_source="财报",
        ))

        # 条件2: CFO margin 同比扩张 >3pct
        cfo_margin_yoy_change = data.get("cfo_margin_yoy_change", 0)
        c2 = cfo_margin_yoy_change > 3.0
        results.append(SubConditionResult(
            name="CFO margin同比扩张>3pct",
            triggered=c2,
            detail=f"CFO margin同比变化 {cfo_margin_yoy_change:+.1f}pct",
            data_source="财报",
        ))

        # 条件3: 维持性资本支出占收入比下降
        maint_capex_ratio_trend = data.get("maint_capex_ratio_trend", [])
        c3 = (len(maint_capex_ratio_trend) >= 2
               and maint_capex_ratio_trend[-1] < maint_capex_ratio_trend[-2])
        results.append(SubConditionResult(
            name="维持性Capex占比下降",
            triggered=c3,
            detail=f"近期占比趋势: {[f'{r:.1f}%' for r in maint_capex_ratio_trend[-2:]]}",
            data_source="财报附注",
        ))

        # 条件4: 核心竞争力指标改善
        core_metric_improved = data.get("core_metric_improved", False)
        core_metric_detail = data.get("core_metric_detail", "未提供")
        results.append(SubConditionResult(
            name="核心竞争力指标改善",
            triggered=core_metric_improved,
            detail=core_metric_detail,
            data_source="财报+行业数据",
        ))

        return results
