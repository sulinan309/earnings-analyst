"""Combo D1 · 市场错杀型（作确认器，不作核心买点）
Combo D2 · 内部人确认型（权重高于D1）

D1:
1. 南向资金连续5日净流入且加速
2. 机构持仓比例处于历史低位
3. 做空比率高位/分析师集体下调过度
4. 市场情绪极度悲观

D2:
1. 公司加速回购
2. 管理层增持
3. 特别分红
4. 资本配置动作与买入逻辑一致
"""

from .base import ComboSignal, SubConditionResult


class ComboD1(ComboSignal):
    COMBO_NAME = "Combo D1 · 市场错杀型"
    COMBO_TYPE = "买入"
    WEIGHT = "确认器"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 南向资金连续5日净流入且加速
        southbound_consecutive_days = data.get("southbound_net_inflow_days", 0)
        southbound_accelerating = data.get("southbound_accelerating", False)
        c1 = southbound_consecutive_days >= 5 and southbound_accelerating
        results.append(SubConditionResult(
            name="南向资金连续流入加速",
            triggered=c1,
            detail=f"连续净流入 {southbound_consecutive_days} 日，{'加速' if southbound_accelerating else '未加速'}",
            data_source="港交所数据",
        ))

        # 机构持仓处于历史低位
        inst_holding_percentile = data.get("institutional_holding_percentile", 50)
        c2 = inst_holding_percentile <= 20
        results.append(SubConditionResult(
            name="机构持仓历史低位",
            triggered=c2,
            detail=f"机构持仓历史分位 {inst_holding_percentile:.0f}%",
            data_source="持仓数据",
        ))

        # 做空比率高位
        short_ratio_high = data.get("short_ratio_high", False)
        analyst_downgrade_excessive = data.get("analyst_downgrade_excessive", False)
        c3 = short_ratio_high or analyst_downgrade_excessive
        results.append(SubConditionResult(
            name="做空/下调过度",
            triggered=c3,
            detail=f"做空高位={'是' if short_ratio_high else '否'}，分析师过度下调={'是' if analyst_downgrade_excessive else '否'}",
            data_source="市场数据",
        ))

        # 市场情绪极度悲观
        extreme_pessimism = data.get("extreme_pessimism", False)
        results.append(SubConditionResult(
            name="市场情绪极度悲观",
            triggered=extreme_pessimism,
            detail=data.get("sentiment_detail", "正常"),
            data_source="情绪指标",
        ))

        return results


class ComboD2(ComboSignal):
    COMBO_NAME = "Combo D2 · 内部人确认型"
    COMBO_TYPE = "买入"
    WEIGHT = "核心"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        results.append(SubConditionResult(
            name="公司加速回购",
            triggered=data.get("buyback_accelerating", False),
            detail=data.get("buyback_detail", "无回购"),
            data_source="港交所公告",
        ))

        results.append(SubConditionResult(
            name="管理层增持",
            triggered=data.get("management_buying", False),
            detail=data.get("management_buying_detail", "无增持"),
            data_source="港交所公告",
        ))

        results.append(SubConditionResult(
            name="特别分红",
            triggered=data.get("special_dividend", False),
            detail=data.get("special_dividend_detail", "无特别分红"),
            data_source="公司公告",
        ))

        results.append(SubConditionResult(
            name="资本配置与买入逻辑一致",
            triggered=data.get("capital_allocation_aligned", False),
            detail=data.get("capital_allocation_detail", "未评估"),
            data_source="综合判断",
        ))

        return results
