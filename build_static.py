"""生成静态 HTML 站点到 docs/ 目录，用于 GitHub Pages 部署

用法:
    python build_static.py          # 生成到 docs/
    python build_static.py --open   # 生成并打开首页
"""

import argparse
import json
import os
import webbrowser
from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html
from analyze_all import COMPANIES

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "docs")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "watchlist.json")


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def build_report_input(ticker: str, rate: float = 0.10) -> ReportInput | None:
    co = COMPANIES.get(ticker)
    if co is None:
        return None
    fd = co["data"]
    oe_result = OECalculator(discount_rate=rate).calculate(fd)
    combo_a = ComboScanner().scan_combo_a(
        oe_result,
        ComboAInput(
            asset_tier=co["asset_tier"],
            quarterly_oes=co["quarterly_oes"],
            oe_multiple_percentile=co["oe_percentile"],
            structural_deterioration=False,
        ),
    )
    matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, co["asset_tier"])
    return ReportInput(
        company_name=co["name"], ticker=ticker,
        asset_tier=co["asset_tier"], focus=co["focus"],
        financial_data=fd, oe_result=oe_result,
        combo_a=combo_a, matrix_result=matrix_result,
        report_date=date.today(),
    )


def build_index_html(reports: dict[str, ReportInput]) -> str:
    """生成首页：Watchlist 状态卡片"""

    cards = ""
    for ticker, inp in reports.items():
        oe = inp.oe_result
        m = inp.matrix_result
        ca = inp.combo_a
        margin_cls = "positive" if oe.has_safety_margin else "negative"
        action_cls = {"重仓": "action-heavy", "标准仓位": "action-standard",
                      "轻仓": "action-light"}.get(m.action, "action-pass")
        combo_cls = "positive" if ca.triggered else "text-dim"
        safe_ticker = ticker.replace(".", "_")

        cards += f"""
        <a href="{safe_ticker}.html" class="stock-card">
            <div class="card-header">
                <span class="card-name">{_esc(inp.company_name)}</span>
                <span class="card-ticker">{_esc(ticker)}</span>
                <span class="tag">{_esc(inp.asset_tier)}</span>
            </div>
            <div class="card-metrics">
                <div class="metric">
                    <div class="metric-label">OE</div>
                    <div class="metric-value">{oe.oe:.0f}<small>亿</small></div>
                </div>
                <div class="metric">
                    <div class="metric-label">安全边际</div>
                    <div class="metric-value {margin_cls}">{oe.safety_margin_pct:+.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Combo A</div>
                    <div class="metric-value {combo_cls}">{ca.triggered_count}/4</div>
                </div>
                <div class="metric">
                    <div class="metric-label">胜率×赔率</div>
                    <div class="metric-value">{m.win_rate_score}×{m.odds_score}</div>
                </div>
            </div>
            <div class="card-action {action_cls}">{_esc(m.action)}</div>
            <div class="card-footer">{_esc(inp.focus)} · {_esc(oe.period)}</div>
        </a>"""

    today = date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>港股财报分析工具</title>
<style>
:root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --text-muted: #484f58;
    --green: #3fb950; --red: #f85149; --yellow: #d29922; --blue: #58a6ff;
    --green-bg: rgba(63,185,80,0.12); --red-bg: rgba(248,81,73,0.12);
    --yellow-bg: rgba(210,153,34,0.12); --blue-bg: rgba(88,166,255,0.12);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, 'Noto Sans SC', 'PingFang SC', sans-serif; line-height: 1.6; }}
a {{ color: var(--blue); text-decoration: none; }}
.container {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px; }}
.page-header {{ text-align: center; margin-bottom: 40px; }}
.page-header h1 {{ font-size: 32px; margin-bottom: 8px; }}
.page-header p {{ color: var(--text-dim); font-size: 15px; }}
.stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
.stock-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-decoration: none !important; color: var(--text); transition: border-color 0.2s, transform 0.15s; display: flex; flex-direction: column; gap: 12px; }}
.stock-card:hover {{ border-color: var(--blue); transform: translateY(-2px); }}
.stock-card.no-data {{ opacity: 0.5; }}
.card-header {{ display: flex; align-items: center; gap: 8px; }}
.card-name {{ font-size: 20px; font-weight: 700; }}
.card-ticker {{ color: var(--text-dim); font-size: 14px; }}
.tag {{ background: var(--blue-bg); color: var(--blue); padding: 2px 10px; border-radius: 12px; font-size: 12px; margin-left: auto; }}
.card-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }}
.metric {{ text-align: center; background: var(--bg); border-radius: 8px; padding: 8px 4px; }}
.metric-label {{ font-size: 11px; color: var(--text-muted); }}
.metric-value {{ font-size: 18px; font-weight: 700; font-family: 'SF Mono', monospace; }}
.metric-value small {{ font-size: 12px; font-weight: 400; }}
.card-action {{ text-align: center; font-weight: 700; font-size: 15px; padding: 6px; border-radius: 8px; }}
.action-heavy {{ background: var(--green-bg); color: var(--green); }}
.action-standard {{ background: var(--blue-bg); color: var(--blue); }}
.action-light {{ background: var(--yellow-bg); color: var(--yellow); }}
.action-pass {{ background: var(--red-bg); color: var(--red); }}
.card-footer {{ font-size: 12px; color: var(--text-muted); }}
.card-no-data {{ color: var(--text-muted); font-size: 14px; padding: 20px 0; text-align: center; }}
.positive {{ color: var(--green); }}
.negative {{ color: var(--red); }}
.text-dim {{ color: var(--text-dim); }}
.footer {{ text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
    <div class="page-header">
        <h1>港股财报分析工具</h1>
        <p>基于李录 Owner's Earnings 框架 · 聚焦现金流质量与保守估值 · 更新于 {today}</p>
    </div>
    <div class="stock-grid">{cards}</div>
    <div class="footer">
        港股财报分析工具 · 数据来源: 公司财报原文 &gt; 港交所公告 &gt; 管理层业绩会纪要<br>
        PDF 上传解析功能请在本地运行: <code>python web.py</code>
    </div>
</div>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="生成静态 HTML 站点")
    parser.add_argument("--open", action="store_true", help="生成后打开首页")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 生成每只股票的报告
    reports: dict[str, ReportInput] = {}
    for ticker in COMPANIES:
        inp = build_report_input(ticker)
        if inp is None:
            continue
        reports[ticker] = inp

        # 报告页的返回链接指向 index.html
        html = generate_html(inp).replace('href="/"', 'href="index.html"')
        safe_name = ticker.replace(".", "_")
        path = os.path.join(OUTPUT_DIR, f"{safe_name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  ✓ {path}")

    # 首页
    index_html = build_index_html(reports)
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  ✓ {index_path}")

    print(f"\n静态站点已生成到 {OUTPUT_DIR}/")
    print(f"共 {len(reports) + 1} 个页面")

    if args.open:
        webbrowser.open(f"file://{os.path.abspath(index_path)}")


if __name__ == "__main__":
    main()
