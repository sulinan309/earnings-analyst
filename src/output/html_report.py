"""HTML 报告生成器

将 AnalysisInput 渲染为可在浏览器中预览的单文件 HTML 报告。
"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, OEResult, FinancialData
from src.signals.combo_scanner import ComboScanResult
from src.frameworks.odds_matrix import MatrixResult
from src.frameworks.kpi_dashboard import get_kpi_dashboard, KPIDashboard
from src.frameworks.management_signals import get_management_signals, ManagementSignals
from src.frameworks.variant_view import get_variant_view, VariantView
from src.frameworks.deep_analysis import DeepAnalysis, ComboSignal, CoreProduct
from src.output.report_generator import ReportInput


def generate_html(inp: ReportInput, deep=None) -> str:
    """生成完整的 HTML 报告

    Args:
        inp: 基础报告输入
        deep: FullAnalysisResult（可选），有的话渲染 9 个新 section
    """
    oe = inp.oe_result
    fd = inp.financial_data
    ca = inp.combo_a
    m = inp.matrix_result
    d = inp.report_date or date.today()

    scenarios = OECalculator(discount_rate=0.10).scenario_analysis(fd)
    kpi = get_kpi_dashboard(inp.ticker)
    mgmt = get_management_signals(inp.ticker)
    variant = get_variant_view(inp.ticker)

    # 从 deep (FullAnalysisResult) 中提取 DeepAnalysis 和 capex_sim
    deep_analysis = None
    capex_sim = None
    if deep is not None:
        deep_analysis = getattr(deep, 'deep', None)
        capex_sim = getattr(deep, 'capex_sim', None)

    margin_class = "positive" if oe.has_safety_margin else "negative"
    margin_label = "存在安全边际" if oe.has_safety_margin else "无安全边际"

    action_class = {
        "重仓": "action-heavy",
        "标准仓位": "action-standard",
        "轻仓": "action-light",
        "不参与": "action-pass",
    }.get(m.action, "action-pass")

    # Combo A 子条件 HTML
    combo_rows = ""
    for sc in ca.sub_conditions:
        icon = "check" if sc.triggered else "cross"
        cls = "triggered" if sc.triggered else "not-triggered"
        gap_html = f'<div class="gap">→ {_esc(sc.gap)}</div>' if sc.gap else ""
        combo_rows += f"""
        <div class="condition {cls}">
            <div class="condition-header">
                <span class="icon-{icon}"></span>
                <span class="condition-name">{_esc(sc.name)}</span>
            </div>
            <div class="condition-detail">{_esc(sc.detail)}</div>
            {gap_html}
        </div>"""

    # (scenarios table is rendered inline in the HTML template)

    # 缺失项
    missing_html = ""
    if ca.missing:
        items = "".join(
            f'<li><strong>{_esc(sc.name.split("（")[0])}</strong>: {_esc(sc.gap or "")}</li>'
            for sc in ca.missing
        )
        missing_html = f"""
        <div class="missing-box">
            <div class="missing-title">未达标项 ({len(ca.missing)} 条)</div>
            <ul>{items}</ul>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_esc(inp.company_name)} ({_esc(inp.ticker)}) 分析报告</title>
<style>
:root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --text: #e6edf3; --text-dim: #8b949e; --text-muted: #484f58;
    --green: #3fb950; --red: #f85149; --yellow: #d29922; --blue: #58a6ff;
    --green-bg: rgba(63,185,80,0.12); --red-bg: rgba(248,81,73,0.12);
    --yellow-bg: rgba(210,153,34,0.12); --blue-bg: rgba(88,166,255,0.12);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--text); font-family: -apple-system, 'Noto Sans SC', sans-serif; line-height: 1.6; padding: 24px; max-width: 960px; margin: 0 auto; }}
.header {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 32px; margin-bottom: 24px; }}
.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header .meta {{ color: var(--text-dim); font-size: 14px; display: flex; gap: 16px; flex-wrap: wrap; }}
.tag {{ background: var(--blue-bg); color: var(--blue); padding: 2px 10px; border-radius: 12px; font-size: 13px; }}
.section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-bottom: 16px; }}
.section h2 {{ font-size: 18px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }}
.calc-table {{ width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }}
.calc-table td {{ padding: 6px 12px; }}
.calc-table td:last-child {{ text-align: right; font-family: 'SF Mono', 'Fira Code', monospace; }}
.calc-table .separator td {{ border-top: 1px solid var(--border); }}
.calc-table .result td {{ font-weight: 700; font-size: 16px; }}
.calc-table .op {{ color: var(--text-dim); width: 20px; }}
.positive {{ color: var(--green); }}
.negative {{ color: var(--red); }}
.data-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }}
.data-card {{ background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }}
.data-card .label {{ font-size: 13px; color: var(--text-dim); margin-bottom: 4px; }}
.data-card .value {{ font-size: 24px; font-weight: 700; font-family: 'SF Mono', monospace; }}
.data-card .sub {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}
.sens-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
.sens-table th, .sens-table td {{ padding: 8px 12px; text-align: right; font-size: 14px; }}
.sens-table th {{ color: var(--text-dim); border-bottom: 1px solid var(--border); font-weight: 500; }}
.sens-table td {{ border-bottom: 1px solid var(--border); font-family: 'SF Mono', monospace; }}
.sens-table tr.current {{ background: var(--blue-bg); }}
.condition {{ padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; }}
.condition.triggered {{ background: var(--green-bg); border-left: 3px solid var(--green); }}
.condition.not-triggered {{ background: var(--red-bg); border-left: 3px solid var(--red); }}
.condition-header {{ font-weight: 600; margin-bottom: 4px; }}
.icon-check::before {{ content: "✅ "; }}
.icon-cross::before {{ content: "❌ "; }}
.condition-detail {{ font-size: 13px; color: var(--text-dim); }}
.gap {{ font-size: 13px; color: var(--yellow); margin-top: 4px; }}
.missing-box {{ background: var(--yellow-bg); border: 1px solid rgba(210,153,34,0.3); border-radius: 8px; padding: 16px; margin-top: 16px; }}
.missing-title {{ font-weight: 600; color: var(--yellow); margin-bottom: 8px; }}
.missing-box ul {{ padding-left: 20px; font-size: 14px; }}
.missing-box li {{ margin-bottom: 4px; }}
.decision-box {{ text-align: center; padding: 24px; border-radius: 12px; margin: 16px 0; }}
.action-heavy {{ background: var(--green-bg); border: 2px solid var(--green); }}
.action-standard {{ background: var(--blue-bg); border: 2px solid var(--blue); }}
.action-light {{ background: var(--yellow-bg); border: 2px solid var(--yellow); }}
.action-pass {{ background: var(--red-bg); border: 2px solid var(--red); }}
.decision-box .action {{ font-size: 32px; font-weight: 800; }}
.decision-box .position {{ font-size: 18px; color: var(--text-dim); margin-top: 4px; }}
.score-bar {{ display: flex; gap: 16px; justify-content: center; margin: 16px 0; }}
.score-item {{ text-align: center; }}
.score-item .score-label {{ font-size: 13px; color: var(--text-dim); }}
.score-item .score-value {{ font-size: 36px; font-weight: 800; font-family: 'SF Mono', monospace; }}
.reasoning {{ font-size: 14px; color: var(--text-dim); text-align: center; margin-top: 8px; max-width: 600px; margin-left: auto; margin-right: auto; }}
.next-steps {{ list-style: none; padding: 0; }}
.next-steps li {{ padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px; }}
.next-steps li::before {{ content: "→ "; color: var(--blue); font-weight: 700; }}
.warn-box {{ background: var(--yellow-bg); border: 1px solid rgba(210,153,34,0.3); border-radius: 8px; padding: 12px 16px; margin-top: 12px; font-size: 13px; color: var(--yellow); }}
.portfolio-box {{ background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-top: 12px; }}
.portfolio-box .portfolio-title {{ font-size: 14px; font-weight: 600; margin-bottom: 8px; color: var(--text-dim); }}
.back-link {{ display: inline-block; margin-bottom: 16px; font-size: 14px; }}
.footer {{ text-align: center; color: var(--text-muted); font-size: 12px; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); }}
.combo-badges {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
.combo-badge {{ padding: 3px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
.combo-badge.buy-triggered {{ background: var(--green-bg); color: var(--green); border: 1px solid rgba(63,185,80,0.3); }}
.combo-badge.buy-not {{ background: var(--bg); color: var(--text-muted); border: 1px solid var(--border); }}
.combo-badge.sell-triggered {{ background: var(--red-bg); color: var(--red); border: 1px solid rgba(248,81,73,0.3); }}
.combo-badge.sell-not {{ background: var(--bg); color: var(--text-muted); border: 1px solid var(--border); }}
.change-pos {{ color: var(--green); font-weight: 600; }}
.change-neg {{ color: var(--red); font-weight: 600; }}
.judgment {{ font-size: 16px; text-align: center; min-width: 32px; }}
.core-metric-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 14px; }}
.core-metric-table th {{ padding: 8px 12px; text-align: left; color: var(--text-dim); border-bottom: 1px solid var(--border); font-weight: 500; font-size: 14px; }}
.subtitle {{ font-size: 14px; color: var(--text-dim); margin-top: 4px; }}
.headline-sub {{ font-size: 16px; color: var(--yellow); margin-top: 6px; font-weight: 500; }}
</style>
</head>
<body>

<a href="/" class="back-link">← 返回首页</a>
<div class="header">
    <h1>{_esc(inp.company_name)} ({_esc(inp.ticker)}) 深度分析</h1>
    {f'<div class="headline-sub">{_esc(deep_analysis.executive_summary.headline)}</div>' if deep_analysis and deep_analysis.executive_summary else ''}
    <div class="meta">
        <span>报告日期: {d.isoformat()}</span>
        <span>财报期间: {_esc(oe.period)}</span>
        <span class="tag">{_esc(inp.asset_tier)}</span>
        {_render_combo_a_badge(ca)}
    </div>
    <div style="font-size:13px;color:var(--text-dim);margin-top:8px">{_esc(inp.focus)}</div>
</div>

<!-- 核心指标 -->
<div class="data-grid" style="margin-bottom:4px">
    <div class="data-card">
        <div class="label">Owner's Earnings</div>
        <div class="value">{oe.oe:.0f}<small> 亿</small></div>
        <div class="sub">OE Margin {oe.oe_margin_pct:.1f}% | CFO {oe.cfo:.0f} − 维持CapEx {oe.maintenance_capex:.0f}</div>
    </div>
    <div class="data-card">
        <div class="label">可分配净现金</div>
        <div class="value">{oe.distributable_net_cash:.0f}<small> 亿</small></div>
        <div class="sub">可利用资金 {oe.gross_net_cash:.0f} − 扣除 {oe.total_deductions:.0f}</div>
    </div>
    <div class="data-card">
        <div class="label">内在价值 (r={oe.discount_rate:.0%})</div>
        <div class="value">{oe.intrinsic_value:,.0f}<small> 亿港元</small></div>
        <div class="sub">零增长 {oe.zero_growth_value:.0f} + 净现金 {oe.distributable_net_cash:.0f}{f' + 投资 {oe.investment_portfolio_value:.0f}' if oe.investment_portfolio_value else ''}</div>
    </div>
</div>
<div class="data-grid" style="margin-bottom:16px">
    <div class="data-card">
        <div class="label">当前市值</div>
        <div class="value">{oe.market_cap:,.0f}<small> 亿港元</small></div>
        <div class="sub">{'P/E N/A (OE&lt;0)' if oe.oe <= 0 else f'P/E {oe.market_cap/oe.oe:.1f}x'} | 赔率 {oe.odds:.1%}</div>
    </div>
    <div class="data-card">
        <div class="label">安全边际</div>
        <div class="value {margin_class}">{oe.safety_margin_pct:+.1f}%</div>
        <div class="sub">{margin_label} | {_esc(inp.asset_tier)}需赔率 ≥{_odds_threshold(inp.asset_tier)}</div>
    </div>
</div>

{_render_exec_summary(deep_analysis)}

{_render_key_forces(deep_analysis)}

<!-- OE 计算 -->
<div class="section">
    <h2>1. Owner's Earnings 计算</h2>
    <table class="calc-table">
        <tr><td></td><td>经营性现金流 (CFO)</td><td>{oe.cfo:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>维持性资本支出{'  ⚠ 估算' if oe.maintenance_capex_is_estimated else ''}</td><td>{oe.maintenance_capex:.2f} 亿</td></tr>
        <tr class="separator result"><td class="op">=</td><td>Owner's Earnings</td><td>{oe.oe:.2f} 亿</td></tr>
        <tr><td></td><td colspan="2" style="font-size:13px;color:var(--text-dim)">扩张性 Capex {oe.growth_capex:.2f} 亿 (总 {fd.total_capex:.1f} − 维持性 {oe.maintenance_capex:.1f}) | OE Margin {oe.oe_margin_pct:.1f}%</td></tr>
    </table>
    {'<div class="warn-box">⚠ 维持性Capex为估算值: ' + _esc(oe.maintenance_capex_note) + '</div>' if oe.maintenance_capex_is_estimated and oe.maintenance_capex_note else ''}
</div>

<!-- 净现金 -->
<div class="section">
    <h2>2. 净现金（保守口径）</h2>
    <table class="calc-table">
        <tr><td></td><td>现金及等价物</td><td>{fd.cash_and_equivalents:.2f} 亿</td></tr>
        <tr><td class="op">+</td><td>短期理财</td><td>{fd.short_term_investments:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>有息负债</td><td>{fd.interest_bearing_debt:.2f} 亿</td></tr>
        <tr class="separator"><td class="op">=</td><td>毛净现金</td><td><strong>{oe.gross_net_cash:.2f} 亿</strong></td></tr>
    </table>
    <table class="calc-table" style="margin-top:12px">
        <tr><td class="op">−</td><td>运营储备 (1.5月营收)</td><td>{oe.operating_reserve:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>已承诺投资款</td><td>{fd.committed_investments:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>受限资金</td><td>{fd.restricted_cash:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>海外现金回流折扣 (15%)</td><td>{fd.overseas_cash * 0.15:.2f} 亿</td></tr>
        <tr class="separator result"><td class="op">=</td><td>可分配净现金</td><td>{oe.distributable_net_cash:.2f} 亿</td></tr>
    </table>
    {'<div class="portfolio-box"><div class="portfolio-title">投资组合（保守 ' + f'{oe.investment_discount_rate:.0%}' + ' 折扣）</div><table class="calc-table"><tr><td></td><td>上市投资公允价值</td><td>' + f'{fd.listed_investments_fv:.2f}' + ' 亿</td></tr><tr><td class="op">+</td><td>非上市投资账面价值</td><td>' + f'{fd.unlisted_investments_bv:.2f}' + ' 亿</td></tr><tr class="separator"><td class="op">=</td><td>投资组合总值</td><td>' + f'{oe.investment_portfolio_gross:.2f}' + ' 亿</td></tr><tr class="separator result"><td class="op">×</td><td>(1 − ' + f'{oe.investment_discount_rate:.0%}' + ') 折扣后</td><td>' + f'{oe.investment_portfolio_value:.2f}' + ' 亿</td></tr></table></div>' if oe.investment_portfolio_gross > 0 else ''}
</div>

<!-- 估值 -->
<div class="section">
    <h2>3. 零增长估值与安全边际</h2>
    <table class="calc-table">
        <tr><td></td><td>零增长估值 = OE / r</td><td>{oe.oe:.1f} / {oe.discount_rate:.0%} = {oe.zero_growth_value:.2f} 亿</td></tr>
        <tr><td class="op">+</td><td>可分配净现金</td><td>{oe.distributable_net_cash:.2f} 亿</td></tr>
        {'<tr><td class="op">+</td><td>投资组合 (折扣后)</td><td>' + f'{oe.investment_portfolio_value:.2f}' + ' 亿</td></tr>' if oe.investment_portfolio_value else ''}
        <tr class="separator result"><td class="op">=</td><td>内在价值</td><td>{oe.intrinsic_value:.2f} 亿</td></tr>
        <tr><td class="op">−</td><td>当前市值</td><td>{oe.market_cap:.2f} 亿</td></tr>
        <tr class="separator result"><td class="op">=</td><td>安全边际</td><td class="{margin_class}">{oe.safety_margin:+.2f} 亿 ({oe.safety_margin_pct:+.1f}%)</td></tr>
    </table>
    <h3 style="font-size:15px;margin-top:20px;margin-bottom:4px;color:var(--text-dim)">三情景估值对比</h3>
    <table class="sens-table">
        <tr><th style="text-align:left">情景</th><th>OE</th><th>内在价值</th><th>安全边际</th></tr>
        {''.join(f'<tr class="{"current" if s.name == "中性" else ""}"><td style="text-align:left">{"★ " if s.name == "中性" else ""}{s.name}</td><td>{s.oe.oe:.0f}</td><td>{s.intrinsic_value:.0f}</td><td class="{"positive" if s.safety_margin_pct > 0 else "negative"}">{s.safety_margin_pct:+.1f}%</td></tr>' for s in scenarios)}
    </table>
    <div style="font-size:12px;color:var(--text-muted);margin-top:8px">
        保守: r=12%零增长,Capex×1.2 · 中性: r=10%零增长,当前OE · 乐观: r=8%,g=5%,Capex×0.9
    </div>
</div>

{_render_revenue_section(deep_analysis)}

{_render_profitability_section(deep_analysis)}

{_render_core_products(deep_analysis)}

{_render_kpi_section(kpi)}

{_render_capex_sim_section(capex_sim, deep_analysis.capex_warning if deep_analysis else '')}

{_render_competition_section(deep_analysis)}

{_render_mgmt_section(mgmt)}

{_render_variant_section(variant)}

{_render_philosophies_section(deep_analysis)}

{_render_premortem_section(deep_analysis)}

<!-- Combo A -->
<div class="section">
    <h2>Combo A · 估值安全边际型 [{ca.triggered_count}/{ca.total_count}] {"✅ 触发" if ca.triggered else "❌ 未触发"}</h2>
    {combo_rows}
    {missing_html}
</div>

{_render_combo_signals(deep_analysis)}

<!-- 决策 -->
<div class="section">
    <h2>仓位决策</h2>
    <div class="score-bar">
        <div class="score-item">
            <div class="score-label">胜率</div>
            <div class="score-value">{m.win_rate_score}<small style="font-size:16px;color:var(--text-dim)">/5</small></div>
            <div class="score-label">{_esc(m.win_rate_level)}胜率</div>
        </div>
        <div class="score-item" style="font-size:36px;color:var(--text-muted);padding-top:20px">×</div>
        <div class="score-item">
            <div class="score-label">赔率</div>
            <div class="score-value">{m.odds_score}<small style="font-size:16px;color:var(--text-dim)">/5</small></div>
            <div class="score-label">{_esc(m.odds_level)}赔率</div>
        </div>
    </div>
    <div class="decision-box {action_class}">
        <div class="action">{_esc(m.action)}</div>
        <div class="position">建议仓位: {_esc(m.position_range)}</div>
    </div>
    <div class="reasoning">{_esc(m.reasoning)}</div>
</div>

<!-- 后续跟踪 -->
<div class="section">
    <h2>6. 后续跟踪要点</h2>
    <ul class="next-steps">
        {_next_steps_html(inp)}
    </ul>
</div>

<div class="footer">
    港股财报分析工具 · 基于李录 Owner's Earnings 框架 · 数据来源: 公司财报原文 > 港交所公告 > 管理层业绩会纪要
</div>

</body>
</html>"""


def _render_exec_summary(deep: DeepAnalysis | None) -> str:
    if deep is None or deep.executive_summary is None:
        return ""
    es = deep.executive_summary
    tldr = "".join(f"<li>{_esc(t)}</li>" for t in es.tldr)
    return f"""<div class="section">
    <h2>Executive Summary</h2>
    <div style="background:var(--blue-bg);color:var(--blue);display:inline-block;padding:4px 16px;border-radius:20px;font-weight:600;font-size:14px;margin-bottom:16px">建议动作: {_esc(es.action)}</div>
    <div style="font-size:14px;color:var(--text);line-height:1.8;white-space:pre-line;margin-bottom:16px">{_esc(es.body)}</div>
    <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px 16px">
        <div style="font-weight:600;color:var(--blue);margin-bottom:6px">TL;DR:</div>
        <ul style="font-size:14px;padding-left:16px;display:flex;flex-direction:column;gap:4px">{tldr}</ul>
    </div>
</div>"""


def _render_key_forces(deep: DeepAnalysis | None) -> str:
    if deep is None or not deep.key_forces:
        return ""
    kf_html = ""
    for kf in deep.key_forces:
        kf_html += f"""<div style="background:var(--bg);border-left:3px solid var(--blue);border-radius:8px;padding:12px 16px;margin-bottom:8px">
            <div style="font-weight:600;color:var(--blue)">{_esc(kf.title)}</div>
            <div style="font-size:13px;margin-top:4px">{_esc(kf.body)}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">OE含义: {_esc(kf.oe_implication)}</div>
        </div>"""
    return f"""<div class="section">
    <h2>Key Forces（决定性力量）</h2>
    {kf_html}
</div>"""


def _render_revenue_section(deep: DeepAnalysis | None) -> str:
    if deep is None or not deep.revenue_breakdown or not deep.revenue_breakdown.segments:
        return ""
    # Check if quarterly data exists
    has_quarterly = any(s.get('q1') for s in deep.revenue_breakdown.segments)
    q_headers = '<th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th>' if has_quarterly else ''

    rows = ""
    total_fy = 0
    for s in deep.revenue_breakdown.segments:
        yoy_cls = _change_color_class(str(s.get('yoy', '')))
        fy_val = s.get('fy2025', '')
        # Try to accumulate total
        try:
            total_fy += float(fy_val) if isinstance(fy_val, (int, float)) else 0
        except (ValueError, TypeError):
            pass
        q_cols = ''
        if has_quarterly:
            q_cols = f"<td>{s.get('q1','')}</td><td>{s.get('q2','')}</td><td>{s.get('q3','')}</td><td>{s.get('q4','')}</td>"
        rows += f"<tr><td style='text-align:left'>{_esc(str(s.get('name','')))}</td><td>{fy_val}</td><td class='{yoy_cls}'>{_esc(str(s.get('yoy','')))}</td><td>{_esc(str(s.get('share','')))}</td>{q_cols}<td style='font-size:12px;color:var(--text-dim)'>{_esc(str(s.get('trend','')))}</td></tr>"

    # Totals row
    total_row = ''
    if total_fy > 0:
        q_empty = '<td></td><td></td><td></td><td></td>' if has_quarterly else ''
        total_row = f'<tr style="font-weight:700;border-top:2px solid var(--border)"><td style="text-align:left">合计</td><td>{total_fy:.1f}</td><td></td><td>100%</td>{q_empty}<td></td></tr>'

    warn = f'<div class="warn-box">{_esc(deep.revenue_breakdown.warning)}</div>' if deep.revenue_breakdown.warning else ''
    return f"""<div class="section">
    <h2>收入拆分</h2>
    <table class="sens-table">
        <tr><th style="text-align:left">业务线</th><th>FY2025(亿)</th><th>同比</th><th>占比</th>{q_headers}<th style="text-align:left">趋势</th></tr>
        {rows}
        {total_row}
    </table>
    {warn}
</div>"""


def _render_profitability_section(deep: DeepAnalysis | None) -> str:
    if deep is None or not deep.profitability or not deep.profitability.metrics:
        return ""
    rows = ""
    for m in deep.profitability.metrics:
        change_str = str(m.get('change', ''))
        change_cls = _change_color_class(change_str)
        rows += f"<tr><td style='text-align:left'>{_esc(str(m.get('name','')))}</td><td>{m.get('fy2024','')}</td><td>{m.get('fy2025','')}</td><td class='{change_cls}'>{_esc(change_str)}</td></tr>"
    insight = f'<div style="margin-top:12px;font-size:13px;color:var(--text-dim)">💡 {_esc(deep.profitability.insight)}</div>' if deep.profitability.insight else ""
    return f"""<div class="section">
    <h2>盈利能力趋势</h2>
    <table class="sens-table">
        <tr><th style="text-align:left">指标</th><th>FY2024</th><th>FY2025</th><th>变化</th></tr>
        {rows}
    </table>
    {insight}
</div>"""


def _render_capex_sim_section(capex_sim, capex_warning: str = '') -> str:
    if not capex_sim:
        return ""
    rows = ""
    for s in capex_sim:
        oe_cls = "positive" if s.oe > 0 else "negative"
        fcf_cls = "positive" if s.fcf > 0 else "negative"
        rows += f"<tr><td style='text-align:left'>{_esc(s.label)}</td><td>{s.cfo:.0f}</td><td>{s.total_capex:.0f}</td><td>{s.maintenance_capex:.0f}</td><td class='{oe_cls}'>{s.oe:.0f}</td><td class='{fcf_cls}'>{s.fcf:.0f}</td></tr>"
    warn = f'<div class="warn-box">{_esc(capex_warning)}</div>' if capex_warning else ''
    return f"""<div class="section">
    <h2>CapEx 冲击模拟</h2>
    <table class="sens-table">
        <tr><th style="text-align:left">场景</th><th>CFO</th><th>总Capex</th><th>维持性</th><th>OE</th><th>FCF</th></tr>
        {rows}
    </table>
    <div style="font-size:12px;color:var(--text-muted);margin-top:8px">基准: CFO温和增长+Capex持平 · 悲观: CFO不增长+Capex大幅增长</div>
    {warn}
</div>"""


def _render_competition_section(deep: DeepAnalysis | None) -> str:
    if deep is None or not deep.competition or not deep.competition.dimensions:
        return ""
    d0 = deep.competition.dimensions[0]
    rows = ""
    for d in deep.competition.dimensions:
        rows += f"<tr><td style='text-align:left'>{_esc(str(d.get('metric','')))}</td><td>{_esc(str(d.get('company_value','')))}</td><td>{_esc(str(d.get('comp1_value','')))}</td><td>{_esc(str(d.get('comp2_value','')))}</td></tr>"
    moat = f'<div style="margin-top:12px;padding:12px;background:var(--bg);border-radius:8px;font-size:13px"><strong>护城河评估:</strong> {_esc(deep.competition.moat_assessment)}</div>' if deep.competition.moat_assessment else ""
    return f"""<div class="section">
    <h2>竞争格局</h2>
    <table class="sens-table">
        <tr><th style="text-align:left">维度</th><th>本公司</th><th>{_esc(str(d0.get('comp1_name','竞对1')))}</th><th>{_esc(str(d0.get('comp2_name','竞对2')))}</th></tr>
        {rows}
    </table>
    {moat}
</div>"""


def _render_philosophies_section(deep: DeepAnalysis | None) -> str:
    if deep is None or not deep.philosophies:
        return ""
    verdict_map = {"看多": ("🟢", "positive"), "轻多": ("🟡", ""), "观望": ("⚪", "text-dim"), "看空": ("🔴", "negative")}
    rows = ""
    for p in deep.philosophies:
        icon, cls = verdict_map.get(p.verdict, ("⚪", "text-dim"))
        rows += f"""<div style="display:flex;gap:12px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--border)">
            <div style="font-size:20px;min-width:28px">{icon}</div>
            <div style="flex:1">
                <div><span class="{cls}" style="font-weight:700">{_esc(p.verdict)}</span> <span style="font-weight:600">{_esc(p.name)}</span> <span style="color:var(--text-muted);font-size:13px">({_esc(p.representative)})</span></div>
                <div style="font-size:13px;color:var(--text-dim);margin-top:2px">{_esc(p.reasoning)}</div>
            </div>
        </div>"""
    return f"""<div class="section">
    <h2>6大投资哲学视角</h2>
    {rows}
</div>"""


def _render_premortem_section(deep: DeepAnalysis | None) -> str:
    if deep is None or deep.pre_mortem is None:
        return ""
    pm = deep.pre_mortem
    paths = "".join(f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border)"><span style="font-size:14px">{_esc(fp.get("description",""))}</span><span style="color:var(--yellow);font-weight:600;min-width:40px;text-align:right">{_esc(str(fp.get("probability","")))}</span></div>' for fp in pm.failure_paths)
    biases = "".join(f'<tr><td style="text-align:left;font-weight:600">{_esc(str(cb.get("bias","")))}</td><td style="text-align:left;color:var(--red)">{_esc(str(cb.get("risk","")))}</td><td style="text-align:left;color:var(--green)">{_esc(str(cb.get("check","")))}</td></tr>' for cb in pm.cognitive_biases)
    return f"""<div class="section">
    <h2>Pre-Mortem & Anti-Bias</h2>
    <div style="background:var(--red-bg);border-radius:8px;padding:16px;margin-bottom:16px">
        <div style="font-weight:600;color:var(--red);margin-bottom:12px">{_esc(pm.failure_scenario)}</div>
        {paths}
    </div>
    <div style="font-weight:600;margin-bottom:8px">认知偏差自检</div>
    <table class="sens-table">
        <tr><th style="text-align:left">偏差</th><th style="text-align:left">风险</th><th style="text-align:left">检查</th></tr>
        {biases}
    </table>
</div>"""


def _esc(s: str) -> str:
    """HTML 转义"""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _render_kpi_section(kpi: KPIDashboard | None) -> str:
    if kpi is None:
        return ""
    rows = ""
    for k in kpi.kpis:
        trend_cls = "positive" if k.is_positive else "negative"
        val = f"{k.current}" if isinstance(k.current, str) else f"{k.current:g}"
        rows += f"""<tr>
            <td style="text-align:left">{_esc(k.name)}</td>
            <td class="{trend_cls}">{val}{_esc(k.unit)} {k.trend}</td>
            <td style="font-size:12px;color:var(--text-dim)">{_esc(k.note)}</td>
        </tr>"""

    highlights = "".join(f'<li style="color:var(--green)">{_esc(h)}</li>' for h in kpi.highlights)
    concerns = "".join(f'<li style="color:var(--yellow)">{_esc(c)}</li>' for c in kpi.concerns)

    return f"""<div class="section">
    <h2>核心 KPI 仪表盘 · {_esc(kpi.business_type)}</h2>
    <table class="sens-table">
        <tr><th style="text-align:left">指标</th><th>当前值</th><th style="text-align:left">说明</th></tr>
        {rows}
    </table>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px">
        <div style="background:var(--green-bg);border-radius:8px;padding:12px">
            <div style="font-weight:600;color:var(--green);margin-bottom:8px">核心发现</div>
            <ul style="font-size:13px;padding-left:16px">{highlights}</ul>
        </div>
        <div style="background:var(--yellow-bg);border-radius:8px;padding:12px">
            <div style="font-weight:600;color:var(--yellow);margin-bottom:8px">核心隐忧</div>
            <ul style="font-size:13px;padding-left:16px">{concerns}</ul>
        </div>
    </div>
</div>"""


def _render_mgmt_section(mgmt: ManagementSignals | None) -> str:
    if mgmt is None:
        return ""

    guidance_rows = ""
    for g in mgmt.guidance_track:
        icon = "✅" if g.hit else "❌"
        guidance_rows += f"<tr><td>{icon}</td><td>{_esc(g.metric)}</td><td>{_esc(g.guidance)}</td><td>{_esc(g.actual)}</td></tr>"

    actions_html = ""
    for a in mgmt.insider_actions:
        sig_cls = "positive" if a.signal == "正面" else ("negative" if a.signal == "负面" else "text-dim")
        actions_html += f'<div style="margin-bottom:8px"><span class="{sig_cls}" style="font-weight:600">{_esc(a.action_type)}</span> {_esc(a.amount)} ({_esc(a.period)}) — {_esc(a.detail)}</div>'

    flags_html = ""
    if mgmt.red_flags:
        flags = "".join(f"<li>{_esc(f)}</li>" for f in mgmt.red_flags)
        flags_html = f'<div class="warn-box" style="margin-top:12px"><div style="font-weight:600">⚠ 风险信号</div><ul style="padding-left:16px;margin-top:4px">{flags}</ul></div>'

    return f"""<div class="section">
    <h2>管理层信号</h2>
    {f'<table class="sens-table"><tr><th></th><th style="text-align:left">指标</th><th style="text-align:left">指引</th><th style="text-align:left">实际</th></tr>{guidance_rows}</table>' if guidance_rows else '<div style="color:var(--text-muted)">管理层未提供前瞻指引</div>'}
    <div style="margin-top:8px;font-size:13px;color:var(--text-dim)">指引可信度: {_esc(mgmt.guidance_credibility)}</div>
    {f'<div style="margin-top:16px"><div style="font-weight:600;margin-bottom:8px">内部人行为</div>{actions_html}</div>' if actions_html else ''}
    <div style="margin-top:16px;padding:12px;background:var(--bg);border-radius:8px">
        <div style="font-size:13px;color:var(--text-dim)"><strong>资本配置:</strong> {_esc(mgmt.capital_allocation_summary)}</div>
        <div style="font-size:13px;color:var(--text-dim);margin-top:8px"><strong>业绩会 tone:</strong> {_esc(mgmt.tone_summary)}</div>
        {f'<div style="font-size:13px;color:var(--blue);margin-top:4px">vs 上期: {_esc(mgmt.tone_shift)}</div>' if mgmt.tone_shift else ''}
    </div>
    {flags_html}
</div>"""


def _render_variant_section(variant: VariantView | None) -> str:
    if variant is None:
        return ""

    debates = "".join(f"<li>{_esc(d)}</li>" for d in variant.key_debates)
    catalysts = "".join(f'<li style="color:var(--green)">{_esc(c)}</li>' for c in variant.catalysts)
    anti_catalysts = "".join(f'<li style="color:var(--red)">{_esc(c)}</li>' for c in variant.anti_catalysts)
    kills = "".join(f"<li>{_esc(k)}</li>" for k in variant.kill_conditions)

    return f"""<div class="section">
    <h2>Variant View — 市场共识 vs 我们的判断</h2>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div style="background:var(--bg);border-radius:8px;padding:16px;border-left:3px solid var(--text-dim)">
            <div style="font-weight:600;color:var(--text-dim);margin-bottom:8px">市场共识</div>
            <div style="font-size:14px">{_esc(variant.consensus)}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:8px">{_esc(variant.consensus_implied_growth)}</div>
        </div>
        <div style="background:var(--bg);border-radius:8px;padding:16px;border-left:3px solid var(--blue)">
            <div style="font-weight:600;color:var(--blue);margin-bottom:8px">我们的判断</div>
            <div style="font-size:14px">{_esc(variant.our_view)}</div>
        </div>
    </div>
    <div style="background:var(--yellow-bg);border-radius:8px;padding:16px;margin-top:16px">
        <div style="font-weight:600;color:var(--yellow);margin-bottom:8px">市场错在哪</div>
        <div style="font-size:14px">{_esc(variant.why_market_wrong)}</div>
    </div>
    <div style="margin-top:16px"><div style="font-weight:600;margin-bottom:8px">关键分歧</div><ul style="font-size:14px;padding-left:16px">{debates}</ul></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px">
        <div><div style="font-weight:600;color:var(--green);margin-bottom:8px">正面催化剂</div><ul style="font-size:13px;padding-left:16px">{catalysts}</ul></div>
        <div><div style="font-weight:600;color:var(--red);margin-bottom:8px">负面催化剂</div><ul style="font-size:13px;padding-left:16px">{anti_catalysts}</ul></div>
    </div>
    <div class="warn-box" style="margin-top:16px">
        <div style="font-weight:600">Kill Conditions — 论点证伪条件</div>
        <ul style="padding-left:16px;margin-top:4px;font-size:14px">{kills}</ul>
    </div>
</div>"""


def _next_steps_html(inp: ReportInput) -> str:
    oe = inp.oe_result
    m = inp.matrix_result
    items = []
    if m.action == "不参与":
        target_mcap = oe.intrinsic_value / 1.70
        items.append(f"赔率达标: 需市值降至 {target_mcap:.0f} 亿以下（当前 {oe.market_cap:.0f} 亿）")
        items.append(f"或 OE 提升: 需 OE 从 {oe.oe:.0f} 亿提升至使内在价值覆盖 70% 赔率")
        items.append("关注下季财报是否出现 Combo B（基本面拐点）信号")
    else:
        items.append(f"已达建仓条件 ({m.action})，执行前写入核心假设至 data/assumptions/{inp.company_name}.md")
        items.append("设定止损: 关注 Combo H（逻辑证伪）触发条件")
        items.append("设定止盈: 关注 Combo E（估值透支）触发条件")
    return "".join(f"<li>{_esc(item)}</li>" for item in items)


def _odds_threshold(asset_tier: str) -> str:
    """Return odds threshold string for display."""
    return {"顶级资产": "40%", "中等质量": "70%", "高波动": "100%"}.get(asset_tier, "70%")


def _render_combo_a_badge(ca) -> str:
    """Render Combo A status as inline tag in header meta."""
    cls = "combo-a-triggered" if ca.triggered else "combo-a-not"
    bg = "var(--green-bg)" if ca.triggered else "var(--yellow-bg)"
    color = "var(--green)" if ca.triggered else "var(--yellow)"
    label = "触发" if ca.triggered else "未触发"
    return f'<span style="background:{bg};color:{color};padding:2px 10px;border-radius:12px;font-size:13px;font-weight:600">Combo A {ca.triggered_count}/{ca.total_count} {label}</span>'


def _change_color_class(change_str: str) -> str:
    """Determine CSS class for change/YoY columns: green for positive, red for negative."""
    s = change_str.strip()
    if not s:
        return ""
    # Explicit positive indicators
    if "✓" in s or "✅" in s:
        return "change-pos"
    # Explicit negative indicators
    if "⚠" in s or "❌" in s:
        return "change-neg"
    # Check sign: starts with + or contains positive growth
    if s.startswith("+"):
        return "change-pos"
    if s.startswith("-"):
        return "change-neg"
    return ""


# Buy combos: A, B, C, D1, D2. Sell combos: E, F, G, H, I, J
_SELL_COMBOS = {"Combo E", "Combo F", "Combo G", "Combo H", "Combo I", "Combo J"}


def _render_combo_badges(ca, deep_analysis) -> str:
    """Render combo status badges in header area."""
    badges = []
    # Combo A badge from scan result
    a_cls = "buy-triggered" if ca.triggered else "buy-not"
    badges.append(f'<span class="combo-badge {a_cls}">A·估值安全边际 [{ca.triggered_count}/{ca.total_count}]</span>')

    # Additional combo badges from deep_analysis
    if deep_analysis and deep_analysis.combo_signals:
        for cs in deep_analysis.combo_signals:
            is_sell = any(cs.name.startswith(s) for s in _SELL_COMBOS)
            if cs.triggered:
                cls = "sell-triggered" if is_sell else "buy-triggered"
            else:
                cls = "sell-not" if is_sell else "buy-not"
            short_name = cs.name.split("·")[0].strip() if "·" in cs.name else cs.name
            badges.append(f'<span class="combo-badge {cls}">{_esc(cs.name)} [{_esc(cs.count)}]</span>')

    if not badges:
        return ""
    return f'<div class="combo-badges">{"".join(badges)}</div>'


def _render_combo_signals(deep: DeepAnalysis | None) -> str:
    """Render full Combo B-J signal details."""
    if deep is None or not deep.combo_signals:
        return ""
    sections = ""
    for cs in deep.combo_signals:
        status = "✅ 触发" if cs.triggered else "❌ 未触发"
        rows = ""
        for sc in cs.sub_conditions:
            triggered = sc.get("triggered", False)
            icon = "check" if triggered else "cross"
            cls = "triggered" if triggered else "not-triggered"
            detail = sc.get("detail", "")
            rows += f"""
            <div class="condition {cls}">
                <div class="condition-header">
                    <span class="icon-{icon}"></span>
                    <span class="condition-name">{_esc(sc.get('name', ''))}</span>
                </div>
                <div class="condition-detail">{_esc(detail)}</div>
            </div>"""
        sections += f"""
<div class="section">
    <h2>{_esc(cs.name)} [{_esc(cs.count)}] {status}</h2>
    {rows}
</div>"""
    return sections


def _render_core_products(deep: DeepAnalysis | None) -> str:
    """Render core product analysis sections."""
    if deep is None or not deep.core_products:
        return ""
    judgment_map = {"正面": "🟢", "负面": "🔴", "中性": "🟡", "观察": "⚪"}
    sections = ""
    for cp in deep.core_products:
        rows = ""
        for m in cp.metrics:
            j_emoji = judgment_map.get(m.get("judgment", ""), "⚪")
            rows += f"""<tr>
                <td>{_esc(str(m.get('metric', '')))}</td>
                <td style="font-weight:600">{_esc(str(m.get('value', '')))}</td>
                <td class="judgment">{j_emoji}</td>
                <td style="font-size:12px;color:var(--text-dim)">{_esc(str(m.get('note', '')))}</td>
            </tr>"""
        insight_html = f'<div style="margin-top:12px;font-size:13px;color:var(--text-dim)">💡 {_esc(cp.insight)}</div>' if cp.insight else ''
        sections += f"""
<div class="section">
    <h2>{_esc(cp.name)} — {_esc(cp.subtitle)}</h2>
    <table class="core-metric-table" style="width:100%;border-collapse:collapse">
        <tr><th>指标</th><th>数值</th><th style="text-align:center">判断</th><th>备注</th></tr>
        {rows}
    </table>
    {insight_html}
</div>"""
    return sections
