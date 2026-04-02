"""Combo H · 逻辑证伪型（最重要的卖出信号）

1. 当初买入的核心假设被财报数据否定
2. 竞争对手出现颠覆性打法且公司无有效应对
3. 管理层资本配置出现重大失误
4. 监管风险明确落地（非市场解读）

核心假设存储在 data/assumptions/[公司名].md
"""

import os
from .base import ComboSignal, SubConditionResult


ASSUMPTIONS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "assumptions"
)


class ComboH(ComboSignal):
    COMBO_NAME = "Combo H · 逻辑证伪型"
    COMBO_TYPE = "卖出"
    WEIGHT = "核心"

    def load_assumption(self, company_name: str) -> str | None:
        """从 data/assumptions/ 加载买入时的核心假设"""
        filepath = os.path.join(ASSUMPTIONS_DIR, f"{company_name}.md")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        return None

    def evaluate(self, data: dict) -> list[SubConditionResult]:
        results = []

        # 条件1: 核心假设被否定
        company_name = data.get("company_name", "")
        assumption = self.load_assumption(company_name)
        assumption_falsified = data.get("assumption_falsified", False)
        results.append(SubConditionResult(
            name="核心假设被财报否定",
            triggered=assumption_falsified,
            detail=f"原假设: {assumption or '未记录'}，{'已被否定' if assumption_falsified else '未被否定'}",
            data_source="财报 vs data/assumptions/",
        ))

        # 条件2: 竞争对手颠覆性打法
        results.append(SubConditionResult(
            name="竞对颠覆性打法",
            triggered=data.get("disruptive_competitor", False),
            detail=data.get("competitor_disruption_detail", "未观察到"),
            data_source="行业分析",
        ))

        # 条件3: 管理层资本配置重大失误
        results.append(SubConditionResult(
            name="管理层资本配置失误",
            triggered=data.get("capital_misallocation", False),
            detail=data.get("capital_misallocation_detail", "未观察到"),
            data_source="财报+公告",
        ))

        # 条件4: 监管风险落地
        results.append(SubConditionResult(
            name="监管风险明确落地",
            triggered=data.get("regulatory_risk_materialized", False),
            detail=data.get("regulatory_risk_detail", "无"),
            data_source="政策公告",
        ))

        return results
