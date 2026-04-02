"""Combo A 扫描测试 - 快手 (1024.HK) FY2024 模拟数据

已知结果：
- OE = 180 亿，内在价值 = 2120 亿，市值 = 1600 亿
- 安全边际 +32.5%，赔率 32.5%
- 中等质量资产，赔率阈值 70%

预期 Combo A 判定：
- 条件1 ✅ 市值(1600) < 内在价值(2120)
- 条件2 ❌ 赔率 32.5% < 中等质量阈值 70%
- 条件3 ✅ 近4季OE均为正且稳定
- 条件4 ✅ 历史低分位 25% + 无结构性恶化
→ 3/4 触发，Combo A 有效
"""

import pytest

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput


KUAISHOU_FY2024 = FinancialData(
    cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
    cash_and_equivalents=400.0, short_term_investments=150.0,
    interest_bearing_debt=50.0, committed_investments=25.0,
    restricted_cash=10.0, overseas_cash=50.0,
    revenue=1100.0, market_cap=1600.0,
    period="FY2024", ticker="1024.HK",
)


@pytest.fixture
def kuaishou_oe():
    return OECalculator(discount_rate=0.10).calculate(KUAISHOU_FY2024)


@pytest.fixture
def scanner():
    return ComboScanner()


# ── 快手基准场景：3/4 触发 ──

class TestKuaishouBaseline:
    """快手 FY2024: 条件1✅ 条件2❌ 条件3✅ 条件4✅ → 3/4 触发"""

    def test_combo_a_triggered(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],   # 稳定正OE
            oe_multiple_percentile=25.0,                # 历史低分位
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        assert result.triggered is True
        assert result.triggered_count == 3

    def test_condition_1_safety_margin(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c1 = result.sub_conditions[0]
        assert c1.triggered is True
        assert c1.gap is None

    def test_condition_2_odds_not_met(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c2 = result.sub_conditions[1]
        assert c2.triggered is False
        assert "32.5%" in c2.detail
        assert "70%" in c2.detail
        assert c2.gap is not None

    def test_condition_3_oe_stable(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c3 = result.sub_conditions[2]
        assert c3.triggered is True

    def test_condition_4_low_percentile(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c4 = result.sub_conditions[3]
        assert c4.triggered is True

    def test_missing_only_odds(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        assert len(result.missing) == 1
        assert "赔率" in result.missing[0].name


# ── 赔率达标：顶级资产阈值低，同样的赔率可以过 ──

class TestTopTierAsset:
    """若视快手为顶级资产 (>40%)，32.5% 仍不达标，但边界测试很近"""

    def test_top_tier_still_not_met(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="顶级资产",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c2 = result.sub_conditions[1]
        # 32.5% < 40%，仍不达标
        assert c2.triggered is False


# ── OE 不稳定场景 ──

class TestUnstableOE:
    """某季度 OE 为负或波动过大 → 条件3不触发"""

    def test_negative_quarter(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, -5.0, 44.0, 48.0],   # Q2 为负
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c3 = result.sub_conditions[2]
        assert c3.triggered is False
        assert "非正值" in c3.gap

    def test_volatile_oe(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[20.0, 60.0, 25.0, 75.0],   # 波动巨大
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c3 = result.sub_conditions[2]
        assert c3.triggered is False
        assert "波动率" in c3.gap

    def test_negative_drops_to_2_of_4(self, kuaishou_oe, scanner):
        """OE 不稳定 + 赔率不足 → 仅 2/4，Combo A 不触发"""
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, -5.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        assert result.triggered is False
        assert result.triggered_count == 2
        assert len(result.missing) == 2


# ── 结构性恶化场景 ──

class TestStructuralDeterioration:
    """条件4: 高分位或结构性恶化 → 不触发"""

    def test_high_percentile(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=60.0,               # 非低分位
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c4 = result.sub_conditions[3]
        assert c4.triggered is False
        assert "≤30%" in c4.gap

    def test_deterioration_flag(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=True,             # 结构性恶化
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        c4 = result.sub_conditions[3]
        assert c4.triggered is False
        assert "结构性恶化" in c4.gap


# ── summary 输出 ──

class TestSummaryOutput:
    def test_summary_contains_key_info(self, kuaishou_oe, scanner):
        extra = ComboAInput(
            asset_tier="中等质量",
            quarterly_oes=[42.0, 46.0, 44.0, 48.0],
            oe_multiple_percentile=25.0,
            structural_deterioration=False,
        )
        result = scanner.scan_combo_a(kuaishou_oe, extra)
        text = result.summary()
        assert "Combo A" in text
        assert "3/4" in text
        assert "触发" in text
        assert "赔率" in text       # 未达标项中提到赔率
