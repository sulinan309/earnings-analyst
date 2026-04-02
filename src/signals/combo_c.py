"""Combo C · 政策催化型（只作加分项，不单独触发重仓）

1. 监管表态明确转向友好（非模糊表述）
2. 行业竞争格局收缩（对手退出/合并）
3. 公司处于政策直接受益位置
4. 海外同类公司已先行验证逻辑
"""

from .base import ComboSignal, SubConditionResult


class ComboC(ComboSignal):
    COMBO_NAME = "Combo C · 政策催化型"
    COMBO_TYPE = "买入"
    WEIGHT = "加分项"

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        results.append(SubConditionResult(
            name="监管明确转向友好",
            triggered=data.get("regulatory_positive", False),
            detail=data.get("regulatory_detail", "无明确信号"),
            data_source="政策公告",
        ))

        results.append(SubConditionResult(
            name="行业竞争格局收缩",
            triggered=data.get("competition_consolidation", False),
            detail=data.get("competition_detail", "未观察到"),
            data_source="行业数据",
        ))

        results.append(SubConditionResult(
            name="公司处于政策直接受益位置",
            triggered=data.get("direct_policy_beneficiary", False),
            detail=data.get("policy_benefit_detail", "未确认"),
            data_source="政策分析",
        ))

        results.append(SubConditionResult(
            name="海外同类已验证逻辑",
            triggered=data.get("overseas_validated", False),
            detail=data.get("overseas_validation_detail", "无参考"),
            data_source="海外市场",
        ))

        return results
