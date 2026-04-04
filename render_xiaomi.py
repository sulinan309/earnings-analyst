"""小米 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML

数据来源：Claude 生成的完整分析文档（非规则模板）
"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.frameworks.auto_analysis import CompanyProfile, run_full_analysis
from src.frameworks.deep_analysis import (
    DeepAnalysis, ExecutiveSummary, KeyForce, RevenueBreakdown,
    ProfitabilityTrend, CompetitionTable, InvestmentPhilosophy, PreMortem,
    ComboSignal, CoreProduct,
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
        headline='小米v4.3：32 HKD处于回避区——Payback 30年，三家中最贵。经调整利润392亿 vs FCF仅~200亿，市场在为"故事"而非"现金流"定价',
        action="回避/减持 — 当前32 HKD高于乐观估值(27 HKD)约19%，在v4.3框架下明确超出估值上限",
        tldr=[
            "v4.3估值：保守16 / 基准22 / 乐观27 HKD。当前32处于回避区(>27)，Payback 30年(三家最贵)",
            "核心问题：经调整净利润392亿 vs FCF仅~200亿——Guard Rail要求OE≤240亿，远低于市场隐含的利润预期",
            "分层估值：手机×AIoT×互联网(Layer A) OE~200亿 + 汽车×AI(Layer B) OE~0-60亿",
            "按李录/价值框架不应持有。400股@33.47定位为swing trade(非价值买入)，34.5+考虑减持释放资金给快手/腾讯",
        ],
        body=(
            "2025年报整体符合'史上最强'叙事——全年营收4573亿(+25%)，经调整净利润392亿(+44%)，"
            "汽车业务首破千亿且年度经营收益转正至9亿。然而Q4单季暴露的结构性隐忧不容忽视：手机毛利率"
            "跌至8.3%历史低位，Q4经营现金流仅6亿。\n\n"
            "v4.3估值修正：Guard Rail要求OE≤1.2×FCF。FCF估计~200亿(远低于经调整净利润392亿)——"
            "OE上限240亿。分层估值：Layer A(手机+IoT+互联网) OE~200亿，Layer B(汽车+AI) OE~0-60亿。"
            "基准OE 240亿(g=3%, r=11%) → 基准内在价值22 HKD。当前32 HKD高出45%。\n\n"
            "Payback 30年(base, static)是三家中最长——每投入1港币需要30年通过现金流回收。"
            "按李录/价值框架，32 HKD处于回避区。400股@33.47应定位为swing trade而非价值持仓。"
            "34.5+考虑减持，释放资金优先配置快手(明确加仓区)和腾讯(等回落)。"
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

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ 汽车工厂CapEx高峰期(2025-2027)，总CapEx 400亿中~280亿为汽车+AI扩张性投入。OE严重依赖维持性CapEx的拆分假设",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", True, "3/4", [
            {"name": "核心收入增速连续2季回升", "triggered": True, "detail": "汽车+237%拉动整体+35%"},
            {"name": "OCF margin同比扩张>3pct", "triggered": True, "detail": "OCF margin改善，但汽车仍亏损"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "汽车工厂CapEx高峰，总CapEx占比上升至8.7%"},
            {"name": "核心竞争力指标改善", "triggered": True, "detail": "SU7交付量超预期，单车毛利率转正"},
        ]),
        ComboSignal("Combo C · 政策催化型", True, "3/4", [
            {"name": "监管表态明确转向友好", "triggered": True, "detail": "新能源汽车补贴延续，以旧换新政策"},
            {"name": "行业竞争格局收缩", "triggered": False, "detail": "新能源汽车竞争白热化，玩家众多"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "小米汽车直接受益于新能源政策"},
            {"name": "海外同类公司已先行验证", "triggered": True, "detail": "特斯拉验证了科技公司造车路径"},
        ]),
        ComboSignal("Combo E · 估值透支型", True, "3/4", [
            {"name": "市值>乐观OE估值+净现金", "triggered": True, "detail": "市值8570亿 vs 乐观估值~7000亿"},
            {"name": "赔率<20%停止加仓", "triggered": True, "detail": "赔率为负(市值>内在价值)"},
            {"name": "市值/OE>历史均值130%", "triggered": True, "detail": "当前PE远高于历史均值"},
            {"name": "分析师上调空间<10%", "triggered": False, "detail": "汽车故事仍有上调空间"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", False, "0/4", [
            {"name": "核心假设被财报否定", "triggered": False, "detail": "汽车交付超预期，手机仍稳健"},
            {"name": "竞争对手颠覆性打法", "triggered": False, "detail": "暂无颠覆性威胁"},
            {"name": "管理层资本配置重大失误", "triggered": False, "detail": "汽车投入有章法"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "无重大监管风险"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="小米SU7/YU7",
            subtitle="Reality Check — 汽车业务盈利路径",
            metrics=[
                {"metric": "SU7交付量(2025)", "value": "~13.6万台", "judgment": "正面", "note": "超年初10万台指引"},
                {"metric": "单车毛利率", "value": "~20%", "judgment": "正面", "note": "好于蔚来/小鹏同期"},
                {"metric": "汽车业务亏损", "value": "仍亏损", "judgment": "负面", "note": "工厂折旧+研发摊销"},
                {"metric": "YU7预订量", "value": ">10万(估)", "judgment": "正面", "note": "SUV市场更大"},
                {"metric": "2026目标", "value": "30万台", "judgment": "中性", "note": "产能爬坡是关键瓶颈"},
                {"metric": "对OE侵蚀", "value": "~280亿CapEx", "judgment": "负面", "note": "扩张性CapEx压低OE"},
            ],
            insight="小米汽车交付数据亮眼，但OE视角下280亿扩张性CapEx使其短期内无法贡献正向现金流。至少到2027年才能开始正向贡献。",
        ),
    ],
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
