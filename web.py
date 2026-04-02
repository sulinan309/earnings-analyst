"""港股财报分析工具 - 网页版

用法:
    python web.py                  # 启动服务器，端口 8888
    python web.py --port 9000      # 自定义端口

功能:
    /                  首页：Watchlist 状态卡片 + PDF 上传
    /report/<ticker>   个股分析报告页
    /upload            POST：上传 PDF 自动解析生成报告
"""

import argparse
import cgi
import io
import json
import os
import tempfile
import webbrowser
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from main import DEMO_DATA, run_analysis
from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "watchlist.json")

# ── 共享 CSS ──

SHARED_CSS = """
:root {
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --text-muted: #484f58;
    --green: #3fb950; --red: #f85149; --yellow: #d29922; --blue: #58a6ff;
    --green-bg: rgba(63,185,80,0.12); --red-bg: rgba(248,81,73,0.12);
    --yellow-bg: rgba(210,153,34,0.12); --blue-bg: rgba(88,166,255,0.12);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: -apple-system, 'Noto Sans SC', 'PingFang SC', sans-serif; line-height: 1.6; }
a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }
"""


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


# ═══════════════════════════════════════════════════════════
#  分析逻辑
# ═══════════════════════════════════════════════════════════

def build_report_input(ticker: str, rate: float = 0.10) -> ReportInput | None:
    demo = DEMO_DATA.get(ticker)
    if demo is None:
        return None

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

    return ReportInput(
        company_name=demo["company_name"],
        ticker=ticker,
        asset_tier=demo["asset_tier"],
        focus=demo["focus"],
        financial_data=demo["financial_data"],
        oe_result=oe_result,
        combo_a=combo_a,
        matrix_result=matrix_result,
        report_date=date.today(),
    )


def get_watchlist_with_status() -> list[dict]:
    """为每只 watchlist 股票计算快速状态"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    results = []
    for item in config["watchlist"]:
        ticker = item["ticker"]
        demo = DEMO_DATA.get(ticker)
        status = {"name": item["name"], "ticker": ticker, "focus": item["focus"],
                  "asset_tier": item["asset_tier"], "has_data": False}

        if demo:
            try:
                oe = OECalculator(discount_rate=0.10).calculate(demo["financial_data"])
                combo_a = ComboScanner().scan_combo_a(
                    oe, ComboAInput(
                        asset_tier=demo["asset_tier"],
                        quarterly_oes=demo["quarterly_oes"],
                        oe_multiple_percentile=demo["oe_multiple_percentile"],
                        structural_deterioration=demo["structural_deterioration"],
                    ))
                mx = OddsMatrix().evaluate(combo_a, oe.odds, demo["asset_tier"])
                status.update({
                    "has_data": True,
                    "oe": oe.oe,
                    "margin_pct": oe.safety_margin_pct,
                    "has_margin": oe.has_safety_margin,
                    "odds": oe.odds,
                    "combo_a_count": combo_a.triggered_count,
                    "combo_a_triggered": combo_a.triggered,
                    "action": mx.action,
                    "win_score": mx.win_rate_score,
                    "odds_score": mx.odds_score,
                    "period": oe.period,
                    "market_cap": oe.market_cap,
                    "intrinsic": oe.intrinsic_value,
                })
            except Exception:
                pass

        results.append(status)
    return results


# ═══════════════════════════════════════════════════════════
#  HTML 页面生成
# ═══════════════════════════════════════════════════════════

def make_index_html() -> str:
    stocks = get_watchlist_with_status()

    cards_html = ""
    for s in stocks:
        if not s["has_data"]:
            cards_html += f"""
            <a href="#" class="stock-card no-data">
                <div class="card-header">
                    <span class="card-name">{_esc(s['name'])}</span>
                    <span class="card-ticker">{_esc(s['ticker'])}</span>
                </div>
                <div class="card-body">
                    <div class="card-no-data">暂无数据 — 请上传财报 PDF</div>
                </div>
                <div class="card-footer">{_esc(s['focus'])}</div>
            </a>"""
            continue

        margin_cls = "positive" if s["has_margin"] else "negative"
        action_cls = {"重仓": "action-heavy", "标准仓位": "action-standard",
                      "轻仓": "action-light", "不参与": "action-pass"}.get(s["action"], "action-pass")
        combo_cls = "positive" if s["combo_a_triggered"] else "text-dim"

        cards_html += f"""
        <a href="/report/{_esc(s['ticker'])}" class="stock-card">
            <div class="card-header">
                <span class="card-name">{_esc(s['name'])}</span>
                <span class="card-ticker">{_esc(s['ticker'])}</span>
                <span class="tag">{_esc(s['asset_tier'])}</span>
            </div>
            <div class="card-metrics">
                <div class="metric">
                    <div class="metric-label">OE</div>
                    <div class="metric-value">{s['oe']:.0f}<small>亿</small></div>
                </div>
                <div class="metric">
                    <div class="metric-label">安全边际</div>
                    <div class="metric-value {margin_cls}">{s['margin_pct']:+.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Combo A</div>
                    <div class="metric-value {combo_cls}">{s['combo_a_count']}/4</div>
                </div>
                <div class="metric">
                    <div class="metric-label">胜率×赔率</div>
                    <div class="metric-value">{s['win_score']}×{s['odds_score']}</div>
                </div>
            </div>
            <div class="card-action {action_cls}">{_esc(s['action'])}</div>
            <div class="card-footer">{_esc(s['focus'])} · {_esc(s['period'])}</div>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>港股财报分析工具</title>
<style>
{SHARED_CSS}
.container {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px; }}
.page-header {{ text-align: center; margin-bottom: 40px; }}
.page-header h1 {{ font-size: 32px; margin-bottom: 8px; }}
.page-header p {{ color: var(--text-dim); font-size: 15px; }}
.stock-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin-bottom: 40px; }}
.stock-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-decoration: none !important; color: var(--text); transition: border-color 0.2s, transform 0.15s; display: flex; flex-direction: column; gap: 12px; }}
.stock-card:hover {{ border-color: var(--blue); transform: translateY(-2px); }}
.stock-card.no-data {{ opacity: 0.5; cursor: default; }}
.stock-card.no-data:hover {{ border-color: var(--border); transform: none; }}
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

/* 上传区域 */
.upload-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 32px; }}
.upload-section h2 {{ font-size: 20px; margin-bottom: 16px; }}
.upload-form {{ display: flex; flex-direction: column; gap: 16px; }}
.form-row {{ display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }}
.form-group {{ display: flex; flex-direction: column; gap: 4px; }}
.form-group label {{ font-size: 13px; color: var(--text-dim); }}
.form-group input, .form-group select {{ background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 8px 12px; font-size: 14px; }}
.form-group input[type="file"] {{ padding: 6px; }}
.form-group input:focus, .form-group select:focus {{ outline: none; border-color: var(--blue); }}
.btn {{ background: var(--blue); color: #fff; border: none; border-radius: 8px; padding: 10px 24px; font-size: 15px; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }}
.btn:hover {{ opacity: 0.85; }}
.btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.upload-hint {{ font-size: 13px; color: var(--text-muted); }}
.upload-status {{ display: none; padding: 12px; border-radius: 8px; font-size: 14px; margin-top: 8px; }}
.upload-status.loading {{ display: block; background: var(--blue-bg); color: var(--blue); }}
.upload-status.error {{ display: block; background: var(--red-bg); color: var(--red); }}

.footer {{ text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">

<div class="page-header">
    <h1>港股财报分析工具</h1>
    <p>基于李录 Owner's Earnings 框架 · 聚焦现金流质量与保守估值</p>
</div>

<div class="stock-grid">
    {cards_html}
</div>

<div class="upload-section">
    <h2>上传财报 PDF</h2>
    <form class="upload-form" id="uploadForm" action="/upload" method="POST" enctype="multipart/form-data">
        <div class="form-row">
            <div class="form-group" style="flex:2">
                <label>财报 PDF 文件</label>
                <input type="file" name="pdf" accept=".pdf" required id="pdfInput">
            </div>
            <div class="form-group">
                <label>公司名称</label>
                <input type="text" name="company_name" placeholder="如: 腾讯" required>
            </div>
            <div class="form-group">
                <label>股票代码</label>
                <input type="text" name="ticker" placeholder="如: 0700.HK" required>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>资产层级</label>
                <select name="asset_tier">
                    <option value="顶级资产">顶级资产 (赔率≥40%)</option>
                    <option value="中等质量" selected>中等质量 (赔率≥70%)</option>
                    <option value="高波动">高波动 (赔率≥100%)</option>
                </select>
            </div>
            <div class="form-group">
                <label>折现率</label>
                <select name="discount_rate">
                    <option value="0.08">8% (乐观)</option>
                    <option value="0.10" selected>10% (基准)</option>
                    <option value="0.12">12% (保守)</option>
                </select>
            </div>
            <div class="form-group">
                <label>当前市值 (亿港币)</label>
                <input type="number" name="market_cap" placeholder="如: 42000" required step="0.1">
            </div>
            <button type="submit" class="btn" id="submitBtn">解析并生成报告</button>
        </div>
        <div class="upload-hint">
            支持港交所业绩公告 PDF · Claude API 自动提取 CFO/Capex/净现金等字段 · 缺失字段标注 null 并说明原因
        </div>
        <div class="upload-status" id="uploadStatus"></div>
    </form>
</div>

<div class="footer">
    港股财报分析工具 · 基于李录 Owner's Earnings 框架 · 数据来源优先级: 公司财报原文 &gt; 港交所公告 &gt; 管理层业绩会纪要
</div>

</div>

<script>
document.getElementById('uploadForm').addEventListener('submit', function(e) {{
    var status = document.getElementById('uploadStatus');
    var btn = document.getElementById('submitBtn');
    status.className = 'upload-status loading';
    status.textContent = '正在解析财报 PDF，请稍候...';
    btn.disabled = true;
    btn.textContent = '解析中...';
}});
</script>
</body>
</html>"""


def make_upload_result_html(title: str, message: str, is_error: bool = False) -> str:
    cls = "error" if is_error else ""
    bg = "var(--red-bg)" if is_error else "var(--green-bg)"
    color = "var(--red)" if is_error else "var(--green)"
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>{_esc(title)}</title>
<style>{SHARED_CSS}
.container {{ max-width: 600px; margin: 80px auto; text-align: center; }}
.msg-box {{ background: {bg}; color: {color}; border-radius: 12px; padding: 32px; margin: 24px 0; font-size: 16px; }}
.btn {{ display: inline-block; background: var(--blue); color: #fff; padding: 10px 24px; border-radius: 8px; font-weight: 600; margin-top: 16px; }}
</style></head><body><div class="container">
<h1>{_esc(title)}</h1>
<div class="msg-box">{message}</div>
<a href="/" class="btn">返回首页</a>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════
#  HTTP 服务器
# ═══════════════════════════════════════════════════════════

class ReportHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = urlparse(self.path).path.strip("/")

        if not path:
            self._send_html(make_index_html())
        elif path.startswith("report/"):
            ticker = path[len("report/"):]
            inp = build_report_input(ticker)
            if inp:
                self._send_html(generate_html(inp))
            else:
                self._send_html(make_upload_result_html(
                    "未找到数据", f"未找到 {ticker} 的分析数据", is_error=True
                ), status=404)
        else:
            self._send_html(make_upload_result_html("404", "页面不存在", is_error=True), status=404)

    def do_POST(self):
        if urlparse(self.path).path.strip("/") != "upload":
            self._send_html(make_upload_result_html("错误", "无效的请求路径", True), 404)
            return

        try:
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                raise ValueError("请使用 multipart/form-data 上传")

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST",
                         "CONTENT_TYPE": content_type},
            )

            # 提取表单字段
            company_name = form.getfirst("company_name", "未知公司")
            ticker = form.getfirst("ticker", "0000.HK")
            asset_tier = form.getfirst("asset_tier", "中等质量")
            discount_rate = float(form.getfirst("discount_rate", "0.10"))
            market_cap = float(form.getfirst("market_cap", "0"))

            if market_cap <= 0:
                raise ValueError("市值必须大于 0")

            # 读取 PDF
            pdf_field = form["pdf"]
            if not pdf_field.file:
                raise ValueError("请选择 PDF 文件")
            pdf_bytes = pdf_field.file.read()
            if len(pdf_bytes) < 100:
                raise ValueError("PDF 文件无效或为空")

            # 尝试使用 Claude API 解析
            report_html = self._parse_and_analyze(
                pdf_bytes, company_name, ticker, asset_tier,
                discount_rate, market_cap,
            )
            self._send_html(report_html)

        except Exception as e:
            self._send_html(make_upload_result_html(
                "解析失败", f"{_esc(str(e))}<br><br>请检查 ANTHROPIC_API_KEY 环境变量是否已设置。",
                is_error=True,
            ))

    def _parse_and_analyze(
        self, pdf_bytes: bytes, company_name: str, ticker: str,
        asset_tier: str, discount_rate: float, market_cap: float,
    ) -> str:
        """解析 PDF → 提取数据 → 运行 OE 分析 → 生成 HTML 报告"""
        from src.parsers.report_parser import ReportParser

        parser = ReportParser()
        parsed = parser.parse_pdf_bytes(pdf_bytes)

        # 用解析结果构建 FinancialData
        # 缺失字段用保守默认值
        def v(field, default=0.0):
            return field.value if field.value is not None else default

        cfo = v(parsed.cfo)
        maint_capex = v(parsed.maintenance_capex, v(parsed.total_capex) * 0.5)
        is_estimated = parsed.maintenance_capex.value is None

        fd = FinancialData(
            cfo=cfo,
            maintenance_capex=maint_capex,
            total_capex=v(parsed.total_capex),
            cash_and_equivalents=v(parsed.cash_and_equivalents),
            short_term_investments=v(parsed.short_term_investments),
            interest_bearing_debt=v(parsed.interest_bearing_debt),
            committed_investments=v(parsed.committed_investments),
            restricted_cash=v(parsed.restricted_cash),
            overseas_cash=v(parsed.overseas_cash),
            revenue=v(parsed.revenue),
            market_cap=market_cap,
            period=parsed.period or "未知",
            ticker=ticker,
            maintenance_capex_is_estimated=is_estimated,
            maintenance_capex_note="Claude API 未能从财报中拆分维持性Capex，按总Capex的50%估算" if is_estimated else "",
        )

        oe_result = OECalculator(discount_rate=discount_rate).calculate(fd)

        quarterly_oes = [round(oe_result.oe / 4, 1)] * 4
        combo_a = ComboScanner().scan_combo_a(
            oe_result,
            ComboAInput(
                asset_tier=asset_tier,
                quarterly_oes=quarterly_oes,
                oe_multiple_percentile=50.0,
                structural_deterioration=False,
            ),
        )

        matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, asset_tier)

        inp = ReportInput(
            company_name=parsed.company_name or company_name,
            ticker=ticker,
            asset_tier=asset_tier,
            focus=f"通过 PDF 上传解析 · 缺失 {len(parsed.missing_fields())} 个字段",
            financial_data=fd,
            oe_result=oe_result,
            combo_a=combo_a,
            matrix_result=matrix_result,
            report_date=date.today(),
        )

        return generate_html(inp)

    def _send_html(self, html: str, status: int = 200):
        content = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, fmt, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description="港股财报分析工具 - 网页版")
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), ReportHandler)
    url = f"http://localhost:{args.port}"
    print(f"港股财报分析工具已启动: {url}")
    print("功能: Watchlist 状态总览 · PDF 上传解析 · OE 分析报告")
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
