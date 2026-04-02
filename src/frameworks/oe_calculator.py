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

    def scenario_analysis(self, data: FinancialData) -> list["ScenarioResult"]:
        """三情景估值分析

        保守: r=12%, 零增长, 维持性Capex上浮20%, 保守净现金
        中性: r=10%, 零增长, 当前OE, 保守净现金
        乐观: r=8%, 温和增长g=5%, 维持性Capex下浮10%, 净现金完整口径
        """
        scenarios = []

        # ── 保守情景 ──
        conservative_data = FinancialData(
            cfo=data.cfo,
            maintenance_capex=data.maintenance_capex * 1.20,  # 上浮20%
            total_capex=data.total_capex,
            cash_and_equivalents=data.cash_and_equivalents,
            short_term_investments=data.short_term_investments,
            interest_bearing_debt=data.interest_bearing_debt,
            committed_investments=data.committed_investments,
            restricted_cash=data.restricted_cash,
            overseas_cash=data.overseas_cash,
            revenue=data.revenue,
            market_cap=data.market_cap,
            listed_investments_fv=data.listed_investments_fv,
            unlisted_investments_bv=data.unlisted_investments_bv,
            investment_discount=0.70,  # 投资组合打7折（更保守）
            period=data.period,
            ticker=data.ticker,
        )
        conservative_calc = OECalculator(
            discount_rate=0.12,
            reserve_months=2.0,  # 2个月运营储备（更保守）
            overseas_discount_rate=0.25,  # 海外现金折扣更高
        )
        c_result = conservative_calc.calculate(conservative_data)
        scenarios.append(ScenarioResult(
            name="保守",
            label="最坏情况下值多少",
            params="r=12%, 零增长, 维持性Capex×1.2, 运营储备2月, 投资组合70%折扣",
            oe=c_result,
        ))

        # ── 中性情景 ──
        n_result = OECalculator(discount_rate=0.10).calculate(data)
        scenarios.append(ScenarioResult(
            name="中性",
            label="合理估值",
            params="r=10%, 零增长, 当前OE, 保守净现金, 投资组合50%折扣",
            oe=n_result,
        ))

        # ── 乐观情景 ──
        optimistic_data = FinancialData(
            cfo=data.cfo,
            maintenance_capex=data.maintenance_capex * 0.90,  # 下浮10%
            total_capex=data.total_capex,
            cash_and_equivalents=data.cash_and_equivalents,
            short_term_investments=data.short_term_investments,
            interest_bearing_debt=data.interest_bearing_debt,
            committed_investments=0.0,  # 完整口径不扣
            restricted_cash=0.0,
            overseas_cash=0.0,  # 不扣海外折扣
            revenue=data.revenue,
            market_cap=data.market_cap,
            listed_investments_fv=data.listed_investments_fv,
            unlisted_investments_bv=data.unlisted_investments_bv,
            investment_discount=0.30,  # 投资组合仅打3折
            period=data.period,
            ticker=data.ticker,
        )
        optimistic_calc = OECalculator(
            discount_rate=0.08,
            reserve_months=1.0,  # 1个月运营储备
            overseas_discount_rate=0.0,
        )
        o_base = optimistic_calc.calculate(optimistic_data)
        # 叠加温和增长 g=5%: 估值 = OE / (r - g) = OE / 3%
        growth_rate = 0.05
        effective_rate = 0.08 - growth_rate  # 3%
        growth_value = o_base.oe / effective_rate
        growth_intrinsic = growth_value + o_base.distributable_net_cash + o_base.investment_portfolio_value
        growth_margin = growth_intrinsic - data.market_cap
        growth_margin_pct = round(growth_margin / data.market_cap * 100, 1)

        scenarios.append(ScenarioResult(
            name="乐观",
            label="业务持续改善时值多少",
            params="r=8%, g=5%, 维持性Capex×0.9, 完整净现金, 投资组合30%折扣",
            oe=o_base,
            override_value=round(growth_value, 2),
            override_intrinsic=round(growth_intrinsic, 2),
            override_margin=round(growth_margin, 2),
            override_margin_pct=growth_margin_pct,
            override_odds=round(growth_margin / data.market_cap, 4),
            growth_rate=growth_rate,
        ))

        return scenarios


@dataclass
class ScenarioResult:
    """单个情景的估值结果"""
    name: str           # "保守" / "中性" / "乐观"
    label: str          # 情景含义
    params: str         # 参数描述
    oe: OEResult        # 基础计算结果

    # 乐观情景叠加增长后的覆盖值（可选）
    override_value: float | None = None       # 增长估值
    override_intrinsic: float | None = None   # 含增长内在价值
    override_margin: float | None = None
    override_margin_pct: float | None = None
    override_odds: float | None = None
    growth_rate: float = 0.0

    @property
    def intrinsic_value(self) -> float:
        return self.override_intrinsic if self.override_intrinsic is not None else self.oe.intrinsic_value

    @property
    def safety_margin_pct(self) -> float:
        return self.override_margin_pct if self.override_margin_pct is not None else self.oe.safety_margin_pct

    @property
    def odds(self) -> float:
        return self.override_odds if self.override_odds is not None else self.oe.odds
