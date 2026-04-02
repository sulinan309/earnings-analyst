"""自动分析管线 — 从财务数据程序化生成全部分析模块

程序化模块（纯计算）：
- 收入拆分表
- 盈利能力趋势
- CapEx 冲击模拟
- Combo B-J 信号（规则引擎）

AI 生成模块（需 ANTHROPIC_API_KEY）：
- Executive Summary
- Key Forces
- 竞争格局
- 6大投资哲学
- Pre-Mortem

无 API key 时用规则模板兜底。
"""

import json
import os
from dataclasses import dataclass, field, asdict

from src.frameworks.oe_calculator import OECalculator, OEResult, FinancialData
from src.frameworks.capex_simulation import simulate_capex, CapexScenario
from src.frameworks.deep_analysis import (
    DeepAnalysis, ExecutiveSummary, KeyForce, RevenueBreakdown,
    ProfitabilityTrend, CompetitionTable, InvestmentPhilosophy, PreMortem,
)


@dataclass
class CompanyProfile:
    """公司档案 — 分析管线的输入"""
    name: str
    ticker: str
    asset_tier: str
    period: str

    # 收入拆分（从 PDF 或手动输入）
    revenue_segments: list[dict] = field(default_factory=list)
    # 格式: [{"name": "游戏", "fy2025": 2416, "yoy": "+18%", "share": "32%", "trend": "AI驱动"}]

    # 盈利指标 YoY
    profitability_metrics: list[dict] = field(default_factory=list)
    # 格式: [{"name": "毛利率", "fy2024": "34.8%", "fy2025": "56.2%", "change": "+1.4pct"}]
    profitability_insight: str = ""

    # 竞争对手对比
    competition_dims: list[dict] = field(default_factory=list)
    # 格式: [{"metric": "DAU", "company_value": "4.1亿", "comp1_name": "抖音", "comp1_value": "7.5亿", ...}]
    moat_assessment: str = ""

    # CapEx 模拟参数
    capex_cfo_growth: float = 0.05
    capex_growth_base: float = 0.0
    capex_growth_bear: float = 0.30


@dataclass
class FullAnalysisResult:
    """完整分析结果"""
    # 程序化模块
    oe_result: OEResult | None = None
    scenarios: list = field(default_factory=list)
    capex_sim: list[CapexScenario] = field(default_factory=list)
    revenue_breakdown: RevenueBreakdown | None = None
    profitability: ProfitabilityTrend | None = None
    competition: CompetitionTable | None = None

    # AI/模板生成
    deep: DeepAnalysis | None = None

    # 元数据
    data_source: str = ""  # "programmatic" / "claude_api" / "template_fallback"


def run_full_analysis(
    financial_data: FinancialData,
    profile: CompanyProfile,
    oe_result: OEResult | None = None,
    discount_rate: float = 0.10,
) -> FullAnalysisResult:
    """端到端分析管线"""

    result = FullAnalysisResult()

    # ── Step 1: OE 计算（如果没有传入）──
    if oe_result is None:
        oe_result = OECalculator(discount_rate=discount_rate).calculate(financial_data)
    result.oe_result = oe_result

    # ── Step 2: 三情景估值 ──
    result.scenarios = OECalculator(discount_rate=discount_rate).scenario_analysis(financial_data)

    # ── Step 3: CapEx 冲击模拟（程序化）──
    result.capex_sim = simulate_capex(
        fy_cfo=oe_result.cfo,
        fy_total_capex=financial_data.total_capex,
        fy_maintenance_capex=oe_result.maintenance_capex,
        cfo_growth=profile.capex_cfo_growth,
        capex_growth_base=profile.capex_growth_base,
        capex_growth_bear=profile.capex_growth_bear,
    )

    # ── Step 4: 收入拆分（直接用输入数据）──
    if profile.revenue_segments:
        result.revenue_breakdown = RevenueBreakdown(segments=profile.revenue_segments)

    # ── Step 5: 盈利趋势（直接用输入数据）──
    if profile.profitability_metrics:
        result.profitability = ProfitabilityTrend(
            metrics=profile.profitability_metrics,
            insight=profile.profitability_insight,
        )

    # ── Step 6: 竞争格局（直接用输入数据）──
    if profile.competition_dims:
        result.competition = CompetitionTable(
            dimensions=profile.competition_dims,
            moat_assessment=profile.moat_assessment,
        )

    # ── Step 7: AI 叙事模块 ──
    api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            result.deep = _generate_with_claude(financial_data, profile, oe_result, result)
            result.data_source = "claude_api"
        except Exception as e:
            print(f"  ⚠ AI生成失败({type(e).__name__})，使用模板兜底")
            result.deep = _generate_with_template(financial_data, profile, oe_result, result)
            result.data_source = "template_fallback (API failed)"
    else:
        result.deep = _generate_with_template(financial_data, profile, oe_result, result)
        result.data_source = "template_fallback"

    return result


def _generate_with_claude(
    fd: FinancialData, profile: CompanyProfile, oe: OEResult, partial: FullAnalysisResult
) -> DeepAnalysis:
    """用 Claude API 生成叙事模块"""
    import anthropic

    client = anthropic.Anthropic(
        api_key=os.environ.get("OPENROUTER_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"),
        base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    # 准备数据摘要给 Claude
    data_summary = f"""
公司: {profile.name} ({profile.ticker}) {profile.period}
资产层级: {profile.asset_tier}

OE 计算:
- CFO: {oe.cfo:.1f} 亿港币
- 维持性Capex: {oe.maintenance_capex:.1f} 亿{'(估算)' if oe.maintenance_capex_is_estimated else ''}
- OE: {oe.oe:.1f} 亿 (margin {oe.oe_margin_pct}%)
- 零增长估值: {oe.zero_growth_value:.1f} 亿
- 内在价值: {oe.intrinsic_value:.1f} 亿
- 市值: {oe.market_cap:.1f} 亿
- 安全边际: {oe.safety_margin_pct:+.1f}%
- 赔率: {oe.odds:.1%}

收入拆分: {json.dumps(profile.revenue_segments, ensure_ascii=False) if profile.revenue_segments else '无'}

盈利趋势: {json.dumps(profile.profitability_metrics, ensure_ascii=False) if profile.profitability_metrics else '无'}

CapEx 模拟:
{chr(10).join(f'  {s.label}: CFO {s.cfo:.0f}, Capex {s.total_capex:.0f}, OE {s.oe:.0f}, FCF {s.fcf:.0f}' for s in partial.capex_sim)}

竞争格局: {json.dumps(profile.competition_dims, ensure_ascii=False) if profile.competition_dims else '无'}
"""

    prompt = f"""你是一位基于李录Owner's Earnings框架的港股分析师。根据以下数据，生成深度分析报告的叙事部分。

{data_summary}

请严格按以下JSON格式输出，所有内容用中文：
{{
  "executive_summary": {{
    "headline": "一句话核心投资论点（Variant View风格，如'260亿AI豪赌——是AWS时刻还是价值陷阱?'）",
    "action": "建议动作（如'观察，等待股价≤X港币或Combo B触发再入场'）",
    "tldr": ["要点1", "要点2", "要点3"],
    "body": "2-3段Executive Summary正文"
  }},
  "key_forces": [
    {{"title": "#1 标题", "body": "2-3句分析", "oe_implication": "对OE框架的含义"}},
    {{"title": "#2 标题", "body": "分析", "oe_implication": "含义"}}
  ],
  "philosophies": [
    {{"name": "品质复利", "representative": "巴菲特/芒格", "verdict": "看多/看空/观望/轻多", "reasoning": "1-2句理由"}},
    {{"name": "想象力成长", "representative": "Baillie Gifford/ARK", "verdict": "...", "reasoning": "..."}},
    {{"name": "基本面多空", "representative": "Tiger Cubs", "verdict": "...", "reasoning": "..."}},
    {{"name": "深度价值", "representative": "Klarman/Marks", "verdict": "...", "reasoning": "..."}},
    {{"name": "催化剂驱动", "representative": "Tepper/Ackman", "verdict": "...", "reasoning": "..."}},
    {{"name": "宏观策略", "representative": "Druckenmiller", "verdict": "...", "reasoning": "..."}}
  ],
  "pre_mortem": {{
    "failure_scenario": "假设18个月后亏钱，最可能原因是...",
    "failure_paths": [{{"description": "路径描述", "probability": "30%"}}],
    "cognitive_biases": [{{"bias": "偏差名", "risk": "风险", "check": "检查方法"}}]
  }}
}}"""

    response = client.messages.create(
        model="anthropic/claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt + "\n\n请只输出JSON，不要输出其他内容。"}],
    )

    text = next((b.text for b in response.content if b.type == "text"), None)
    raw = json.loads(text)
    return _parse_deep_json(raw)


def _generate_with_template(
    fd: FinancialData, profile: CompanyProfile, oe: OEResult, partial: FullAnalysisResult
) -> DeepAnalysis:
    """无 API key 时的规则模板兜底"""

    margin_status = "存在" if oe.has_safety_margin else "不存在"
    margin_dir = "低估" if oe.odds > 0 else "高估"

    # CapEx 趋势判断
    capex_ratio = fd.total_capex / fd.revenue * 100 if fd.revenue > 0 else 0
    capex_warning = f"Capex/收入比 {capex_ratio:.1f}%"
    if capex_ratio > 15:
        capex_note = "，重资本投入期，OE承压"
    elif capex_ratio > 10:
        capex_note = "，投入力度较大"
    else:
        capex_note = "，投入可控"

    # FCF 判断
    fcf = oe.cfo - fd.total_capex
    fcf_note = f"FCF {fcf:.0f}亿" + ("（正向造血）" if fcf > 0 else "（现金消耗）")

    headline = (
        f"{profile.name}：OE {oe.oe:.0f}亿，安全边际{oe.safety_margin_pct:+.1f}%"
        f"——{'被' + margin_dir if abs(oe.safety_margin_pct) > 10 else '估值合理'}"
    )

    action_map = {True: f"存在安全边际(+{oe.safety_margin_pct:.0f}%)，关注Combo信号确认后建仓",
                  False: f"安全边际不足({oe.safety_margin_pct:+.0f}%)，等待更好价格"}
    action = action_map[oe.has_safety_margin]

    tldr = [
        f"OE {oe.oe:.0f}亿 (margin {oe.oe_margin_pct}%)，{fcf_note}",
        f"内在价值 {oe.intrinsic_value:.0f}亿 vs 市值 {oe.market_cap:.0f}亿，安全边际 {oe.safety_margin_pct:+.1f}%",
        f"{capex_warning}{capex_note}",
    ]
    if oe.investment_portfolio_gross > 0:
        tldr.append(f"投资组合 {oe.investment_portfolio_gross:.0f}亿，折扣后贡献 {oe.investment_portfolio_value:.0f}亿")

    body = (
        f"{profile.name} {profile.period} 交出收入 {fd.revenue:.0f}亿港币的成绩单。"
        f"OE框架下，经营性现金流 {oe.cfo:.0f}亿 减去维持性Capex {oe.maintenance_capex:.0f}亿"
        f"{'(估算)' if oe.maintenance_capex_is_estimated else ''}，"
        f"得到Owner's Earnings {oe.oe:.0f}亿，OE Margin {oe.oe_margin_pct}%。\n\n"
        f"零增长估值 {oe.zero_growth_value:.0f}亿 + 可分配净现金 {oe.distributable_net_cash:.0f}亿"
        + (f" + 投资组合(折扣后) {oe.investment_portfolio_value:.0f}亿" if oe.investment_portfolio_value else "")
        + f" = 内在价值 {oe.intrinsic_value:.0f}亿。当前市值 {oe.market_cap:.0f}亿，"
        f"安全边际 {oe.safety_margin_pct:+.1f}%，{margin_status}安全边际。\n\n"
        f"关键关注：{capex_warning}{capex_note}。{fcf_note}。"
        f"{'维持性Capex为估算值，需关注实际拆分。' if oe.maintenance_capex_is_estimated else ''}"
    )

    # Key Forces（从数据自动推导）
    key_forces = []
    if capex_ratio > 10:
        key_forces.append(KeyForce(
            title=f"#1 Capex投入强度 ({capex_warning})",
            body=f"总Capex {fd.total_capex:.0f}亿中维持性 {oe.maintenance_capex:.0f}亿，扩张性 {oe.growth_capex:.0f}亿。扩张性Capex不计入OE，但其回报率决定长期价值。",
            oe_implication=f"当前OE {oe.oe:.0f}亿不受扩张性Capex影响，但若投入2-3年无回报，市场会重分类为'维持性'，压缩OE。",
        ))
    if oe.investment_portfolio_gross > 0:
        key_forces.append(KeyForce(
            title=f"#{'2' if key_forces else '1'} 投资组合价值 ({oe.investment_portfolio_gross:.0f}亿)",
            body=f"上市投资公允价值 {fd.listed_investments_fv:.0f}亿 + 非上市账面 {fd.unlisted_investments_bv:.0f}亿。按{oe.investment_discount_rate:.0%}折扣计入 {oe.investment_portfolio_value:.0f}亿。",
            oe_implication=f"投资组合占内在价值 {oe.investment_portfolio_value/oe.intrinsic_value*100:.0f}%，折扣率的选择对估值影响巨大。",
        ))
    if abs(oe.safety_margin_pct) < 15:
        key_forces.append(KeyForce(
            title=f"#{len(key_forces)+1} 估值处于临界区间",
            body=f"安全边际{oe.safety_margin_pct:+.1f}%接近零，小幅变化即可改变结论。",
            oe_implication="需要Combo信号确认方向，单独OE估值不足以做决策。",
        ))

    # 6 大投资哲学（规则模板）
    has_margin = oe.has_safety_margin
    high_growth = capex_ratio > 12
    philosophies = [
        InvestmentPhilosophy("品质复利", "巴菲特/芒格",
            "观望" if not has_margin else "轻多",
            f"OE Margin {oe.oe_margin_pct}%{'达标' if (oe.oe_margin_pct or 0) > 20 else '偏低'}，"
            f"{'但当前估值偏贵' if not has_margin else '估值有安全边际'}"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK",
            "看多" if high_growth else "观望",
            f"Capex/收入 {capex_ratio:.1f}%，{'重投入期意味着增长野心' if high_growth else '投入力度一般'}"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs",
            "看多" if has_margin else "观望",
            f"安全边际{oe.safety_margin_pct:+.1f}%，{'EV/OE有吸引力' if has_margin else '估值不够便宜'}"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks",
            "看多" if oe.odds > 0.3 else ("轻多" if has_margin else "观望"),
            f"赔率{oe.odds:.1%}，{'净现金+投资组合提供安全垫' if oe.distributable_net_cash > 0 else '净现金为负需警惕'}"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman",
            "观望",
            "需要明确催化剂（业绩拐点/回购加速/政策利好）才能触发重定价"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller",
            "观望",
            "港股流动性一般，南向资金态度不明朗，不是最佳宏观窗口"),
    ]

    # Pre-Mortem
    pre_mortem = PreMortem(
        failure_scenario=f"假设18个月后{profile.name}亏钱，最可能原因是...",
        failure_paths=[
            {"description": f"OE下滑：维持性Capex实际高于估计，压缩OE至{oe.oe*0.7:.0f}亿以下", "probability": "25%"},
            {"description": f"估值压缩：市场给更低倍数，即使OE不变市值也下跌", "probability": "25%"},
            {"description": "竞争恶化：核心业务市占率被蚕食，收入增速转负", "probability": "20%"},
            {"description": "监管风险：政策打击导致商业模式受损", "probability": "15%"},
            {"description": "宏观衰退：港股整体下跌拖累估值", "probability": "15%"},
        ],
        cognitive_biases=[
            {"bias": "锚定效应", "risk": f"被{oe.safety_margin_pct:+.1f}%安全边际锚定", "check": "用三情景估值交叉验证"},
            {"bias": "叙事偏差", "risk": "被增长故事吸引忽视现金流质量", "check": "只看OE和FCF，不看利润"},
            {"bias": "确认偏差", "risk": "只找支持买入的证据", "check": "主动列出3个不买的理由"},
        ],
    )

    return DeepAnalysis(
        executive_summary=ExecutiveSummary(headline=headline, action=action, tldr=tldr, body=body),
        key_forces=key_forces,
        revenue_breakdown=RevenueBreakdown(segments=profile.revenue_segments),
        profitability=ProfitabilityTrend(metrics=profile.profitability_metrics, insight=profile.profitability_insight),
        competition=CompetitionTable(dimensions=profile.competition_dims, moat_assessment=profile.moat_assessment),
        philosophies=philosophies,
        pre_mortem=pre_mortem,
    )


def _parse_deep_json(raw: dict) -> DeepAnalysis:
    """将 Claude API 返回的 JSON 转为 DeepAnalysis"""
    es = raw["executive_summary"]
    return DeepAnalysis(
        executive_summary=ExecutiveSummary(**es),
        key_forces=[KeyForce(**kf) for kf in raw["key_forces"]],
        revenue_breakdown=RevenueBreakdown(),
        profitability=ProfitabilityTrend(),
        competition=CompetitionTable(),
        philosophies=[InvestmentPhilosophy(**p) for p in raw["philosophies"]],
        pre_mortem=PreMortem(
            failure_scenario=raw["pre_mortem"]["failure_scenario"],
            failure_paths=raw["pre_mortem"]["failure_paths"],
            cognitive_biases=raw["pre_mortem"]["cognitive_biases"],
        ),
    )
