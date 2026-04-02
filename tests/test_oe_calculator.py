"""快手 (1024.HK) 模拟数据测试 OECalculator

模拟场景：快手 2025 年全年财报
- 电商 GMV 变现率提升，CFO 强劲
- 可灵商业化初期，维持性 Capex 可控
- 海外投入导致部分扩张性 Capex
"""

import pytest

from src.frameworks.oe_calculator import OECalculator, FinancialData, OEResult


# ── 快手模拟财务数据 ──
KUAISHOU_2025 = FinancialData(
    # OE 相关（亿港币）
    cfo=220.0,                      # 经营性现金流
    maintenance_capex=45.0,         # 维持性 Capex（服务器折旧替换等，从附注拆分）
    total_capex=110.0,              # 总 Capex（含可灵 GPU、海外扩张）

    # 净现金相关
    cash_and_equivalents=350.0,     # 现金及等价物
    short_term_investments=180.0,   # 短期理财
    interest_bearing_debt=50.0,     # 有息负债
    committed_investments=30.0,     # 已承诺投资款（可灵算力采购等）
    restricted_cash=15.0,           # 受限资金
    overseas_cash=60.0,             # 海外现金（印尼/巴西等）

    # 营收 & 市值
    revenue=1200.0,                 # 全年营收
    market_cap=3500.0,              # 当前市值

    period="2025FY",
    ticker="1024.HK",
)


class TestOECalculation:
    """Step 1: OE = CFO - 维持性 Capex"""

    def test_oe_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # OE = 220 - 45 = 175
        assert result.oe == 175.0

    def test_growth_capex(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 扩张性 Capex = 110 - 45 = 65
        assert result.growth_capex == 65.0

    def test_oe_margin(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # OE margin = 175 / 1200 * 100 ≈ 14.6%
        assert result.oe_margin_pct == 14.6


class TestNetCash:
    """Step 2: 保守口径净现金"""

    def test_gross_net_cash(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 毛净现金 = 350 + 180 - 50 = 480
        assert result.gross_net_cash == 480.0

    def test_operating_reserve(self):
        calc = OECalculator(discount_rate=0.10, reserve_months=1.5)
        result = calc.calculate(KUAISHOU_2025)
        # 月均营收 = 1200/12 = 100, 运营储备 = 100 * 1.5 = 150
        assert result.operating_reserve == 150.0

    def test_distributable_net_cash(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 扣除: 运营储备 150 + 已承诺 30 + 受限 15 + 海外折扣 60*0.15=9 = 204
        # 可分配 = 480 - 204 = 276
        assert result.total_deductions == 204.0
        assert result.distributable_net_cash == 276.0


class TestValuation:
    """Step 3 & 4: 零增长估值 + 安全边际"""

    def test_zero_growth_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 零增长估值 = 175 / 0.10 = 1750
        assert result.zero_growth_value == 1750.0

    def test_intrinsic_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 内在价值 = 1750 + 276 = 2026
        assert result.intrinsic_value == 2026.0

    def test_safety_margin_negative(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 安全边际 = 2026 - 3500 = -1474，不存在安全边际
        assert result.has_safety_margin is False
        assert result.safety_margin == -1474.0

    def test_safety_margin_pct(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 安全边际% = -1474 / 3500 * 100 ≈ -42.1%
        assert result.safety_margin_pct == -42.1

    def test_odds(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_2025)
        # 赔率 = -1474 / 3500 ≈ -0.4211
        assert result.odds == -0.4211

    def test_lower_market_cap_has_safety_margin(self):
        """市值足够低时应存在安全边际"""
        cheap_kuaishou = FinancialData(
            cfo=220.0, maintenance_capex=45.0, total_capex=110.0,
            cash_and_equivalents=350.0, short_term_investments=180.0,
            interest_bearing_debt=50.0, committed_investments=30.0,
            restricted_cash=15.0, overseas_cash=60.0,
            revenue=1200.0,
            market_cap=1800.0,  # 市值低于内在价值 2026
            period="2025FY", ticker="1024.HK",
        )
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(cheap_kuaishou)
        assert result.has_safety_margin is True
        assert result.odds > 0


class TestSensitivity:
    """折现率敏感性分析"""

    def test_three_scenarios(self):
        calc = OECalculator(discount_rate=0.10)
        results = calc.sensitivity(KUAISHOU_2025)
        assert len(results) == 3
        # r=8% 估值最高，r=12% 估值最低
        assert results[0].zero_growth_value > results[1].zero_growth_value
        assert results[1].zero_growth_value > results[2].zero_growth_value

    def test_sensitivity_values(self):
        calc = OECalculator(discount_rate=0.10)
        results = calc.sensitivity(KUAISHOU_2025)
        # r=8%: 175/0.08 = 2187.5
        assert results[0].zero_growth_value == 2187.5
        # r=10%: 175/0.10 = 1750
        assert results[1].zero_growth_value == 1750.0
        # r=12%: 175/0.12 ≈ 1458.33
        assert results[2].zero_growth_value == 1458.33


class TestEdgeCases:
    """边界条件"""

    def test_discount_rate_out_of_range(self):
        with pytest.raises(ValueError, match="超出港股合理范围"):
            OECalculator(discount_rate=0.05)

    def test_discount_rate_boundary_low(self):
        calc = OECalculator(discount_rate=0.08)
        result = calc.calculate(KUAISHOU_2025)
        assert result.discount_rate == 0.08

    def test_discount_rate_boundary_high(self):
        calc = OECalculator(discount_rate=0.12)
        result = calc.calculate(KUAISHOU_2025)
        assert result.discount_rate == 0.12
