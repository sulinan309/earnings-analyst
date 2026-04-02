"""港股财报分析工具 - 一键生成完整分析报告

用法:
    python main.py                          # 使用内置快手模拟数据
    python main.py --ticker 1024.HK         # 指定 watchlist 中的公司
"""

import argparse
import json
import os
from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportGenerator, ReportInput


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "watchlist.json")


def load_watchlist() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_company(watchlist: dict, ticker: str) -> dict | None:
    for item in watchlist["watchlist"]:
        if item["ticker"] == ticker:
            return item
    return None


def run_analysis(
    financial_data: FinancialData,
    company_name: str,
    asset_tier: str,
    focus: str,
    quarterly_oes: list[float],
    oe_multiple_percentile: float,
    structural_deterioration: bool,
    discount_rate: float = 0.10,
) -> str:
    """执行完整分析流程，返回报告文本"""

    # 1. OE 计算
    oe_result = OECalculator(discount_rate=discount_rate).calculate(financial_data)

    # 2. Combo A 扫描
    combo_a = ComboScanner().scan_combo_a(
        oe_result,
        ComboAInput(
            asset_tier=asset_tier,
            quarterly_oes=quarterly_oes,
            oe_multiple_percentile=oe_multiple_percentile,
            structural_deterioration=structural_deterioration,
        ),
    )

    # 3. 决策矩阵
    matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, asset_tier)

    # 4. 生成报告
    report_input = ReportInput(
        company_name=company_name,
        ticker=financial_data.ticker,
        asset_tier=asset_tier,
        focus=focus,
        financial_data=financial_data,
        oe_result=oe_result,
        combo_a=combo_a,
        matrix_result=matrix_result,
        report_date=date.today(),
    )

    return ReportGenerator().generate(report_input)


# ── 内置模拟数据 ──

DEMO_DATA = {
    "1024.HK": {
        "company_name": "快手",
        "asset_tier": "中等质量",
        "focus": "电商GMV变现率、可灵商业化、海外投入节奏",
        "financial_data": FinancialData(
            cfo=220.0, maintenance_capex=40.0, total_capex=95.0,
            cash_and_equivalents=400.0, short_term_investments=150.0,
            interest_bearing_debt=50.0, committed_investments=25.0,
            restricted_cash=10.0, overseas_cash=50.0,
            revenue=1100.0, market_cap=1600.0,
            period="FY2024", ticker="1024.HK",
        ),
        "quarterly_oes": [42.0, 46.0, 44.0, 48.0],
        "oe_multiple_percentile": 25.0,
        "structural_deterioration": False,
    },
    "3690.HK": {
        "company_name": "美团",
        "asset_tier": "顶级资产",
        "focus": "核心本地商业利润率、新业务亏损收窄",
        "financial_data": FinancialData(
            cfo=380.0, maintenance_capex=55.0, total_capex=120.0,
            cash_and_equivalents=600.0, short_term_investments=250.0,
            interest_bearing_debt=150.0, committed_investments=40.0,
            restricted_cash=20.0, overseas_cash=30.0,
            revenue=2800.0, market_cap=5500.0,
            period="FY2024", ticker="3690.HK",
        ),
        "quarterly_oes": [78.0, 82.0, 80.0, 85.0],
        "oe_multiple_percentile": 35.0,
        "structural_deterioration": False,
    },
    "0700.HK": {
        "company_name": "腾讯",
        "asset_tier": "顶级资产",
        "focus": "投资组合公允价值、回购力度",
        "financial_data": FinancialData(
            cfo=1800.0, maintenance_capex=200.0, total_capex=500.0,
            cash_and_equivalents=1500.0, short_term_investments=800.0,
            interest_bearing_debt=600.0, committed_investments=100.0,
            restricted_cash=50.0, overseas_cash=300.0,
            revenue=6500.0, market_cap=38000.0,
            period="FY2024", ticker="0700.HK",
        ),
        "quarterly_oes": [390.0, 410.0, 400.0, 400.0],
        "oe_multiple_percentile": 45.0,
        "structural_deterioration": False,
    },
}


def main():
    parser = argparse.ArgumentParser(description="港股财报分析工具")
    parser.add_argument(
        "--ticker", default="1024.HK",
        help="股票代码（默认 1024.HK 快手）",
    )
    parser.add_argument(
        "--rate", type=float, default=0.10,
        help="折现率（默认 0.10，范围 0.08-0.12）",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_tickers",
        help="列出所有可用的模拟数据",
    )
    args = parser.parse_args()

    if args.list_tickers:
        print("可用模拟数据:")
        for ticker, data in DEMO_DATA.items():
            print(f"  {ticker}  {data['company_name']}  ({data['asset_tier']})")
        return

    demo = DEMO_DATA.get(args.ticker)
    if demo is None:
        print(f"错误: 未找到 {args.ticker} 的模拟数据")
        print(f"可用: {', '.join(DEMO_DATA.keys())}")
        return

    report = run_analysis(
        financial_data=demo["financial_data"],
        company_name=demo["company_name"],
        asset_tier=demo["asset_tier"],
        focus=demo["focus"],
        quarterly_oes=demo["quarterly_oes"],
        oe_multiple_percentile=demo["oe_multiple_percentile"],
        structural_deterioration=demo["structural_deterioration"],
        discount_rate=args.rate,
    )
    print(report)


if __name__ == "__main__":
    main()
