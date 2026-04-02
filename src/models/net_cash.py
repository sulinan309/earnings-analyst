"""净现金保守口径计算模块

净现金 = 现金及等价物 + 短期理财 - 有息负债
可分配净现金需进一步扣除：运营储备、已承诺投资款、受限资金、海外现金回流折扣
"""

from dataclasses import dataclass


@dataclass
class NetCashInput:
    """净现金计算所需数据（单位：亿港币）"""
    cash_and_equivalents: float       # 现金及等价物
    short_term_investments: float     # 短期理财
    interest_bearing_debt: float      # 有息负债
    monthly_revenue: float            # 月均营收（用于计算运营储备）
    committed_investments: float      # 已承诺投资款
    restricted_cash: float            # 受限资金
    overseas_cash: float              # 海外现金
    overseas_discount_rate: float = 0.15  # 海外现金回流折扣率
    reserve_months: float = 1.5       # 运营储备月数


@dataclass
class NetCashResult:
    """净现金计算结果"""
    gross_net_cash: float             # 毛净现金
    operating_reserve: float          # 运营储备
    committed_investments: float
    restricted_cash: float
    overseas_cash_discount: float     # 海外现金折扣金额
    distributable_net_cash: float     # 可分配净现金
    deductions_detail: dict           # 各项扣除明细


class NetCashCalculator:
    """保守口径净现金计算器"""

    def calculate(self, data: NetCashInput) -> NetCashResult:
        gross = data.cash_and_equivalents + data.short_term_investments - data.interest_bearing_debt

        operating_reserve = data.monthly_revenue * data.reserve_months
        overseas_discount = data.overseas_cash * data.overseas_discount_rate

        total_deductions = (
            operating_reserve
            + data.committed_investments
            + data.restricted_cash
            + overseas_discount
        )

        distributable = gross - total_deductions

        deductions_detail = {
            "运营储备": round(operating_reserve, 2),
            "已承诺投资款": round(data.committed_investments, 2),
            "受限资金": round(data.restricted_cash, 2),
            "海外现金回流折扣": round(overseas_discount, 2),
            "扣除合计": round(total_deductions, 2),
        }

        return NetCashResult(
            gross_net_cash=round(gross, 2),
            operating_reserve=round(operating_reserve, 2),
            committed_investments=data.committed_investments,
            restricted_cash=data.restricted_cash,
            overseas_cash_discount=round(overseas_discount, 2),
            distributable_net_cash=round(distributable, 2),
            deductions_detail=deductions_detail,
        )
