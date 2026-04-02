"""Owner's Earnings 端到端计算器

李录框架核心流程：
1. OE = CFO - 维持性资本支出（从附注拆分，禁止直接用总CapEx）
2. 净现金 = 现金及等价物 + 短期理财 - 有息负债，再扣除运营储备/已承诺投资/受限资金/海外折扣
3. 零增长估值 = OE / r（r: 8%-12%）
4. 安全边际 = 零增长估值 + 可分配净现金 - 市值
5. 禁止多阶段 DCF
"""

from dataclasses import dataclass


@dataclass
class FinancialData:
    """单期财务数据输入（单位：亿港币）"""

    # ── OE 相关 ──
    cfo: float                          # 经营性现金流
    maintenance_capex: float            # 维持性资本支出（须从附注拆分）
    total_capex: float                  # 总资本支出（仅供参考，不参与 OE 计算）

    # ── 净现金相关 ──
    cash_and_equivalents: float         # 现金及等价物
    short_term_investments: float       # 短期理财
    interest_bearing_debt: float        # 有息负债
    committed_investments: float        # 已承诺投资款
    restricted_cash: float              # 受限资金
    overseas_cash: float                # 海外现金

    # ── 营收 & 市值 ──
    revenue: float                      # 营业收入
    market_cap: float                   # 当前市值

    # ── 投资组合（可选）──
    listed_investments_fv: float = 0.0  # 上市投资公司权益公允价值
    unlisted_investments_bv: float = 0.0  # 非上市投资公司权益账面价值
    investment_discount: float = 0.5    # 投资组合保守折扣率（默认50%）

    # ── 元数据 ──
    period: str = ""                    # 财报期间，如 "2025FY"
    ticker: str = ""                    # 股票代码
    maintenance_capex_is_estimated: bool = False  # 维持性Capex是否为估算值
    maintenance_capex_note: str = ""    # 维持性Capex估算说明


@dataclass
class OEResult:
    """Owner's Earnings 全框架计算结果"""

    # ── Step 1: OE ──
    oe: float                           # Owner's Earnings
    cfo: float
    maintenance_capex: float
    growth_capex: float                 # 扩张性 Capex = total - maintenance
    oe_margin_pct: float | None         # OE / 营收 (%)
    maintenance_capex_is_estimated: bool = False
    maintenance_capex_note: str = ""

    # ── Step 2: 净现金 ──
    gross_net_cash: float = 0.0         # 毛净现金
    operating_reserve: float = 0.0      # 运营储备扣除额
    total_deductions: float = 0.0       # 总扣除额
    distributable_net_cash: float = 0.0 # 可分配净现金

    # ── Step 2b: 投资组合 ──
    investment_portfolio_value: float = 0.0  # 折扣后的投资组合价值
    investment_portfolio_gross: float = 0.0  # 折扣前的投资组合总值
    investment_discount_rate: float = 0.5    # 使用的折扣率

    # ── Step 3: 零增长估值 ──
    discount_rate: float = 0.0
    zero_growth_value: float = 0.0      # OE / r
    intrinsic_value: float = 0.0        # 零增长估值 + 可分配净现金 + 投资组合

    # ── Step 4: 安全边际 ──
    market_cap: float = 0.0
    safety_margin: float = 0.0          # 内在价值 - 市值
    safety_margin_pct: float = 0.0      # 安全边际 / 市值 (%)
    has_safety_margin: bool = False
    odds: float = 0.0                   # (内在价值 - 市值) / 市值

    period: str = ""


class OECalculator:
    """Owner's Earnings 端到端计算器

    参数:
        discount_rate: 折现率，必须在 8%-12% 范围内（港股）
        reserve_months: 运营储备月数，默认 1.5（即 1-2 个月取中值）
        overseas_discount_rate: 海外现金回流折扣率
    """

    def __init__(
        self,
        discount_rate: float = 0.10,
        reserve_months: float = 1.5,
        overseas_discount_rate: float = 0.15,
    ):
        if not 0.08 <= discount_rate <= 0.12:
            raise ValueError(
                f"折现率 {discount_rate:.1%} 超出港股合理范围 8%-12%"
            )
        self.discount_rate = discount_rate
        self.reserve_months = reserve_months
        self.overseas_discount_rate = overseas_discount_rate

    def calculate(self, data: FinancialData) -> OEResult:
        """执行完整的 OE 框架计算

        流程：OE → 净现金 → 零增长估值 → 安全边际
        """
        # ── Step 1: Owner's Earnings ──
        oe = data.cfo - data.maintenance_capex
        growth_capex = data.total_capex - data.maintenance_capex
        oe_margin_pct = (
            round(oe / data.revenue * 100, 1)
            if data.revenue > 0
            else None
        )

        # ── Step 2: 保守口径净现金 ──
        gross_net_cash = (
            data.cash_and_equivalents
            + data.short_term_investments
            - data.interest_bearing_debt
        )

        monthly_revenue = data.revenue / 12
        operating_reserve = monthly_revenue * self.reserve_months
        overseas_discount = data.overseas_cash * self.overseas_discount_rate

        total_deductions = (
            operating_reserve
            + data.committed_investments
            + data.restricted_cash
            + overseas_discount
        )

        distributable_net_cash = gross_net_cash - total_deductions

        # ── Step 2b: 投资组合保守估值 ──
        investment_gross = data.listed_investments_fv + data.unlisted_investments_bv
        investment_portfolio_value = investment_gross * (1 - data.investment_discount)

        # ── Step 3: 零增长估值（禁止多阶段 DCF）──
        zero_growth_value = oe / self.discount_rate
        intrinsic_value = zero_growth_value + distributable_net_cash + investment_portfolio_value

        # ── Step 4: 安全边际判断 ──
        safety_margin = intrinsic_value - data.market_cap
        safety_margin_pct = safety_margin / data.market_cap * 100
        odds = safety_margin / data.market_cap

        return OEResult(
            oe=round(oe, 2),
            cfo=data.cfo,
            maintenance_capex=data.maintenance_capex,
            growth_capex=round(growth_capex, 2),
            oe_margin_pct=oe_margin_pct,
            maintenance_capex_is_estimated=data.maintenance_capex_is_estimated,
            maintenance_capex_note=data.maintenance_capex_note,
            gross_net_cash=round(gross_net_cash, 2),
            operating_reserve=round(operating_reserve, 2),
            total_deductions=round(total_deductions, 2),
            distributable_net_cash=round(distributable_net_cash, 2),
            investment_portfolio_value=round(investment_portfolio_value, 2),
            investment_portfolio_gross=round(investment_gross, 2),
            investment_discount_rate=data.investment_discount,
            discount_rate=self.discount_rate,
            zero_growth_value=round(zero_growth_value, 2),
            intrinsic_value=round(intrinsic_value, 2),
            market_cap=data.market_cap,
            safety_margin=round(safety_margin, 2),
            safety_margin_pct=round(safety_margin_pct, 1),
            has_safety_margin=safety_margin > 0,
            odds=round(odds, 4),
            period=data.period,
        )

    def sensitivity(
        self, data: FinancialData, rates: list[float] | None = None
    ) -> list[OEResult]:
        """折现率敏感性分析，默认测试 8%/10%/12% 三档"""
        rates = rates or [0.08, 0.10, 0.12]
        results = []
        for r in rates:
            calc = OECalculator(
                discount_rate=r,
                reserve_months=self.reserve_months,
                overseas_discount_rate=self.overseas_discount_rate,
            )
            results.append(calc.calculate(data))
        return results
