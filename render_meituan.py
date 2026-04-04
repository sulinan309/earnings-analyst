"""美团 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML"""

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

financial_data = FinancialData(
    cfo=cnb(-200),                  # 2025 FCF大幅为负，OCF估计也为负或极低
    maintenance_capex=cnb(100),     # 正常化维持性CapEx
    total_capex=cnb(250),           # 研发260亿+其他
    cash_and_equivalents=cnb(600),
    short_term_investments=cnb(500),
    interest_bearing_debt=cnb(200),
    committed_investments=cnb(50),
    restricted_cash=cnb(30),
    overseas_cash=cnb(100),
    revenue=cnb(3649),
    market_cap=5200.0,              # ~84 HKD × 62亿股
    period="FY2025", ticker="3690.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="2025年FCF为大幅负数(估-200至-300亿)。当前OE无意义，须用'正常化OE'方法估值",
)

profile = CompanyProfile(
    name="美团", ticker="3690.HK", asset_tier="顶级资产", period="FY2025",
    revenue_segments=[
        {"name": "核心本地商业", "fy2025": cnb(2608), "yoy": "+4.2%", "share": "71%",
         "trend": "经营利润从+524亿→-69亿。外卖GTV份额保住60%+，但代价是592亿利润蒸发"},
        {"name": "— 配送服务(Q4)", "fy2025": "236亿(Q4)", "yoy": "-9.9%", "share": "-",
         "trend": "补贴抵消实际收入"},
        {"name": "— 广告收入(Q4)", "fy2025": "131亿(Q4)", "yoy": "+2.3%", "share": "-",
         "trend": "最稳定的高质量收入"},
        {"name": "新业务(Keeta+小象)", "fy2025": cnb(1040), "yoy": "+19%", "share": "29%",
         "trend": "亏损从74亿扩大到101亿。Keeta进入沙特/科威特/阿联酋/巴西"},
    ],
    profitability_metrics=[
        {"name": "毛利率", "fy2024": "38.4%", "fy2025": "30.4%", "change": "-8.0ppt ⚠⚠"},
        {"name": "核心本地商业经营利润", "fy2024": "+524亿", "fy2025": "-69亿", "change": "-592亿 翻转"},
        {"name": "新业务经营亏损", "fy2024": "-74亿", "fy2025": "-101亿", "change": "亏损扩大"},
        {"name": "净利润", "fy2024": "+358亿", "fy2025": "-234亿", "change": "-592亿 翻转"},
        {"name": "经调整净利润", "fy2024": "+438亿", "fy2025": "-187亿", "change": "-625亿"},
        {"name": "销售营销支出", "fy2024": "640亿", "fy2025": "1029亿", "change": "+60.9% ⚠"},
        {"name": "研发投入", "fy2024": "211亿", "fy2025": "260亿", "change": "+23%"},
    ],
    profitability_insight=(
        "2025年报是五家中最戏剧性的：从年赚524亿到年亏69亿——592亿利润蒸发几乎全部来自外卖补贴大战。"
        "毛利率从38.4%暴跌至30.4%(-8ppt)，销售营销支出暴增60.9%至1029亿。"
        "但关键信号：3月25日国家市场监管总局转发《外卖大战该结束了》——监管叫停恶性竞争的明确信号。"
        "正常化利润率在12-16%(非2024年的20.9%峰值)——竞争格局已永久性改变。"
    ),
    competition_dims=[
        {"metric": "外卖GTV份额", "company_value": "60%+", "comp1_name": "饿了么", "comp1_value": "~25%", "comp2_name": "京东外卖", "comp2_value": "<5%"},
        {"metric": "核心本地商业利润", "company_value": "-69亿(战时)", "comp1_name": "饿了么", "comp1_value": "持续亏损", "comp2_name": "京东外卖", "comp2_value": "烧钱期"},
        {"metric": "到店/酒旅利润率", "company_value": "25%+", "comp1_name": "抖音团购", "comp1_value": "烧钱获客", "comp2_name": "携程", "comp2_value": "~20%"},
        {"metric": "2024年正常化利润", "company_value": "+524亿", "comp1_name": "-", "comp1_value": "-", "comp2_name": "-", "comp2_value": "-"},
        {"metric": "现金储备", "company_value": "~1100亿", "comp1_name": "阿里(饿了么母公司)", "comp1_value": "5600亿但FCF为负", "comp2_name": "京东", "comp2_value": "~2000亿"},
    ],
    moat_assessment=(
        "美团在外卖市场维持60%+ GTV份额——这是整份分析中最重要的数据点。"
        "花了大价钱但买到了份额防守。如果补贴战结束，这个份额可以重新变现为利润。"
        "补贴战是'谁先扛不住'的消耗战：阿里FCF已负数，京东外卖规模有限，监管已释放'该停了'信号。"
        "美团作为最大份额方+手持最多现金的一方，有最高概率在消耗战中存活并在战后恢复利润。"
    ),
    capex_cfo_growth=0.0,
    capex_growth_base=0.0,
    capex_growth_bear=0.20,
)

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='美团从年赚524亿到年亏69亿——外卖大战是暂时性战争创伤还是护城河永久性损伤？这个判断价值592亿',
        action="观察/持有减仓 — 当前84 HKD略高于Base(76)，处于观察区。67%集中度是最紧迫的风险",
        tldr=[
            "v4.3估值：保守35 / 基准76 / 乐观119 HKD。当前84处于观察区(Base上方10%)",
            "592亿利润翻转：核心本地商业从+524亿→-69亿，几乎全部因外卖补贴大战",
            "关键信号：监管总局转发《外卖大战该结束了》+美团保住60%+份额——战后利润恢复概率高",
            "正常化利润率12-16%(非2024年的20.9%峰值)——竞争格局已永久性改变，恢复幅度被市场高估",
        ],
        body=(
            "美团2025年报是五家分析中最戏剧性的：收入3649亿(+8%)，但净利润从+358亿直接翻转至-234亿，"
            "核心本地商业从经营溢利524亿变成亏损69亿——592亿的利润蒸发几乎全部来自外卖补贴大战。\n\n"
            "但有一个关键信号：3月25日国家市场监管总局转发《外卖大战该结束了》——市场将此解读为监管层叫停恶性竞争的明确信号。"
            "如果外卖补贴战在2026年H1确实降温，美团核心本地商业有望在2026年下半年回归正向经营利润。"
            "美团保住了60%+ GTV份额——花了大价钱但买到了份额防守。\n\n"
            "v4.3估值：正常化OE 250亿(Layer A核心业务300亿 + Layer B新业务-50亿)，g=3%, r=11%。"
            "基准内在价值76 HKD vs 当前84——略贵10%。乐观场景(补贴战结束+利润率16%)给出119 HKD。"
            "Payback 18.2年(normalized base)。不是最便宜的标的——资金优先级：快手>腾讯>美团>小米。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 外卖补贴大战何时终战（决定性力量）",
            body=(
                "2025年核心本地商业利润蒸发的直接原因：为应对阿里(淘宝闪购/饿了么)和京东的补贴攻势，"
                "美团被迫跟进大规模用户补贴。Q4单均UE约-2元，单季外卖补贴约130亿。"
                "但美团保住了60%+ GTV份额——花钱买的是份额防守而非份额流失。"
                "监管总局转发《外卖大战该结束了》是可能改变游戏规则的政策信号。"
            ),
            oe_implication="正常化OE的核心变量。补贴战结束→核心利润率从负数恢复至12-16%→OE从负数恢复至200-400亿。每延迟一个季度≈损失~80亿OE。",
        ),
        KeyForce(
            title="#2 '正常化'盈利能力——524亿是峰值不是常态",
            body=(
                "2024年核心本地商业利润524亿(利润率20.9%)是'和平峰值'——彼时阿里忙于重组、京东外卖尚未入场。"
                "2025年亏损69亿是'战时极端值'。真实正常化水平在300-400亿之间——"
                "假设竞争烈度从极端回归但不完全回到2024年水平(竞争格局已永久性改变)。"
            ),
            oe_implication="市场期望利润恢复至500亿+。我们认为正常化仅300-400亿(利润率12-16%)。这个分歧决定了Base vs Optimistic的选择。",
        ),
        KeyForce(
            title="#3 新业务(Keeta海外+小象超市)——方向正确但短期是纯费用项",
            body=(
                "新业务亏损从74亿扩大到101亿。Keeta在沙特/科威特/阿联酋/巴西扩张，"
                "小象超市进入39个城市。这些方向有长期价值(美团在中东+东南亚复制本地生活平台)，"
                "但短期是纯费用项——Layer B OE在保守/基准场景中为负。"
            ),
            oe_implication="Layer B每年拖累OE 50-100亿。如果Keeta在2027年开始在中东盈利，Layer B转正将为估值提供额外上行空间。",
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
            "本地生活网络效应是强护城河(60%份额)，但利润率波动性太大(524→-69亿)。ROIC当前为负——需等利润恢复后重新评估"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "轻多",
            "Keeta海外+小象超市+AI配送如果全部跑通，收入规模可达万亿级。但从-234亿亏损起步，想象力需要很长的跑道"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "观望",
            "当前84 HKD对应的是'利润恢复的期望值'而非'当前盈利能力'。需要等2026Q1-Q2数据确认利润拐点再行动"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "轻多",
            "如果补贴战确实结束，300亿正常化利润对应~17x PE并不贵。1100亿现金提供安全垫。但需要验证"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "看多",
            "监管叫停补贴战是明确催化剂。如果2026Q1核心业务转正→股价可能快速反弹至100+"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股beta承压+本地生活受消费信心影响。但消费复苏如果发生，美团是最直接受益者"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损30%+，最可能原因是...",
        failure_paths=[
            {"description": "补贴战不结束：阿里/京东继续砸钱，美团被迫跟进，2026年仍亏损", "probability": "25%"},
            {"description": "骑手社保成本超预期：每单+0.2-0.5元且无法转嫁→利润恢复大幅延迟", "probability": "20%"},
            {"description": "到店业务被抖音侵蚀：抖音团购持续加码，到店利润率降至15%以下", "probability": "20%"},
            {"description": "Keeta海外失败：中东地缘冲突+巴西竞争激烈，烧钱无回报", "probability": "15%"},
            {"description": "管理层战略失误：过度关注AI叙事而忽视核心业务利润恢复", "probability": "20%"},
        ],
        cognitive_biases=[
            {"bias": "锚定偏差(CRITICAL)", "risk": "Grant price ~200 HKD vs 当前84——大脑不断说'等回到200再卖'",
             "check": "200 HKD对价值判断零关系。唯一相关问题：从84出发，未来2年expected return是多少？"},
            {"bias": "沉没成本", "risk": "已经在这个仓位上浮亏58%，不愿割肉",
             "check": "浮亏是沉没成本，不应影响对未来的判断。如果今天没有持仓，以84会买入吗？"},
            {"bias": "集中度风险(最紧迫)", "risk": "12400股占总资产67%——不管估值如何，这是不可接受的风险暴露",
             "check": "Position sizing比stock picking更重要。目标减至20%以下(~3500股)"},
        ],
    ),

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ 2025年FCF为大幅负数(估-200至-300亿)。核心本地商业从盈利524亿翻转为亏损69亿——592亿利润蒸发。当前OE无意义，须用正常化方法",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", False, "0/4", [
            {"name": "核心收入增速连续2季回升", "triggered": False, "detail": "核心本地商业利润翻转为负"},
            {"name": "OCF margin同比扩张>3pct", "triggered": False, "detail": "OCF可能为负"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "不适用——整体FCF为负"},
            {"name": "核心竞争力指标改善", "triggered": False, "detail": "外卖GTV份额保住但代价是利润蒸发"},
        ]),
        ComboSignal("Combo F · 基本面恶化型", True, "3/4", [
            {"name": "OE连续2季下滑", "triggered": True, "detail": "从正OE翻转为负OE"},
            {"name": "FCF转负且非高回报扩张", "triggered": True, "detail": "FCF大幅为负，补贴抢份额非高回报投资"},
            {"name": "CapEx扩张无回报路径", "triggered": False, "detail": "Keeta海外有长期逻辑但短期烧钱"},
            {"name": "核心市场份额持续下滑", "triggered": True, "detail": "以利润换份额——份额保住但利润归零"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", True, "3/4", [
            {"name": "核心假设被财报否定", "triggered": True, "detail": "'高利润率稳定增长'假设被592亿利润蒸发彻底否定"},
            {"name": "竞争对手颠覆性打法", "triggered": True, "detail": "抖音外卖+闪购用全域流量打穿美团护城河"},
            {"name": "管理层资本配置重大失误", "triggered": True, "detail": "592亿利润换份额的ROI极差"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "无新增重大监管风险"},
        ]),
        ComboSignal("Combo E · 估值透支型", False, "1/4", [
            {"name": "市值>乐观OE估值+净现金", "triggered": False, "detail": "OE为负，传统估值框架失效"},
            {"name": "赔率<20%停止加仓", "triggered": True, "detail": "OE为负时赔率无意义"},
            {"name": "市值/OE>历史均值130%", "triggered": False, "detail": "不适用"},
            {"name": "分析师上调空间<10%", "triggered": False, "detail": "分析师大幅下调中"},
        ]),
        ComboSignal("Combo J · 时间成本型", True, "3/4", [
            {"name": "核心逻辑未证伪但2-3季未兑现", "triggered": True, "detail": "利润率修复遥遥无期"},
            {"name": "管理层持续讲故事兑现度低", "triggered": True, "detail": "Keeta烧钱进度远超收入"},
            {"name": "资金占用过久替代机会更优", "triggered": True, "detail": "快手/腾讯赔率远优于美团"},
            {"name": "市场不给估值的关键原因未变", "triggered": False, "detail": "竞争格局恶化是核心原因"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="外卖核心业务",
            subtitle="Reality Check — 利润率崩塌分析",
            metrics=[
                {"metric": "外卖GTV份额", "value": "60%+", "judgment": "正面", "note": "保住了份额"},
                {"metric": "核心本地商业利润", "value": "-69亿", "judgment": "负面", "note": "从+524亿翻转，-592亿"},
                {"metric": "配送收入(Q4)", "value": "236亿(-9.9%)", "judgment": "负面", "note": "补贴侵蚀"},
                {"metric": "单均利润", "value": "大幅恶化", "judgment": "负面", "note": "补贴战+运力成本上升"},
                {"metric": "抖音外卖威胁", "value": "持续加大", "judgment": "负面", "note": "全域流量优势明显"},
                {"metric": "利润率恢复时间", "value": "2026H2最早", "judgment": "观察", "note": "取决于竞争格局变化"},
            ],
            insight="美团以592亿利润换取60%份额——ROI极差。这不是暂时的战术让步，而是结构性的竞争格局恶化。利润率恢复至少需要2-3个季度。",
        ),
        CoreProduct(
            name="Keeta海外",
            subtitle="Reality Check — 烧钱扩张节奏",
            metrics=[
                {"metric": "已进入市场", "value": "沙特/科威特/阿联酋/巴西", "judgment": "中性", "note": "扩张速度快"},
                {"metric": "新业务亏损", "value": "101亿(+36%)", "judgment": "负面", "note": "亏损还在扩大"},
                {"metric": "收入增速", "value": "+19%", "judgment": "中性", "note": "增长不够快"},
                {"metric": "盈亏平衡预期", "value": "2028+", "judgment": "负面", "note": "遥远且不确定"},
            ],
            insight="Keeta的'国际化美团'故事有想象力但烧钱速度令人担忧。在核心业务利润崩塌的情况下，海外扩张的资金来源是个大问题。",
        ),
    ],
)

if __name__ == "__main__":
    result = run_full_analysis(financial_data, profile)
    result.deep = deep_analysis
    result.data_source = "claude_analysis_document"

    oe = result.oe_result
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier="顶级资产",
        quarterly_oes=[round(max(oe.oe, 1) / 4, 1)] * 4,  # OE可能为负，取max
        oe_multiple_percentile=80.0,  # 当前估值不在低分位
        structural_deterioration=True,  # 利润结构恶化
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, "顶级资产")

    inp = ReportInput(
        company_name="美团", ticker="3690.HK", asset_tier="顶级资产",
        focus="外卖补贴战终战时点、正常化利润率恢复、67%集中度减仓",
        financial_data=financial_data, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )

    html = generate_html(inp, deep=result)
    out_path = "docs/3690_HK.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} ({len(html)//1024}KB)")
    print(f"  数据源: {result.data_source}")
    print(f"  OE: {oe.oe:.0f}亿 | 安全边际: {oe.safety_margin_pct:+.1f}%")
    print(f"  Combo A: {combo_a.triggered_count}/4 | 决策: {mx.action}")
