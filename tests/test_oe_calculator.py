"""快手 (1024.HK) 模拟数据测试 OECalculator

参数参考 FY2024 财报：
- 市值 ~1600 亿港币
- CFO ~220 亿
- 维持性 Capex ~40 亿（从附注拆分）
- 净现金（保守口径）~350 亿
- r = 10%
"""

import pytest

from src.frameworks.oe_calculator import OECalculator, FinancialData, OEResult


# ── 快手 FY2024 模拟财务数据（参考真实量级）──
KUAISHOU_FY2024 = FinancialData(
    # OE 相关（亿港币）
    cfo=220.0,                      # 经营性现金流
    maintenance_capex=40.0,         # 维持性 Capex（服务器替换、带宽维护等）
    total_capex=95.0,               # 总 Capex（含可灵 GPU、海外扩张）

    # 净现金相关
    cash_and_equivalents=400.0,     # 现金及等价物
    short_term_investments=150.0,   # 短期理财
    interest_bearing_debt=50.0,     # 有息负债
    committed_investments=25.0,     # 已承诺投资款（可灵算力采购等）
    restricted_cash=10.0,           # 受限资金
    overseas_cash=50.0,             # 海外现金（印尼/巴西等）

    # 营收 & 市值
    revenue=1100.0,                 # 全年营收
    market_cap=1600.0,              # 当前市值 ~1600 亿

    period="FY2024",
    ticker="1024.HK",
)


class TestOECalculation:
    """Step 1: OE = CFO - 维持性 Capex"""

    def test_oe_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # OE = 220 - 40 = 180
        assert result.oe == 180.0

    def test_growth_capex(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 扩张性 Capex = 95 - 40 = 55
        assert result.growth_capex == 55.0

    def test_oe_margin(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # OE margin = 180 / 1100 * 100 ≈ 16.4%
        assert result.oe_margin_pct == 16.4


class TestNetCash:
    """Step 2: 保守口径净现金"""

    def test_gross_net_cash(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 毛净现金 = 400 + 150 - 50 = 500
        assert result.gross_net_cash == 500.0

    def test_operating_reserve(self):
        calc = OECalculator(discount_rate=0.10, reserve_months=1.5)
        result = calc.calculate(KUAISHOU_FY2024)
        # 月均营收 = 1100/12 ≈ 91.67, 运营储备 = 91.67 * 1.5 ≈ 137.5
        assert result.operating_reserve == 137.5

    def test_distributable_net_cash(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 扣除: 运营储备 137.5 + 已承诺 25 + 受限 10 + 海外折扣 50*0.15=7.5 = 180
        # 可分配 = 500 - 180 = 320
        assert result.total_deductions == 180.0
        assert result.distributable_net_cash == 320.0


class TestValuation:
    """Step 3 & 4: 零增长估值 + 安全边际"""

    def test_zero_growth_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 零增长估值 = 180 / 0.10 = 1800
        assert result.zero_growth_value == 1800.0

    def test_intrinsic_value(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 内在价值 = 1800 + 320 = 2120
        assert result.intrinsic_value == 2120.0

    def test_safety_margin_positive(self):
        """市值 1600 < 内在价值 2120，安全边际应转正"""
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 安全边际 = 2120 - 1600 = 520
        assert result.has_safety_margin is True
        assert result.safety_margin == 520.0

    def test_safety_margin_pct(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 安全边际% = 520 / 1600 * 100 = 32.5%
        assert result.safety_margin_pct == 32.5

    def test_odds(self):
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        # 赔率 = 520 / 1600 = 0.325
        assert result.odds == 0.325

    def test_odds_vs_threshold(self):
        """快手为中等质量资产，赔率阈值 70%，32.5% 未达标"""
        calc = OECalculator(discount_rate=0.10)
        result = calc.calculate(KUAISHOU_FY2024)
        kuaishou_threshold = 0.70  # 中等质量 > 70%
        assert result.odds < kuaishou_threshold


class TestSensitivity:
    """折现率敏感性分析：8%/10%/12%"""

    def test_three_scenarios(self):
        calc = OECalculator(discount_rate=0.10)
        results = calc.sensitivity(KUAISHOU_FY2024)
        assert len(results) == 3
        # r=8% 估值最高，r=12% 估值最低
        assert results[0].zero_growth_value > results[1].zero_growth_value
        assert results[1].zero_growth_value > results[2].zero_growth_value

    def test_sensitivity_values(self):
        calc = OECalculator(discount_rate=0.10)
        results = calc.sensitivity(KUAISHOU_FY2024)
        # r=8%:  180/0.08 = 2250,  内在 = 2250+320 = 2570, 边际 = +60.6%
        assert results[0].zero_growth_value == 2250.0
        assert results[0].has_safety_margin is True
        # r=10%: 180/0.10 = 1800,  内在 = 2120, 边际 = +32.5%
        assert results[1].zero_growth_value == 1800.0
        assert results[1].has_safety_margin is True
        # r=12%: 180/0.12 = 1500,  内在 = 1500+320 = 1820, 边际 = +13.8%
        assert results[2].zero_growth_value == 1500.0
        assert results[2].has_safety_margin is True

    def test_all_rates_show_safety_margin(self):
        """在 8%-12% 全范围内，快手 1600 亿市值均有安全边际"""
        calc = OECalculator(discount_rate=0.10)
        for result in calc.sensitivity(KUAISHOU_FY2024):
            assert result.has_safety_margin is True


class TestEdgeCases:
    """边界条件"""

    def test_discount_rate_out_of_range(self):
        with pytest.raises(ValueError, match="超出港股合理范围"):
            OECalculator(discount_rate=0.05)

    def test_discount_rate_boundary_low(self):
        calc = OECalculator(discount_rate=0.08)
        result = calc.calculate(KUAISHOU_FY2024)
        assert result.discount_rate == 0.08

    def test_discount_rate_boundary_high(self):
        calc = OECalculator(discount_rate=0.12)
        result = calc.calculate(KUAISHOU_FY2024)
        assert result.discount_rate == 0.12
