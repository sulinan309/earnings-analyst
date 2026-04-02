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
from src.output.report_generator import ReportInput


def generate_html(inp: ReportInput) -> str:
    """生成完整的 HTML 报告"""
    oe = inp.oe_result
    fd = inp.financial_data
    ca = inp.combo_a
    m = inp.matrix_result
    d = inp.report_date or date.today()

    scenarios = OECalculator(discount_rate=0.10).scenario_analysis(fd)
    kpi = get_kpi_dashboard(inp.ticker)
    mgmt = get_management_signals(inp.ticker)
    variant = get_variant_view(inp.ticker)

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
</style>
</head>
<body>

<a href="/" class="back-link">← 返回首页</a>
<div class="header">
    <h1>{_esc(inp.company_name)} ({_esc(inp.ticker)})</h1>
    <div class="meta">
        <span>报告日期: {d.isoformat()}</span>
        <span>财报期间: {_esc(oe.period)}</span>
        <span class="tag">{_esc(inp.asset_tier)}</span>
        <span>{_esc(inp.focus)}</span>
    </div>
</div>

<!-- 核心指标 -->
<div class="data-grid">
    <div class="data-card">
        <div class="label">Owner's Earnings</div>
        <div class="value">{oe.oe:.1f}<small> 亿</small></div>
        <div class="sub">OE Margin {oe.oe_margin_pct:.1f}%</div>
    </div>
    <div class="data-card">
        <div class="label">可分配净现金</div>
        <div class="value">{oe.distributable_net_cash:.1f}<small> 亿</small></div>
        <div class="sub">毛净现金 {oe.gross_net_cash:.1f} - 扣除 {oe.total_deductions:.1f}</div>
    </div>
    <div class="data-card">
        <div class="label">内在价值</div>
        <div class="value">{oe.intrinsic_value:.1f}<small> 亿</small></div>
        <div class="sub">零增长 {oe.zero_growth_value:.1f} + 净现金 {oe.distributable_net_cash:.1f}{f' + 投资 {oe.investment_portfolio_value:.1f}' if oe.investment_portfolio_value else ''}</div>
    </div>
    <div class="data-card">
        <div class="label">安全边际</div>
        <div class="value {margin_class}">{oe.safety_margin_pct:+.1f}%</div>
        <div class="sub">{margin_label} | 赔率 {oe.odds:.1%}</div>
    </div>
</div>

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

{_render_kpi_section(kpi)}

{_render_mgmt_section(mgmt)}

{_render_variant_section(variant)}

<!-- Combo A -->
<div class="section">
    <h2>Combo A · 估值安全边际型 [{ca.triggered_count}/{ca.total_count}] {"✅ 触发" if ca.triggered else "❌ 未触发"}</h2>
    {combo_rows}
    {missing_html}
</div>

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
