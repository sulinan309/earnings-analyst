"""小米 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML

数据来源：Claude 生成的完整分析文档（非规则模板）
"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.frameworks.auto_analysis import CompanyProfile, run_full_analysis
from src.frameworks.deep_analysis import (
    DeepAnalysis, ExecutiveSummary, KeyForce, RevenueBreakdown,
    ProfitabilityTrend, CompetitionTable, InvestmentPhilosophy, PreMortem,
)
from src.frameworks.capex_simulation import simulate_capex
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html

FX = 1.1
def cnb(v): return round(v * FX, 2)


# ═══════════════════════════════════════════
#  财务数据（从分析文档提取）
# ═══════════════════════════════════════════

financial_data = FinancialData(
    cfo=cnb(676),                   # 券商预估全年CFO ~676亿
    maintenance_capex=cnb(120),     # ≈折旧 ~120亿（文档K0）
    total_capex=cnb(400),           # 汽车工厂+AI
    cash_and_equivalents=cnb(800),
    short_term_investments=cnb(1200),
    interest_bearing_debt=cnb(350),
    committed_investments=cnb(100),
    restricted_cash=cnb(30),
    overseas_cash=cnb(150),
    revenue=cnb(4573),
    market_cap=8570.0,              # ~32 HKD × 255亿股 ≈ 8570亿港币
    period="FY2025", ticker="1810.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="Maintenance CapEx ≈ 折旧~120亿（保守代理假设），文档K0方法",
)


# ═══════════════════════════════════════════
#  CompanyProfile（程序化模块数据）
# ═══════════════════════════════════════════

profile = CompanyProfile(
    name="小米", ticker="1810.HK", asset_tier="中等质量", period="FY2025",

    revenue_segments=[
        {"name": "智能手机", "fy2025": cnb(1864), "yoy": "-2.8%", "share": "41%",
         "trend": "出货1.652亿台(-2%)，ASP下降，高端占比27.1%"},
        {"name": "IoT与生活消费品", "fy2025": cnb(1232), "yoy": "+18.3%", "share": "27%",
         "trend": "连接设备10.79亿台(+19%)，大家电出海启动"},
        {"name": "互联网服务", "fy2025": cnb(374), "yoy": "+9.7%", "share": "8%",
         "trend": "毛利率76.5%，高利润贡献者，依赖硬件基数"},
        {"name": "智能电动汽车及AI", "fy2025": cnb(1061), "yoy": "+224%", "share": "23%",
         "trend": "交付41.1万辆，ASP 25.12万，年度经营收益首次转正9亿"},
    ],

    profitability_metrics=[
        {"name": "集团毛利率", "fy2024": "20.9%", "fy2025": "22.3%", "change": "+1.4pct"},
        {"name": "手机毛利率", "fy2024": "12.6%", "fy2025": "10.9%", "change": "-1.7pct ⚠"},
        {"name": "手机Q4毛利率", "fy2024": "~12%", "fy2025": "8.3%", "change": "历史低位 ⚠⚠"},
        {"name": "IoT毛利率", "fy2024": "20.3%", "fy2025": "23.1%", "change": "+2.8pct"},
        {"name": "汽车毛利率", "fy2024": "18.5%", "fy2025": "24.3%", "change": "+5.8pct"},
        {"name": "互联网服务毛利率", "fy2024": "76.3%", "fy2025": "76.5%", "change": "稳定"},
        {"name": "经调整净利润率", "fy2024": "7.4%", "fy2025": "8.6%", "change": "+1.2pct"},
    ],
    profitability_insight=(
        "集团毛利率+1.4pct的改善掩盖了严重的结构性分化：汽车毛利率24.3%已高于手机×AIoT分部的21.7%，"
        "但手机毛利率从12.6%暴跌至10.9%（Q4仅8.3%）。存储成本上涨是核心驱动——管理层判断可能持续到2027年底。"
        "如果手机毛利率无法回升至10%+，仅靠汽车增量无法完全弥补。"
    ),

    competition_dims=[
        {"metric": "2025收入(亿)", "company_value": str(cnb(4573)), "comp1_name": "比亚迪", "comp1_value": "~7,700", "comp2_name": "华为终端", "comp2_value": "~5,000+"},
        {"metric": "手机出货(亿台)", "company_value": "1.65", "comp1_name": "苹果", "comp1_value": "2.3", "comp2_name": "华为", "comp2_value": "~0.5"},
        {"metric": "汽车交付(万辆)", "company_value": "41.1", "comp1_name": "比亚迪", "comp1_value": "425", "comp2_name": "理想", "comp2_value": "50"},
        {"metric": "汽车毛利率", "company_value": "24.3%", "comp1_name": "比亚迪", "comp1_value": "~22%", "comp2_name": "特斯拉", "comp2_value": "~18%"},
        {"metric": "IoT设备连接", "company_value": "10.79亿", "comp1_name": "华为", "comp1_value": "~9亿", "comp2_name": "苹果", "comp2_value": "~20亿"},
    ],
    moat_assessment=(
        "多层护城河但各层深度有限：品牌认知强但高端化仍在进行中（6000+市占仅4.5%）；"
        "IoT生态连接10.79亿设备形成锁定效应；互联网服务的变现依赖硬件基数。"
        "相比腾讯的社交图谱或美团的本地生活网络效应，小米更多是'生态广度'而非'单点深度'。"
    ),

    capex_cfo_growth=0.05,
    capex_growth_base=0.10,
    capex_growth_bear=0.35,
)


# ═══════════════════════════════════════════
#  DeepAnalysis（从 Claude 分析文档直接映射）
# ═══════════════════════════════════════════

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='小米"人车家"第二曲线已跑通，但传统基本盘失血速度被市场低估——汽车盈利兑现后，2026年的真问题是手机毛利能否止跌',
        action="持有/观察，非新建仓时机 — 当前~32 HKD处于Action Price(~29 HKD)附近，安全边际有限",
        tldr=[
            "OE ~412亿元(1.76 HKD/股)，内在价值~38.4 HKD vs 当前~32 HKD，折价~17%但IRR仅~9%＜15%铁律",
            "汽车业务首破千亿且盈利(+9亿)，毛利率24.3%已超手机×AIoT分部——第二曲线兑现",
            "Q4手机毛利率跌至8.3%历史低位，存储涨价可能持续到2027底——不是一两季度的扰动",
            "Action Price ~29 HKD，跌至28以下考虑加仓；涨至38+考虑获利了结",
        ],
        body=(
            "2025年报整体符合'史上最强'叙事——全年营收4573亿(+25%)，经调整净利润392亿(+44%)，"
            "汽车业务首破千亿且年度经营收益转正至9亿。然而Q4单季暴露的结构性隐忧不容忽视：手机毛利率"
            "跌至8.3%历史低位，存储成本上涨的冲击远超管理层此前预期，手机×AIoT分部Q4经营利润同比下降约六成。"
            "市场已用脚投票——股价从高点61.45 HKD回调至~32 HKD，跌幅超47%。\n\n"
            "核心矛盾：汽车业务的规模化盈利已兑现(Key Force #1)，但传统基本盘的利润侵蚀(Key Force #2)"
            "正在加速，两股力量的净效应在2026年存在较大不确定性。我们的Variant View是：市场对汽车业务的"
            "定价已较为充分，但对存储成本冲击的持续性可能仍然低估——管理层判断本轮存储涨价可能持续到2027年底，"
            "这意味着手机业务的利润压力不是一两个季度的扰动，而是中期结构性问题。\n\n"
            "K0估值: OE×(1+g)/(r-g) + 净现金 + 投资组合 = 31.1 + 5.88 + 1.37 = 38.4 HKD。"
            "扣除25%安全边际后Action Price ~29 HKD。当前32 HKD处于Action Price上沿——持有合理，新建仓吸引力不足。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 汽车业务从'烧钱'到'利润贡献者'的跨越速度",
            body=(
                "2025年已实现年度经营收益转正。2026年目标交付55万辆，北京+武汉双工厂总产能~120万辆。"
                "汽车业务24.3%的全年毛利率已高于手机×AIoT分部的21.7%，如果汽车规模持续放大，"
                "将结构性地拉升集团毛利率。新一代SU7开售34分钟锁单15000台。"
            ),
            oe_implication="汽车Capex目前大部分是扩张性的（不计入OE），但随着规模化，折旧替换部分将逐步转为维持性Capex，需持续跟踪。",
        ),
        KeyForce(
            title="#2 手机业务的成本-收入剪刀差（存储涨价危机）",
            body=(
                "存储芯片长周期涨价（管理层判断可能持续到2027年底）正在侵蚀手机毛利。"
                "2025年手机毛利率从12.6%降至10.9%，Q4更跌至8.3%。手机仍贡献41%的收入，"
                "如果毛利率持续承压，将显著拖累集团利润增速。"
            ),
            oe_implication="手机毛利率每下降1pct，约减少19亿利润。如果毛利率长期维持8-9%，OE将被压缩~60-80亿。",
        ),
        KeyForce(
            title="#3 AI生态 + '人车家'协同效应的货币化",
            body=(
                "MiMo大模型全球排名第八、国内第二。miclaw AI Agent正在封测。AI眼镜出货全球第三。"
                "但这些目前均不构成独立收入线——AI是费用项不是收入项。未来三年600亿AI投入意味着："
                "如果AI未能有效货币化，将持续压制利润增速。"
            ),
            oe_implication="600亿AI投入/3年 = 年均200亿费用项。如果归类为扩张性Capex不影响OE，但如果被视为维持竞争力的'必要投入'则应计入维持性Capex。",
        ),
    ],

    revenue_breakdown=RevenueBreakdown(segments=profile.revenue_segments),
    profitability=ProfitabilityTrend(
        metrics=profile.profitability_metrics,
        insight=profile.profitability_insight,
    ),
    competition=CompetitionTable(
        dimensions=profile.competition_dims,
        moat_assessment=profile.moat_assessment,
    ),

    philosophies=[
        InvestmentPhilosophy("品质复利", "巴菲特/芒格", "持有",
            "生态协同有长期价值，但护城河深度不及社交/支付类平台。低毛利硬件业务的ROIC能否持续改善是关键。"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "看多",
            "'人车家+AI'如果全部跑通，收入规模可达万亿级。风险是过度多元化导致每条线都做不深。"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "观望",
            "当前估值未提供足够variant view空间，IRR<15%。不构成明确的多头或空头机会。"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "观望",
            "PE 20x对一个手机毛利率在下滑的公司偏高。等待28 HKD以下的深度折价。"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "轻多",
            "新一代SU7交付（2026年4月）是短期催化剂，但已被部分price in。"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股受地缘+利率压制，beta环境不友好。小米高beta属性放大了宏观风险。"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损20%+，最可能原因是...",
        failure_paths=[
            {"description": "存储超级周期：DRAM/NAND涨价持续到2027+，手机毛利率长期维持8%以下", "probability": "25%"},
            {"description": "汽车订单断崖：消费信心走弱，月新增订单降至1.5万以下", "probability": "20%"},
            {"description": "AI投入无回报：600亿投入未能产生商业化进展，市场将其定价为沉没成本", "probability": "20%"},
            {"description": "华为手机回归：芯片供应缓解后加速抢占高端市场，小米高端化受阻", "probability": "15%"},
            {"description": "港股系统性去估值：地缘+利率导致估值中枢下移20%+", "probability": "20%"},
        ],
        cognitive_biases=[
            {"bias": "锚定效应", "risk": "被持仓成本33.47 HKD锚定，不愿在盈亏平衡点附近做决策",
             "check": "忽略entry price，只看forward value"},
            {"bias": "叙事偏差", "risk": "'人车家全生态'极其引人入胜，但叙事吸引力≠利润确定性",
             "check": "Q4利润下滑是真实数据，不应被叙事遮盖"},
            {"bias": "确认偏差", "risk": "选择性关注汽车数据(亮眼)而忽视手机数据(恶化)",
             "check": "两边数据权重应对等"},
        ],
    ),
)


# ═══════════════════════════════════════════
#  运行分析 + 渲染 HTML
# ═══════════════════════════════════════════

if __name__ == "__main__":
    # 程序化部分
    result = run_full_analysis(financial_data, profile)

    # 用 Claude 分析文档的 DeepAnalysis 替换模板生成的
    result.deep = deep_analysis
    result.data_source = "claude_analysis_document"

    # Combo A
    oe = result.oe_result
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier="中等质量",
        quarterly_oes=[round(oe.oe / 4, 1)] * 4,
        oe_multiple_percentile=50.0,
        structural_deterioration=False,
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, "中等质量")

    inp = ReportInput(
        company_name="小米", ticker="1810.HK", asset_tier="中等质量",
        focus="汽车Capex对OE的侵蚀、手机毛利率止跌、AI投入ROI",
        financial_data=financial_data, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )

    html = generate_html(inp, deep=result)

    out_path = "docs/1810_HK.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} ({len(html)//1024}KB)")
    print(f"  数据源: {result.data_source}")
    print(f"  OE: {oe.oe:.0f}亿 | 安全边际: {oe.safety_margin_pct:+.1f}%")
    print(f"  Combo A: {combo_a.triggered_count}/4 | 决策: {mx.action}")
