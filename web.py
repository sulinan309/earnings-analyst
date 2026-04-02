"""网页预览服务器

用法:
    python web.py                      # 默认快手，端口 8888
    python web.py --ticker 3690.HK     # 美团
    python web.py --port 9000          # 自定义端口
"""

import argparse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import date

from main import DEMO_DATA
from src.frameworks.oe_calculator import OECalculator
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html


def build_report_html(ticker: str, rate: float = 0.10) -> str:
    demo = DEMO_DATA.get(ticker)
    if demo is None:
        tickers = ", ".join(DEMO_DATA.keys())
        return f"<h1>未找到 {ticker}</h1><p>可用: {tickers}</p>"

    oe_result = OECalculator(discount_rate=rate).calculate(demo["financial_data"])
    combo_a = ComboScanner().scan_combo_a(
        oe_result,
        ComboAInput(
            asset_tier=demo["asset_tier"],
            quarterly_oes=demo["quarterly_oes"],
            oe_multiple_percentile=demo["oe_multiple_percentile"],
            structural_deterioration=demo["structural_deterioration"],
        ),
    )
    matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, demo["asset_tier"])

    return generate_html(ReportInput(
        company_name=demo["company_name"],
        ticker=ticker,
        asset_tier=demo["asset_tier"],
        focus=demo["focus"],
        financial_data=demo["financial_data"],
        oe_result=oe_result,
        combo_a=combo_a,
        matrix_result=matrix_result,
        report_date=date.today(),
    ))


def make_index_html() -> str:
    """生成公司列表首页"""
    cards = ""
    for ticker, d in DEMO_DATA.items():
        cards += f'<a href="/{ticker}" class="card"><strong>{d["company_name"]}</strong><br><span>{ticker}</span><br><small>{d["asset_tier"]}</small></a>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>港股财报分析</title>
<style>
body {{ background: #0d1117; color: #e6edf3; font-family: -apple-system, 'Noto Sans SC', sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }}
h1 {{ margin-bottom: 32px; }}
.grid {{ display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px 32px; text-decoration: none; color: #e6edf3; transition: border-color 0.2s; text-align: center; }}
.card:hover {{ border-color: #58a6ff; }}
.card span {{ color: #8b949e; }}
.card small {{ color: #58a6ff; }}
</style></head><body>
<h1>港股财报分析工具</h1>
<div class="grid">{cards}</div>
</body></html>"""


class ReportHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.strip("/")
        if not path:
            html = make_index_html()
        elif path in DEMO_DATA:
            html = build_report_html(path)
        else:
            self.send_error(404)
            return

        content = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass  # 静默日志


def main():
    parser = argparse.ArgumentParser(description="港股财报分析 - 网页预览")
    parser.add_argument("--ticker", default=None, help="直接打开某只股票的报告")
    parser.add_argument("--port", type=int, default=8888, help="端口（默认 8888）")
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), ReportHandler)
    url = f"http://localhost:{args.port}"
    if args.ticker:
        url += f"/{args.ticker}"
    print(f"分析报告预览: {url}")
    print("按 Ctrl+C 停止")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
        server.server_close()


if __name__ == "__main__":
    main()
