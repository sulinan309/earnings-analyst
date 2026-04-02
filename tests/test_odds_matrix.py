"""赔率/胜率决策矩阵测试

快手 FY2024 场景：
- Combo A: 3/4 触发（条件2赔率未达标）
- 赔率: 32.5%（中等质量阈值 70%）
- 预期: 胜率3(中) + 赔率2(低) → 不参与
"""

import pytest

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput, ComboScanResult
from src.frameworks.odds_matrix import OddsMatrix, MatrixResult


KUAISHOU_FY2024 = FinancialData(
    cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
    cash_and_equivalents=400.0, short_term_investments=150.0,
    interest_bearing_debt=50.0, committed_investments=25.0,
    restricted_cash=10.0, overseas_cash=50.0,
    revenue=1100.0, market_cap=1600.0,
    period="FY2024", ticker="1024.HK",
)

KUAISHOU_EXTRA = ComboAInput(
    asset_tier="中等质量",
    quarterly_oes=[42.0, 46.0, 44.0, 48.0],
    oe_multiple_percentile=25.0,
    structural_deterioration=False,
)


@pytest.fixture
def kuaishou_combo_a():
    oe = OECalculator(discount_rate=0.10).calculate(KUAISHOU_FY2024)
    return ComboScanner().scan_combo_a(oe, KUAISHOU_EXTRA), oe


@pytest.fixture
def matrix():
    return OddsMatrix()


# ── 快手基准场景：胜率中 + 赔率低 → 不参与 ──

class TestKuaishouBaseline:
    """快手 FY2024: Combo A 3/4, 赔率 32.5%, 中等质量"""

    def test_win_rate_score(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        # Combo A 3/4 无其他 Combo → 胜率 3
        assert result.win_rate_score == 3
        assert result.win_rate_level == "中"

    def test_odds_score(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        # 赔率 32.5%，中等质量阈值 70%，半程 35%，32.5% < 35% → 赔率 2
        assert result.odds_score == 2
        assert result.odds_level == "低"

    def test_action_no_participate(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        assert result.action == "不参与"
        assert result.position_range == "0%"

    def test_reasoning_mentions_gap(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        assert "赔率" in result.reasoning
        assert "70%" in result.reasoning

    def test_summary_output(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        text = result.summary()
        assert "3/5" in text
        assert "2/5" in text
        assert "不参与" in text


# ── Combo A 3/4 + Combo B 触发 → 胜率升至 4(高) ──

class TestWithExtraCombos:
    """额外 Combo 触发可提升胜率"""

    def _mock_combo_b(self) -> ComboScanResult:
        """模拟已触发的 Combo B"""
        return ComboScanResult(
            combo_name="Combo B · 基本面拐点型",
            sub_conditions=[], triggered_count=3, total_count=4,
            triggered=True, missing=[],
        )

    def test_win_rate_boosted(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(
            combo_a, oe.odds, "中等质量",
            extra_buy_combos=[self._mock_combo_b()],
        )
        # 3/4 + Combo B → 胜率 4(高)
        assert result.win_rate_score == 4
        assert result.win_rate_level == "高"

    def test_high_win_low_odds_still_no(self, kuaishou_combo_a, matrix):
        combo_a, oe = kuaishou_combo_a
        result = matrix.evaluate(
            combo_a, oe.odds, "中等质量",
            extra_buy_combos=[self._mock_combo_b()],
        )
        # 高胜率 + 低赔率 → 不参与
        assert result.action == "不参与"


# ── 市值更低场景：赔率达标 ──

class TestCheaperKuaishou:
    """如果市值足够低，赔率达标可以改变决策"""

    def test_light_position_at_medium_odds(self, matrix):
        """市值 1200 → 赔率 ~76.7% ≥ 70% → 赔率达标"""
        cheap = FinancialData(
            cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
            cash_and_equivalents=400.0, short_term_investments=150.0,
            interest_bearing_debt=50.0, committed_investments=25.0,
            restricted_cash=10.0, overseas_cash=50.0,
            revenue=1100.0, market_cap=1200.0,
            period="FY2024", ticker="1024.HK",
        )
        oe = OECalculator(discount_rate=0.10).calculate(cheap)
        combo_a = ComboScanner().scan_combo_a(oe, KUAISHOU_EXTRA)

        # 此时 Combo A 应 4/4（赔率 76.7% > 70%）
        assert combo_a.triggered_count == 4

        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        # 胜率 5(高, 4/4) + 赔率 4(高, ≥70%) → 重仓
        assert result.win_rate_score == 5
        assert result.odds_score == 4
        assert result.action == "重仓"
        assert "15%" in result.position_range

    def test_standard_position_at_medium_win(self, matrix):
        """市值 1200, Combo A 3/4(模拟低分位不满足) + 赔率达标 → 标准仓位不行，轻仓"""
        cheap = FinancialData(
            cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
            cash_and_equivalents=400.0, short_term_investments=150.0,
            interest_bearing_debt=50.0, committed_investments=25.0,
            restricted_cash=10.0, overseas_cash=50.0,
            revenue=1100.0, market_cap=1200.0,
            period="FY2024", ticker="1024.HK",
        )
        oe = OECalculator(discount_rate=0.10).calculate(cheap)
        # 故意设高分位使条件4不触发 → 3/4
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=50.0,  # 非低分位
            structural_deterioration=False,
        )
        combo_a = ComboScanner().scan_combo_a(oe, extra)
        assert combo_a.triggered_count == 3

        result = matrix.evaluate(combo_a, oe.odds, "中等质量")
        # 胜率 3(中) + 赔率 4(高) → 轻仓
        assert result.win_rate_score == 3
        assert result.odds_score == 4
        assert result.action == "轻仓"


# ── 边界场景 ──

class TestEdgeCases:
    def test_negative_odds(self, matrix):
        combo_a = ComboScanResult(
            combo_name="Combo A", sub_conditions=[],
            triggered_count=1, total_count=4,
            triggered=False, missing=[],
        )
        result = matrix.evaluate(combo_a, -0.20, "中等质量")
        assert result.odds_score == 1
        assert result.action == "不参与"
        assert "为负" in result.reasoning

    def test_unknown_asset_tier(self, matrix):
        combo_a = ComboScanResult(
            combo_name="Combo A", sub_conditions=[],
            triggered_count=3, total_count=4,
            triggered=True, missing=[],
        )
        with pytest.raises(ValueError, match="未知资产层级"):
            matrix.evaluate(combo_a, 0.50, "未知类型")
