"""报告生成器测试 - 快手 FY2024 完整报告"""

import pytest
from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportGenerator, ReportInput


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
def kuaishou_report_input():
    oe_result = OECalculator(discount_rate=0.10).calculate(KUAISHOU_FY2024)
    combo_a = ComboScanner().scan_combo_a(oe_result, KUAISHOU_EXTRA)
    matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, "中等质量")
    return ReportInput(
        company_name="快手",
        ticker="1024.HK",
        asset_tier="中等质量",
        focus="电商GMV变现率、可灵商业化、海外投入节奏",
        financial_data=KUAISHOU_FY2024,
        oe_result=oe_result,
        combo_a=combo_a,
        matrix_result=matrix_result,
        report_date=date(2026, 4, 2),
    )


class TestReportContent:
    """验证报告包含 CLAUDE.md 要求的所有必要内容"""

    def test_contains_oe_calculation(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "Owner's Earnings" in report
        assert "220.00" in report      # CFO
        assert "40.00" in report       # 维持性 Capex
        assert "180.00" in report      # OE

    def test_contains_net_cash(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "净现金" in report
        assert "500.00" in report      # 毛净现金
        assert "320.00" in report      # 可分配净现金

    def test_contains_safety_margin(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "安全边际" in report
        assert "2120" in report        # 内在价值
        assert "1600" in report        # 市值
        assert "+32.5%" in report      # 安全边际百分比

    def test_contains_combo_status(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "Combo A" in report
        assert "3/4" in report
        assert "触发" in report

    def test_contains_position_advice(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "建议操作" in report
        assert "不参与" in report
        assert "建议仓位" in report

    def test_contains_sensitivity(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "8%" in report
        assert "10%" in report
        assert "12%" in report

    def test_contains_next_steps(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "后续跟踪" in report

    def test_contains_header_metadata(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert "快手" in report
        assert "1024.HK" in report
        assert "2026-04-02" in report
        assert "FY2024" in report
        assert "中等质量" in report


class TestReportFormat:
    """验证报告格式规范"""

    def test_report_is_nonempty_string(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        assert isinstance(report, str)
        assert len(report) > 500

    def test_six_sections(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        # 6 个主要段落标题
        for keyword in [
            "Owner's Earnings 计算",
            "净现金",
            "零增长估值",
            "Combo A",
            "仓位决策",
            "后续跟踪",
        ]:
            assert keyword in report


class TestPrintReport:
    """输出完整报告到 stdout（可用 -s 查看）"""

    def test_print_full_report(self, kuaishou_report_input):
        report = ReportGenerator().generate(kuaishou_report_input)
        print("\n" + report)
