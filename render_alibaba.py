"""阿里 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.frameworks.auto_analysis import CompanyProfile, run_full_analysis
from src.frameworks.deep_analysis import (
    DeepAnalysis, ExecutiveSummary, KeyForce, RevenueBreakdown,
    ProfitabilityTrend, CompetitionTable, InvestmentPhilosophy, PreMortem,
    ComboSignal, CoreProduct,
)
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html

FX = 1.1
def cnb(v): return round(v * FX, 2)
def cnm(v): return round(v * FX / 100, 2)

financial_data = FinancialData(
    cfo=cnb(1635),                  # OCF 1635亿 [A]
    maintenance_capex=cnb(400),     # 存量电商/云维护
    total_capex=cnb(896),           # CapEx = OCF - FCF = 1635 - 739
    cash_and_equivalents=cnb(2000),
    short_term_investments=cnb(3000),
    interest_bearing_debt=cnb(2107),
    committed_investments=cnb(200),
    restricted_cash=cnb(50),
    overseas_cash=cnb(800),
    revenue=cnb(9963),
    market_cap=21700.0,             # ~118.5 HKD × 183亿股
    listed_investments_fv=cnb(800),
    unlisted_investments_bv=cnb(300),
    investment_discount=0.50,
    period="FY2025", ticker="9988.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="FCF从1562亿暴跌53%至739亿。CapEx~896亿中大量为AI云基建。维持性取~400亿(存量电商+云)",
)

profile = CompanyProfile(
    name="阿里", ticker="9988.HK", asset_tier="中等质量", period="FY2025",
    revenue_segments=[
        {"name": "淘天集团", "fy2025": cnb(4498), "yoy": "+3%", "share": "45%",
         "trend": "CMR(Q4+12%)靠Take Rate提升，非GMV驱动。88VIP破5000万"},
        {"name": "AIDC（国际）", "fy2025": cnb(1323), "yoy": "+29%", "share": "13%",
         "trend": "Lazada/AliExpress增长强劲但仍亏损"},
        {"name": "云智能", "fy2025": cnb(1180), "yoy": "+11%", "share": "12%",
         "trend": "Q3加速至+34%，AI产品连续多季度三位数增长"},
        {"name": "本地生活", "fy2025": cnb(620), "yoy": "+10-12%", "share": "6%",
         "trend": "饿了么+高德，闪购烧钱中"},
        {"name": "其他（含剥离）", "fy2025": cnb(2342), "yoy": "下降", "share": "24%",
         "trend": "出售高鑫零售+银泰，聚焦核心"},
    ],
    profitability_metrics=[
        {"name": "经调整EBITA", "fy2024": str(cnb(1649)), "fy2025": str(cnb(1731)), "change": "+5%"},
        {"name": "Non-GAAP净利润", "fy2024": str(cnb(1581)), "fy2025": str(cnb(1581)), "change": "持平"},
        {"name": "GAAP净利润", "fy2024": str(cnb(713)), "fy2025": str(cnb(1260)), "change": "+77%(低基数+投资收益)"},
        {"name": "FCF", "fy2024": str(cnb(1562)), "fy2025": str(cnb(739)), "change": "-53% ⚠⚠"},
        {"name": "OCF", "fy2024": str(cnb(1826)), "fy2025": str(cnb(1635)), "change": "-10%"},
        {"name": "Non-GAAP隐含PE", "fy2024": "-", "fy2025": "~10x", "change": "看似便宜"},
        {"name": "FCF隐含PE", "fy2024": "-", "fy2025": "~25x", "change": "⚠ 不便宜"},
    ],
    profitability_insight=(
        "核心矛盾：Non-GAAP利润1581亿(持平)看似稳健，但FCF从1562亿暴跌53%至739亿——"
        "差额被3800亿AI投入(年均~1267亿CapEx)吞噬。用Non-GAAP算PE=10x看似便宜，"
        "用FCF算'真实PE'=25x+——不便宜。FY2026H1 FCF更是净流出407亿。"
        "最新季度(FY2026Q2)经调整EBITA仅91亿(-78%)——闪购烧钱+AI投入加速的双重打击。"
    ),
    competition_dims=[
        {"metric": "电商收入(亿)", "company_value": str(cnb(4498)), "comp1_name": "拼多多", "comp1_value": str(cnb(4318)), "comp2_name": "抖音电商", "comp2_value": "~3,000+"},
        {"metric": "云收入(亿)", "company_value": str(cnb(1180)), "comp1_name": "华为云", "comp1_value": "~770+", "comp2_name": "腾讯云", "comp2_value": "~550+"},
        {"metric": "FCF(亿)", "company_value": str(cnb(739)), "comp1_name": "腾讯", "comp1_value": str(cnb(1826)), "comp2_name": "PDD", "comp2_value": str(cnb(1069))},
        {"metric": "AI投入(年化)", "company_value": "~1267亿", "comp1_name": "腾讯", "comp1_value": "~360亿+", "comp2_name": "字节", "comp2_value": "~1000亿+"},
        {"metric": "回购力度", "company_value": "119亿美元/年", "comp1_name": "腾讯", "comp1_value": "800亿港元/年", "comp2_name": "快手", "comp2_value": "31亿港元/年"},
    ],
    moat_assessment=(
        "淘天面临三面夹击：抖音电商搜索化侵蚀高客单价品类；拼多多下沉市场根基稳固；微信小店+视频号电商崛起。"
        "阿里云在中国IaaS市场份额领先(~30%)但华为云/腾讯云追赶。千问系列开源模型全球下载3亿+是亮点，"
        "但开源模型直接变现路径不如闭源清晰。护城河从'电商绝对垄断'弱化为'多业务组合+云基础设施'。"
    ),
    capex_cfo_growth=0.0,
    capex_growth_base=0.20,
    capex_growth_bear=0.40,
)

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='阿里是一台年产1600亿现金流的机器，但3800亿AI豪赌正在吞噬这台机器的产出——FCF腰斩53%是阵痛还是价值毁灭？',
        action="观望/小额持有 — 当前118.5 HKD处于观察区偏上(Base 101, Optimistic 131)，Medium-Low Conviction",
        tldr=[
            "v4.3估值：保守62 / 基准101 / 乐观131 HKD。当前118.5处于观察区偏上，Payback 17.3年",
            "核心矛盾：Non-GAAP利润1581亿(PE=10x)看似便宜，但FCF仅739亿(PE=25x)——用FCF定价不便宜",
            "3800亿AI豪赌：云+34%加速增长是真实AI变现，但FY2026H1 FCF已净流出407亿",
            "资金配置优先级：快手(明确加仓) > 腾讯(等回落) > 阿里(占座观望) > 小米(swing trade)",
        ],
        body=(
            "FY2025年报：收入9963亿(+6%)，经营利润1409亿(+24%)，GAAP净利1260亿(+77%)，"
            "Non-GAAP净利1581亿(持平)。最刺眼的数字：FCF从1562亿暴跌53%至739亿——云基础设施支出激增所致。\n\n"
            "v4.3估值：Guard Rail要求OE≤1.2×正常化FCF≈1440亿。分层估值：Layer A(淘天+云盈利部分) OE~1000亿，"
            "Layer B(AIDC+本地+闪购+AI基建) OE=-50至+50亿。基准OE 1100亿(g=3%, r=11%) → 基准内在价值101 HKD。"
            "当前118.5高于Base约17%。\n\n"
            "关键判断：3800亿AI投入能否转化为收入增长和利润回报？云+34%增速和AI产品三位数增长是正面信号，"
            "但FY2026H1 FCF净流出407亿说明投入规模远超当前回报。闪购投入'下季度将显著缩减'——是否兑现是近期最关键验证点。"
            "维持1手占座，股价<90考虑小额加仓，>140减持。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 3800亿AI豪赌——回报路径可见但规模不匹配",
            body=(
                "阿里云Q3收入+34%，AI产品连续多季度三位数增长。千问开源模型下载3亿+。"
                "但FY2025 FCF已腰斩至739亿，FY2026H1更是净流出407亿。3800亿三年AI投入≈年均1267亿CapEx——"
                "这意味着阿里正在用存量现金支撑AI投入，造血能力已跟不上烧钱速度。管理层'不排除追加投入'更增不确定性。"
            ),
            oe_implication="年均1267亿CapEx中维持性仅~400亿，增长性~867亿。增长性CapEx不计入OE，但如果3年后回报不及预期，市场会重分类为沉没成本。",
        ),
        KeyForce(
            title="#2 淘天增速困境——CMR靠Take Rate而非GMV",
            body=(
                "淘天FY2025收入4498亿仅+3%。Q4 CMR+12%依靠Take Rate提升而非GMV增长——"
                "这意味着商家在为同样的流量付更多钱，长期可持续性存疑。"
                "抖音电商持续蚕食高客单价品类，拼多多牢占下沉市场，微信小店+视频号电商正在崛起。三面夹击。"
            ),
            oe_implication="淘天贡献约1000亿经营利润(Layer A核心)。如果GMV负增长+Take Rate见顶，OE可能下降15-20%。",
        ),
        KeyForce(
            title="#3 非核心剥离+回购——方向正确但FCF萎缩制约执行",
            body=(
                "出售高鑫零售+银泰是正确的战略聚焦。FY2025回购119亿美元，流通股净减5.1%——力度极大。"
                "但回购的资金来源(FCF)正在萎缩。如果FCF持续为负，回购规模必然缩减，股本下降的复利效应将中断。"
            ),
            oe_implication="回购每年减少~5%股本，OE per share增速快于总OE增速5个百分点。但如果FCF不足以支撑回购，这个加速器会熄火。",
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
        InvestmentPhilosophy("品质复利", "巴菲特/芒格", "观望",
            "曾经的电商绝对垄断已弱化为多业务组合。ROIC在AI投入期大幅下降。20年后是否更强高度不确定"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "轻多",
            "如果阿里云+AI成为中国版AWS，收入空间万亿级。千问开源生态3亿下载是有意义的起点"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "观望",
            "Non-GAAP PE 10x看似便宜，但FCF PE 25x不便宜。利润和现金流的巨大裂缝是最大警告"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "观望",
            "有大量现金(5600亿)+回购意愿，但AI投入正在消耗现金储备。净现金在缩水而非增长"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "轻多",
            "闪购投入缩减(Q3见效?) + 云AI增速加速 + 更多资产剥离——催化剂存在但需验证"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股beta承压。阿里额外面临中美脱钩对AIDC的威胁+VIE架构折扣"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损20%+，最可能原因是...",
        failure_paths=[
            {"description": "AI资本黑洞：3800亿砸下去但云收入增速回落至<20%，ROI不达标", "probability": "30%"},
            {"description": "淘天份额加速流失：GMV负增长+Take Rate见顶，电商利润下滑", "probability": "25%"},
            {"description": "闪购无底洞：管理层未兑现'缩减投入'承诺，持续烧钱", "probability": "15%"},
            {"description": "FCF持续为负：回购缩减+分红压力→市场重新定价为价值陷阱", "probability": "15%"},
            {"description": "地缘冲击AIDC：中美脱钩加剧，国际业务受制裁或合规限制", "probability": "15%"},
        ],
        cognitive_biases=[
            {"bias": "'10x PE好便宜'陷阱", "risk": "Non-GAAP PE 10x是幻觉，FCF视角下真实PE~25x",
             "check": "永远用FCF而非利润定价。FCF是股东真正能拿到的钱"},
            {"bias": "阿里历史光环", "risk": "曾经的王者≠当前的护城河。不要因为历史地位给溢价",
             "check": "和当前的抖音/拼多多/腾讯横向对比，而非和5年前的阿里纵向对比"},
            {"bias": "沉没成本偏差", "risk": "如果已持有阿里，可能不愿承认3800亿AI投入可能回报不足",
             "check": "问自己：如果今天没有持仓，以当前价格会买入吗？"},
        ],
    ),

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ 3年3800亿AI投入计划(FY2026~2028)。CapEx从896亿可能升至1200亿+。FCF已从1562亿暴跌53%至739亿——这是趋势而非一次性",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", True, "3/4", [
            {"name": "核心收入增速连续2季回升", "triggered": True, "detail": "云+34%(Q4)，AIDC+29%，淘天CMR+12%"},
            {"name": "OCF margin同比扩张>3pct", "triggered": False, "detail": "OCF margin下降，因CapEx大增侵蚀"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "总CapEx占比从5%升至9%"},
            {"name": "核心竞争力指标改善", "triggered": True, "detail": "88VIP破5000万, 云AI收入三位数增长"},
        ]),
        ComboSignal("Combo C · 政策催化型", True, "3/4", [
            {"name": "监管表态明确转向友好", "triggered": True, "detail": "反垄断罚款已落地，监管转向支持"},
            {"name": "行业竞争格局收缩", "triggered": False, "detail": "拼多多+抖音电商仍在抢份额"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "AI云基建直接受益于数字经济政策"},
            {"name": "海外同类公司已先行验证", "triggered": True, "detail": "AWS/Azure验证了云AI变现路径"},
        ]),
        ComboSignal("Combo D2 · 内部人确认型", True, "3/4", [
            {"name": "公司加速回购", "triggered": True, "detail": "FY2025回购超120亿美元"},
            {"name": "管理层增持", "triggered": False, "detail": "蔡崇信/吴泳铭未公开增持"},
            {"name": "特别分红", "triggered": True, "detail": "分红+回购年化收益率~5%"},
            {"name": "资本配置动作与买入逻辑一致", "triggered": True, "detail": "回购+分红+AI投入，方向一致"},
        ]),
        ComboSignal("Combo F · 基本面恶化型", False, "1/4", [
            {"name": "OE连续2季下滑", "triggered": False, "detail": "OE同比仍增长(云+淘天拉动)"},
            {"name": "FCF转负且非高回报扩张", "triggered": True, "detail": "FCF暴跌53%至739亿，AI投入ROI未验证"},
            {"name": "CapEx扩张无回报路径", "triggered": False, "detail": "云AI收入三位数增长，有初步验证"},
            {"name": "核心市场份额持续下滑", "triggered": False, "detail": "淘天份额企稳，CMR拐点出现"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", False, "0/4", [
            {"name": "核心假设被财报否定", "triggered": False, "detail": "云拐点+淘天企稳，假设成立"},
            {"name": "竞争对手颠覆性打法", "triggered": False, "detail": "拼多多增速放缓，威胁边际减弱"},
            {"name": "管理层资本配置重大失误", "triggered": False, "detail": "3800亿AI投入需持续观察"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "监管已过最坏时期"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="阿里云+AI",
            subtitle="Reality Check — 3800亿投入的回报预期",
            metrics=[
                {"metric": "云收入(FY2025)", "value": "1180亿", "judgment": "正面", "note": "+11%，Q4加速至+34%"},
                {"metric": "AI收入增速", "value": "三位数", "judgment": "正面", "note": "连续多季三位数增长"},
                {"metric": "3年投入计划", "value": "3800亿", "judgment": "负面", "note": "FCF已腰斩，还要加码"},
                {"metric": "云利润率", "value": "拐点初现", "judgment": "中性", "note": "EBITA转正但margin仍低"},
                {"metric": "通义千问竞争力", "value": "第一梯队", "judgment": "正面", "note": "开源策略+API定价有优势"},
                {"metric": "ROI验证期", "value": "2026-2027", "judgment": "观察", "note": "2年内需看到利润率改善"},
            ],
            insight="云AI是阿里最大的战略赌注。收入增速强劲但利润率尚未证明。3800亿投入使FCF承压——如果2年内利润率未改善，OE将持续恶化。",
        ),
    ],
)

if __name__ == "__main__":
    result = run_full_analysis(financial_data, profile)
    result.deep = deep_analysis
    result.data_source = "claude_analysis_document"

    oe = result.oe_result
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier="中等质量",
        quarterly_oes=[round(oe.oe / 4, 1)] * 4,
        oe_multiple_percentile=25.0,
        structural_deterioration=False,
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, "中等质量")

    inp = ReportInput(
        company_name="阿里", ticker="9988.HK", asset_tier="中等质量",
        focus="3800亿AI投入ROI、淘天份额保卫战、FCF恢复路径",
        financial_data=financial_data, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )

    html = generate_html(inp, deep=result)
    out_path = "docs/9988_HK.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} ({len(html)//1024}KB)")
    print(f"  数据源: {result.data_source}")
    print(f"  OE: {oe.oe:.0f}亿 | 安全边际: {oe.safety_margin_pct:+.1f}%")
    print(f"  Combo A: {combo_a.triggered_count}/4 | 决策: {mx.action}")
