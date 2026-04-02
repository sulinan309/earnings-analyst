"""Owner's Earnings 计算模块

李录框架核心：
OE = 经营性现金流 (CFO) - 维持性资本支出
注意：维持性资本支出需从财报附注拆分，不可直接用总CapEx。
"""

from dataclasses import dataclass


@dataclass
class OwnerEarningsInput:
    """OE 计算所需的财务数据（单位：亿港币）"""
    cfo: float                    # 经营性现金流
    maintenance_capex: float      # 维持性资本支出（从附注拆分）
    total_capex: float            # 总资本支出（仅供参考）
    period: str                   # 财报期间，如 "2025H2", "2025FY"
    is_annualized: bool = False   # 是否已年化


@dataclass
class OwnerEarningsResult:
    """OE 计算结果"""
    oe: float                     # Owner's Earnings
    cfo: float
    maintenance_capex: float
    growth_capex: float           # 扩张性资本支出 = total - maintenance
    oe_margin: float | None       # OE/营收（需外部传入营收）
    period: str


class OwnerEarningsCalculator:
    """计算 Owner's Earnings

    禁止使用多阶段 DCF，仅计算单期 OE 用于零增长估值。
    """

    def calculate(self, data: OwnerEarningsInput, revenue: float | None = None) -> OwnerEarningsResult:
        """计算 OE = CFO - 维持性资本支出"""
        oe = data.cfo - data.maintenance_capex
        growth_capex = data.total_capex - data.maintenance_capex
        oe_margin = (oe / revenue * 100) if revenue and revenue > 0 else None

        return OwnerEarningsResult(
            oe=round(oe, 2),
            cfo=data.cfo,
            maintenance_capex=data.maintenance_capex,
            growth_capex=round(growth_capex, 2),
            oe_margin=round(oe_margin, 1) if oe_margin is not None else None,
            period=data.period,
        )

    def is_stable(self, quarterly_oes: list[float], threshold: float = 0.3) -> bool:
        """判断过去12个月OE是否稳定（非一次性）

        Args:
            quarterly_oes: 最近4个季度的OE列表
            threshold: 波动率阈值，超过则判定不稳定
        """
        if not quarterly_oes or len(quarterly_oes) < 2:
            return False
        if any(oe <= 0 for oe in quarterly_oes):
            return False
        avg = sum(quarterly_oes) / len(quarterly_oes)
        if avg <= 0:
            return False
        max_deviation = max(abs(oe - avg) / avg for oe in quarterly_oes)
        return max_deviation <= threshold
