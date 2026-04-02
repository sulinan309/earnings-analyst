"""腾讯 FY2025 深度分析 V2 — 自动分析管线

程序化模块 + AI叙事(或模板兜底) → 完整报告
"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.frameworks.auto_analysis import run_full_analysis, CompanyProfile, FullAnalysisResult
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput

FX = 1.1

def cnb(v): return round(v * FX, 2)
def cnm(v): return round(v * FX / 100, 2)


# ── 腾讯财务数据（从 tencent.pdf 提取）──

financial_data = FinancialData(
    cfo=cnb(2618), maintenance_capex=cnb(550), total_capex=cnb(792),
    cash_and_equivalents=cnm(141_041),
    short_term_investments=cnm(236_801 + 70_302),
    interest_bearing_debt=cnm(42_618 + 10_542 + 208_369 + 126_204),
    committed_investments=100.0, restricted_cash=cnm(6_977),
    overseas_cash=200.0, revenue=cnb(7518), market_cap=42000.0,
    listed_investments_fv=cnb(6727), unlisted_investments_bv=cnb(3631),
    investment_discount=0.50,
    period="FY2025", ticker="0700.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="附注未拆分，以折旧摊销~500亿上浮至550亿作为保守估计",
)


# ── 腾讯公司档案（业务结构+竞争格局）──

profile = CompanyProfile(
    name="腾讯", ticker="0700.HK", asset_tier="顶级资产", period="FY2025",

    revenue_segments=[
        {"name": "增值服务(游戏+社交)", "fy2025": cnb(3693), "yoy": "+16%", "share": "49%",
         "trend": "国内游戏+18%,国际+33%,社交+5%"},
        {"name": "营销服务(广告)", "fy2025": cnb(1450), "yoy": "+19%", "share": "19%",
         "trend": "AI驱动广告定向+视频号商业化"},
        {"name": "金融科技及企业服务", "fy2025": cnb(2294), "yoy": "+8%", "share": "31%",
         "trend": "云+~20%(AI需求),支付高个位数"},
        {"name": "其他", "fy2025": cnb(81), "yoy": "-", "share": "1%", "trend": "-"},
    ],

    profitability_metrics=[
        {"name": "毛利率", "fy2024": "53.0%", "fy2025": "56.2%", "change": "+3.2pct"},
        {"name": "Non-IFRS经营利润率", "fy2024": "36%", "fy2025": "37%", "change": "+1.0pct"},
        {"name": "IFRS经营利润率", "fy2024": "32%", "fy2025": "32%", "change": "持平"},
        {"name": "Non-IFRS净利润", "fy2024": cnb(2227), "fy2025": cnb(2596), "change": "+17%"},
        {"name": "GAAP vs Non-GAAP差异", "fy2024": "~15%", "fy2025": "~15%",
         "change": "SBC+投资收益调整,差异稳定"},
    ],
    profitability_insight="毛利率+3.2pct是最大亮点，反映AI提效+高毛利广告占比提升。Non-IFRS利润率37%创新高。GAAP vs Non-GAAP差异稳定在~15%，主要来自SBC和投资公允价值变动，可接受。",

    competition_dims=[
        {"metric": "总收入(亿)", "company_value": str(cnb(7518)), "comp1_name": "阿里", "comp1_value": "~10,960", "comp2_name": "字节(参考)", "comp2_value": "~12,000+"},
        {"metric": "游戏收入", "company_value": str(cnb(2416)), "comp1_name": "网易", "comp1_value": "~900", "comp2_name": "米哈游", "comp2_value": "~300+"},
        {"metric": "广告收入", "company_value": str(cnb(1450)), "comp1_name": "字节", "comp1_value": "~6,000+", "comp2_name": "快手", "comp2_value": str(cnb(815))},
        {"metric": "云收入", "company_value": "~500亿+", "comp1_name": "阿里云", "comp1_value": "~1,100亿", "comp2_name": "华为云", "comp2_value": "~700亿+"},
        {"metric": "FCF", "company_value": str(cnb(1826)), "comp1_name": "阿里", "comp1_value": "FCF为负", "comp2_name": "PDD", "comp2_value": str(cnb(1069))},
    ],
    moat_assessment="微信生态是中国互联网最强护城河——13.8亿月活+支付+小程序+视频号形成闭环。游戏IP储备(王者/和平)和全球化投资组合(Supercell/Riot/Epic)是第二护城河。AI是加速器而非护城河本身。",

    capex_cfo_growth=0.08,      # 腾讯CFO增速~8%
    capex_growth_base=0.10,     # Capex基准增10%(AI持续投入)
    capex_growth_bear=0.40,     # 悲观: Capex再增40%
)


# ── 运行完整分析管线 ──

print("=" * 70)
print("  腾讯 (0700.HK) FY2025 深度分析 V2")
print("=" * 70)

result = run_full_analysis(financial_data, profile)
deep = result.deep

# ── 输出 ──

print(f"\n数据源: {result.data_source}")

# Executive Summary
es = deep.executive_summary
print(f"\n{'─'*70}")
print(f"  {es.headline}")
print(f"{'─'*70}")
print(f"\n建议动作: {es.action}")
print(f"\nTL;DR:")
for t in es.tldr:
    print(f"  • {t}")
print(f"\n{es.body}")

# Key Forces
print(f"\n{'─'*70}")
print("  Key Forces（决定性力量）")
print(f"{'─'*70}")
for kf in deep.key_forces:
    print(f"\n  {kf.title}")
    print(f"  {kf.body}")
    print(f"  OE含义: {kf.oe_implication}")

# 收入拆分
if deep.revenue_breakdown and deep.revenue_breakdown.segments:
    print(f"\n{'─'*70}")
    print("  收入拆分")
    print(f"{'─'*70}")
    print(f"  {'业务线':<25} {'FY2025':>10} {'同比':>8} {'占比':>6} 趋势")
    print(f"  {'─'*65}")
    for s in deep.revenue_breakdown.segments:
        print(f"  {s['name']:<25} {s['fy2025']:>10} {s['yoy']:>8} {s['share']:>6} {s['trend']}")

# 盈利趋势
if deep.profitability and deep.profitability.metrics:
    print(f"\n{'─'*70}")
    print("  盈利能力趋势")
    print(f"{'─'*70}")
    print(f"  {'指标':<25} {'FY2024':>12} {'FY2025':>12} {'变化':>10}")
    print(f"  {'─'*60}")
    for m in deep.profitability.metrics:
        print(f"  {m['name']:<25} {str(m['fy2024']):>12} {str(m['fy2025']):>12} {m['change']:>10}")
    if deep.profitability.insight:
        print(f"\n  💡 {deep.profitability.insight}")

# 竞争格局
if deep.competition and deep.competition.dimensions:
    print(f"\n{'─'*70}")
    print("  竞争格局")
    print(f"{'─'*70}")
    d0 = deep.competition.dimensions[0]
    print(f"  {'维度':<15} {'腾讯':>12} {d0['comp1_name']:>12} {d0['comp2_name']:>12}")
    print(f"  {'─'*55}")
    for d in deep.competition.dimensions:
        print(f"  {d['metric']:<15} {d['company_value']:>12} {d['comp1_value']:>12} {d['comp2_value']:>12}")
    print(f"\n  护城河: {deep.competition.moat_assessment}")

# CapEx 模拟
print(f"\n{'─'*70}")
print("  CapEx 冲击模拟")
print(f"{'─'*70}")
print(f"  {'场景':<15} {'CFO':>10} {'总Capex':>10} {'维持性':>10} {'OE':>10} {'FCF':>10}")
print(f"  {'─'*65}")
for s in result.capex_sim:
    oe_color = "\033[32m" if s.oe > 0 else "\033[31m"
    fcf_color = "\033[32m" if s.fcf > 0 else "\033[31m"
    print(f"  {s.label:<15} {s.cfo:>10.0f} {s.total_capex:>10.0f} {s.maintenance_capex:>10.0f} {oe_color}{s.oe:>10.0f}\033[0m {fcf_color}{s.fcf:>10.0f}\033[0m")

# 6大投资哲学
print(f"\n{'─'*70}")
print("  6大投资哲学视角")
print(f"{'─'*70}")
for p in deep.philosophies:
    verdict_map = {"看多": "🟢", "轻多": "🟡", "观望": "⚪", "看空": "🔴"}
    icon = verdict_map.get(p.verdict, "⚪")
    print(f"  {icon} {p.verdict:<4} {p.name} ({p.representative})")
    print(f"       {p.reasoning}")

# Pre-Mortem
pm = deep.pre_mortem
print(f"\n{'─'*70}")
print("  Pre-Mortem & Anti-Bias")
print(f"{'─'*70}")
print(f"\n  {pm.failure_scenario}")
for fp in pm.failure_paths:
    print(f"    • {fp['description']}  [{fp['probability']}]")
print(f"\n  认知偏差自检:")
for cb in pm.cognitive_biases:
    print(f"    {cb['bias']}: {cb['risk']} → {cb['check']}")

print(f"\n{'='*70}")
print(f"  分析完成 · 数据源: {result.data_source}")
print(f"{'='*70}")
