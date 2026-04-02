"""HTML 报告生成测试"""

import pytest
from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html


KUAISHOU_FY2024 = FinancialData(
    cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
    cash_and_equivalents=400.0, short_term_investments=150.0,
    interest_bearing_debt=50.0, committed_investments=25.0,
    restricted_cash=10.0, overseas_cash=50.0,
    revenue=1100.0, market_cap=1600.0,
    period="FY2024", ticker="1024.HK",
)


@pytest.fixture
def kuaishou_html():
    oe = OECalculator(discount_rate=0.10).calculate(KUAISHOU_FY2024)
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier="中等质量", quarterly_oes=[42.0, 46.0, 44.0, 48.0],
        oe_multiple_percentile=25.0, structural_deterioration=False,
    ))
    matrix = OddsMatrix().evaluate(combo_a, oe.odds, "中等质量")
    inp = ReportInput(
        company_name="快手", ticker="1024.HK", asset_tier="中等质量",
        focus="电商GMV变现率、可灵商业化、海外投入节奏",
        financial_data=KUAISHOU_FY2024, oe_result=oe,
        combo_a=combo_a, matrix_result=matrix,
        report_date=date(2026, 4, 2),
    )
    return generate_html(inp)


class TestHTMLContent:
    def test_is_valid_html(self, kuaishou_html):
        assert kuaishou_html.startswith("<!DOCTYPE html>")
        assert "</html>" in kuaishou_html

    def test_contains_company_info(self, kuaishou_html):
        assert "快手" in kuaishou_html
        assert "1024.HK" in kuaishou_html
        assert "2026-04-02" in kuaishou_html

    def test_contains_oe_data(self, kuaishou_html):
        assert "180.00" in kuaishou_html  # OE
        assert "220.00" in kuaishou_html  # CFO
        assert "16.4%" in kuaishou_html   # margin

    def test_contains_valuation(self, kuaishou_html):
        assert "2120" in kuaishou_html    # intrinsic value
        assert "+32.5%" in kuaishou_html  # safety margin

    def test_contains_combo_status(self, kuaishou_html):
        assert "3/4" in kuaishou_html
        assert "未达标" in kuaishou_html

    def test_contains_decision(self, kuaishou_html):
        assert "不参与" in kuaishou_html

    def test_contains_sensitivity(self, kuaishou_html):
        assert "8%" in kuaishou_html
        assert "12%" in kuaishou_html

    def test_size_reasonable(self, kuaishou_html):
        # HTML 应该在 5-30KB 之间
        size_kb = len(kuaishou_html.encode()) / 1024
        assert 5 < size_kb < 30


class TestWebServer:
    def test_build_report(self):
        from web import build_report_html
        html = build_report_html("1024.HK")
        assert "快手" in html
        assert "<!DOCTYPE html>" in html

    def test_build_all_tickers(self):
        from web import build_report_html
        for ticker in ["1024.HK", "3690.HK", "0700.HK"]:
            html = build_report_html(ticker)
            assert "<!DOCTYPE html>" in html

    def test_unknown_ticker(self):
        from web import build_report_html
        html = build_report_html("9999.HK")
        assert "未找到" in html

    def test_index_page(self):
        from web import make_index_html
        html = make_index_html()
        assert "快手" in html
        assert "美团" in html
        assert "腾讯" in html
