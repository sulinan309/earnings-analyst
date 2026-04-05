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
    cfo=cnb(350),                   # 正常化CFO：2024年OCF~480亿，竞争打折后~350亿(含新业务现金消耗)
    maintenance_capex=cnb(100),     # 正常化维持性CapEx估算
    total_capex=cnb(250),           # 研发260亿+其他
    cash_and_equivalents=cnb(1067.71),  # 年末现金及等价物 [A]
    short_term_investments=cnb(600.62),  # 短期treasury investments [A]
    interest_bearing_debt=cnb(200),
    committed_investments=cnb(50),
    restricted_cash=cnb(30),
    overseas_cash=cnb(100),
    revenue=cnb(3649),
    market_cap=5200.0,              # ~84 HKD × 62亿股
    period="FY2025", ticker="3690.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="⚠ 2025年为战时极端值(OCF -138亿[A])，此处使用正常化OE：2024年核心业务利润524亿(利润率20.9%)做竞争折扣→正常化利润率~11.5%→Layer A 300亿 + Layer B -50亿 = Base OE 250亿 RMB",
)

profile = CompanyProfile(
    name="美团", ticker="3690.HK", asset_tier="顶级资产", period="FY2025",
    revenue_segments=[
        {"name": "核心本地商业", "fy2025": 2608, "yoy": "+4.2%", "share": "71%",
         "trend": "经营利润: +524亿→-69亿 [A]。GTV份额60%+(媒体测算)，代价592亿利润蒸发"},
        {"name": "— 配送服务(Q4)", "fy2025": 261.95, "yoy": "同比下降", "share": "-",
         "trend": "补贴侵蚀实际收入 [A]"},
        {"name": "— 佣金收入(Q4)", "fy2025": 240.66, "yoy": "-", "share": "-",
         "trend": "稳定"},
        {"name": "— 在线营销(Q4)", "fy2025": 128.42, "yoy": "+2.3%", "share": "-",
         "trend": "最稳定的高质量收入 [A]"},
        {"name": "新业务(Keeta+小象)", "fy2025": 1040, "yoy": "+19%", "share": "29%",
         "trend": "亏损74→101亿 [A]。Keeta进入沙特/科威特/阿联酋/巴西。小象进入39城"},
    ],
    profitability_metrics=[
        {"name": "收入", "fy2024": "3,376亿", "fy2025": "3,649亿", "change": "+8%"},
        {"name": "毛利率", "fy2024": "38.4%", "fy2025": "30.4%", "change": "-8.0ppt ⚠⚠"},
        {"name": "经营利润", "fy2024": "+451亿", "fy2025": "-170亿", "change": "-621亿 翻转"},
        {"name": "核心本地商业经营利润", "fy2024": "+524亿", "fy2025": "-69亿", "change": "-592亿 翻转"},
        {"name": "新业务经营亏损", "fy2024": "-74亿", "fy2025": "-101亿", "change": "-36% 亏损扩大"},
        {"name": "净利润", "fy2024": "+358亿", "fy2025": "-234亿", "change": "-592亿 翻转"},
        {"name": "经调整净利润", "fy2024": "+438亿", "fy2025": "-187亿", "change": "-625亿"},
        {"name": "经营活动现金流", "fy2024": "+480亿(估)", "fy2025": "-138亿", "change": "-618亿 翻转"},
    ],
    profitability_insight=(
        "2025年报是五家中最戏剧性的：收入3649亿(+8%)，但净利润从+358亿翻转至-234亿 [A]。"
        "毛利率从38.4%暴跌至30.4%(-8ppt)——年报将原因归结为即时零售行业竞争加剧导致的毛利率下降和用户激励、"
        "营销推广开支大幅增加 [A]。OCF也从正~480亿翻转至-138亿——比利润亏损更严重。"
        "但关键信号：监管总局转发《外卖大战该结束了》[C]。正常化利润率12-16%(非2024年峰值20.9%)。"
    ),
    competition_dims=[
        {"metric": "外卖GTV份额(媒体测算)", "company_value": "60%+", "comp1_name": "饿了么", "comp1_value": "~25%", "comp2_name": "京东外卖", "comp2_value": "<5%(新入局)"},
        {"metric": "核心本地商业经营利润", "company_value": "-69亿(战时)", "comp1_name": "饿了么", "comp1_value": "持续亏损", "comp2_name": "京东外卖", "comp2_value": "烧钱期"},
        {"metric": "到店/酒旅利润率", "company_value": "25%+(利润率有所下降)", "comp1_name": "抖音团购", "comp1_value": "加码中", "comp2_name": "携程", "comp2_value": "~20%"},
        {"metric": "2024年和平峰值利润", "company_value": "+524亿(利润率20.9%)", "comp1_name": "-", "comp1_value": "-", "comp2_name": "-", "comp2_value": "-"},
        {"metric": "现金+短期投资[A]", "company_value": "1669亿", "comp1_name": "阿里(饿了么)", "comp1_value": "FCF为负,持续投入受限", "comp2_name": "京东", "comp2_value": "~2000亿"},
    ],
    moat_assessment=(
        "美团在外卖市场维持60%+ GTV份额(媒体测算)——花了大价钱买到份额防守。"
        "年末现金+短期投资合计1669亿 [A]，短期无流动性危机。"
        "补贴战是消耗战：阿里FY2025 FCF暴跌53%至739亿 [A]，FY2026H1 FCF净流出407亿——持续补贴的财务能力受限。"
        "京东外卖新入局规模有限。监管已释放《外卖大战该结束了》信号 [C]。"
        "美团作为最大份额方+现金储备最充裕方，在消耗战中存活并在战后恢复利润的概率最高。"
    ),
    capex_cfo_growth=0.0,
    capex_growth_base=0.0,
    capex_growth_bear=0.20,
)

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='美团从年赚524亿到年亏69亿——外卖大战是暂时性战争创伤还是护城河永久性损伤？这个判断价值592亿',
        action="Hold existing + 加速减仓 — 当前84 HKD刚进入观察区(Base 81上方)。67%集中度是最紧迫的风险",
        tldr=[
            "v4.3估值：Conservative 40 / Base 81 / Optimistic 125 HKD。当前84刚进入观察区",
            "Hold existing employee shares + 加速减仓节奏 — 不是因为不看好，而是因为67%集中度风险",
            "最关键Key Force：外卖大战何时结束→核心本地商业何时回归正常化盈利",
            "正常化利润率12-16%(非2024年峰值20.9%)——三方竞争格局已形成，恢复幅度被市场高估",
        ],
        body=(
            "美团2025年报是五家分析中最戏剧性的一份：收入3649亿(+8%)，但净利润从+358亿直接翻转至-234亿，"
            "经调整净亏损187亿 [A]。核心本地商业从经营溢利524亿变成亏损69亿 [A]——年报将原因归结为即时零售行业"
            "竞争加剧导致的毛利率下降和用户激励、营销推广开支大幅增加 [A]。592亿的利润蒸发是近年中国互联网最大的单年利润翻转。\n\n"
            "但有一个关键信号：3月25日国家市场监督管理总局转发经济日报《外卖大战该结束了》[C]——市场将此解读为"
            "监管层叫停恶性竞争的明确信号。如果外卖补贴战在2026年H1确实降温，美团核心本地商业有望在2026年下半年回归正向经营利润。\n\n"
            "v4.3正常化估值：Layer A(核心业务正常化利润300亿, 利润率~11.5%) + Layer B(新业务-50亿) = Base OE 250亿。"
            "g=3%, r=11%给出Base per share 81 HKD。当前84刚进入观察区。"
            "Payback 18.2年(normalized)。现金储备充裕(现金+投资1669亿 [A])，短期无流动性危机。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 外卖补贴大战何时终战（决定性力量）",
            body=(
                "2025年核心本地商业利润蒸发的直接原因：年报将其归结为即时零售行业竞争加剧 [A]。"
                "竞争主要来自阿里(淘宝闪购/饿了么)和京东外卖的进入。核心本地商业从经营溢利+524亿翻转为亏损-69亿 [A]。"
                "美团保住了60%+ GTV市场份额(媒体/卖方测算)——花钱买的是份额防守而非份额流失。"
                "经济日报发文《外卖大战该结束了》[C]是可能改变游戏规则的政策信号。"
                "阿里FY2025 FCF暴跌53%至739亿 [A]，FY2026H1 FCF净流出407亿——持续大规模补贴的财务能力受限。"
            ),
            oe_implication="正常化OE的核心变量。补贴战结束→核心利润率从负数恢复至12-16%→OE从负数恢复至200-400亿。每延迟一个季度≈损失~80亿OE。",
        ),
        KeyForce(
            title="#2 '正常化'盈利能力——524亿是和平峰值不是常态",
            body=(
                "2024年核心本地商业经营利润524亿(利润率20.9%)[A]——这是'和平峰值'，彼时阿里忙于重组、京东外卖尚未入场。"
                "2025年亏损69亿——这是'战时极端值'。真实正常化水平：保守200亿(利润率~7.7%)、基准300亿(~11.5%)、乐观400亿(~15.3%)。"
                "三方竞争格局(美团/阿里/京东)已形成，即使补贴战结束，利润率也很难回到20%+。"
            ),
            oe_implication="市场共识期望利润恢复至500亿+——我们认为正常化仅300-400亿(利润率12-16%)。这个分歧决定了估值。",
        ),
        KeyForce(
            title="#3 新业务(Keeta海外+小象超市)——方向正确但短期纯费用项",
            body=(
                "新业务亏损从74亿扩大到101亿 [A]。Keeta已进入沙特、科威特、阿联酋、巴西 [A]。"
                "小象超市进入39个城市 [A]。Q4香港Keeta已实现UE(单位经济)转正 [A]——方向正确。"
                "但短期是纯费用项——Layer B OE在保守/基准场景中均为负数。"
            ),
            oe_implication="Layer B每年拖累OE 50-100亿。如果Keeta在2027年中东市场盈利，Layer B转正将提供额外上行。",
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
            "本地生活网络效应是强护城河(60%份额)，但利润率波动极大(524→-69亿)。ROIC当前为负——需等利润恢复后重新评估"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "轻多",
            "Keeta海外+小象超市+AI配送全部跑通→收入可达万亿级。但从-234亿亏损起步，想象力需要很长跑道"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "观望",
            "84 HKD对应的是'利润恢复期望值'而非'当前盈利能力'。需等2026Q1-Q2数据确认利润拐点再行动"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "轻多",
            "补贴战结束后300亿正常化利润对应~17x PE不贵。现金+投资1669亿 [A]提供安全垫。需验证"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "看多",
            "监管叫停补贴战是明确催化剂[C]。2026Q1核心业务如转正→股价可能快速反弹至100+"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股beta承压+本地生活受消费信心影响。但消费复苏时美团是最直接受益者"),
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
             "check": "浮亏是沉没成本，不应影响对未来的判断。问自己：如果今天没有持仓，以84会买入吗？"},
            {"bias": "集中度风险(最紧迫)", "risk": "12400股占总资产67%——不管估值如何，这是不可接受的风险暴露",
             "check": "Position sizing比stock picking更重要。目标减至20%以下(~3500股)。每两周卖500股"},
        ],
    ),

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ 2025年OCF -138亿 [A]，FCF深度负值。核心本地商业从盈利524亿翻转为亏损69亿——592亿利润蒸发。当前OE无意义，须用'正常化OE'(Layer A+B分层)方法估值",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", False, "0/4", [
            {"name": "核心收入增速连续2季回升", "triggered": False, "detail": "核心本地商业利润翻转为负(-69亿)[A]，收入+4.2%但利润方向相反"},
            {"name": "OCF margin同比扩张>3pct", "triggered": False, "detail": "OCF -138亿[A]，从正~480亿翻转，摆幅618亿"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "FCF为负，CapEx讨论不适用"},
            {"name": "核心竞争力指标改善", "triggered": False, "detail": "GTV份额保住60%+(媒体测算)但代价是592亿利润[A]"},
        ]),
        ComboSignal("Combo C · 政策催化型", True, "3/4", [
            {"name": "监管表态明确转向友好", "triggered": True, "detail": "监管总局转发《外卖大战该结束了》[C]——叫停恶性竞争的明确信号"},
            {"name": "行业竞争格局收缩", "triggered": True, "detail": "阿里FCF转负→补贴持续力受限，京东外卖规模有限"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "美团作为市场领导者(60%份额)最先受益于竞争降温"},
            {"name": "海外同类公司已先行验证", "triggered": False, "detail": "外卖补贴战无海外先例可参照"},
        ]),
        ComboSignal("Combo F · 基本面恶化型", True, "3/4", [
            {"name": "OE连续2季下滑", "triggered": True, "detail": "OE从正翻转为负——整个2025年为战时极端值[A]"},
            {"name": "FCF转负且非高回报扩张", "triggered": True, "detail": "OCF -138亿[A]，补贴抢份额而非高回报投资"},
            {"name": "CapEx扩张无回报路径", "triggered": False, "detail": "Keeta香港UE已转正[A]，海外有初步验证"},
            {"name": "核心市场份额持续下滑", "triggered": True, "detail": "份额保住(60%+)但代价是核心业务利润归零[A]"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", True, "3/4", [
            {"name": "核心假设被财报否定", "triggered": True, "detail": "'高利润率稳定增长'假设被592亿利润蒸发彻底否定[A]"},
            {"name": "竞争对手颠覆性打法", "triggered": True, "detail": "阿里(闪购/饿了么)+京东外卖双线夹击，竞争格局永久改变"},
            {"name": "管理层资本配置重大失误", "triggered": True, "detail": "592亿利润换60%份额的ROI极差——但可能是'没有选择的选择'"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "无新增监管风险，反而有利好信号(叫停补贴)[C]"},
        ]),
        ComboSignal("Combo J · 时间成本型", True, "3/4", [
            {"name": "核心逻辑未证伪但2-3季未兑现", "triggered": True, "detail": "利润率恢复至少要2026H2，2-3个季度后才能验证"},
            {"name": "管理层持续讲故事兑现度低", "triggered": True, "detail": "Keeta海外烧钱进度远超收入，新业务亏损扩大36%[A]"},
            {"name": "资金占用过久替代机会更优", "triggered": True, "detail": "快手(明确加仓区)、腾讯(观察区)赔率远优于美团"},
            {"name": "市场不给估值的关键原因未变", "triggered": False, "detail": "竞争格局恶化是根因，但监管信号[C]可能改变"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="外卖核心业务",
            subtitle="正常化利润率推导 — Layer A分析",
            metrics=[
                {"metric": "GTV份额(媒体测算)", "value": "60%+", "judgment": "正面", "note": "花钱买到份额防守而非份额流失"},
                {"metric": "核心本地商业利润[A]", "value": "-69亿", "judgment": "负面", "note": "从+524亿翻转，-592亿蒸发"},
                {"metric": "OCF[A]", "value": "-138亿", "judgment": "负面", "note": "比利润亏损更严重——核心经营在消耗现金"},
                {"metric": "2024和平峰值利润率", "value": "20.9%", "judgment": "中性", "note": "竞争真空期峰值，不可作为正常化基准"},
                {"metric": "正常化利润率(我们判断)", "value": "12-16%", "judgment": "观察", "note": "三方格局→保守7.7%/基准11.5%/乐观15.3%"},
                {"metric": "Layer A正常化OE", "value": "200-400亿", "judgment": "观察", "note": "保守200/基准300/乐观400"},
                {"metric": "监管信号", "value": "《外卖大战该结束了》[C]", "judgment": "正面", "note": "可能改变游戏规则的政策信号"},
                {"metric": "利润率恢复时间", "value": "2026H2最早", "judgment": "观察", "note": "取决于监管是否实质介入"},
            ],
            insight="592亿利润蒸发的关键判断：'战时极端值'而非'新常态'。但恢复幅度被市场高估——正常化利润率12-16%而非市场期望的20%+。三方竞争格局已永久形成。",
        ),
        CoreProduct(
            name="Keeta海外 + 小象超市",
            subtitle="Layer B分析 — 新业务烧钱与前景",
            metrics=[
                {"metric": "新业务收入[A]", "value": "1040亿(+19%)", "judgment": "中性", "note": "增速尚可但不够快"},
                {"metric": "新业务亏损[A]", "value": "-101亿(+36%)", "judgment": "负面", "note": "亏损率9.7%，从-74亿扩大"},
                {"metric": "Keeta已进入市场[A]", "value": "沙特/科威特/阿联酋/巴西", "judgment": "中性", "note": "扩张速度快"},
                {"metric": "香港Keeta UE[A]", "value": "已转正", "judgment": "正面", "note": "Q4验证单位经济模型可行"},
                {"metric": "小象超市[A]", "value": "39城", "judgment": "中性", "note": "产能建设期"},
                {"metric": "Layer B正常化OE", "value": "-80~-20亿", "judgment": "负面", "note": "保守-80/基准-50/乐观-20"},
            ],
            insight="Layer B目前拖累合并OE 50-100亿/年。Keeta香港UE转正是积极信号，但中东/巴西验证需时间。在核心业务利润崩塌的背景下，新业务烧钱节奏需更审慎。",
        ),
        CoreProduct(
            name="现金储备与存活能力",
            subtitle="消耗战弹药盘点",
            metrics=[
                {"metric": "年末现金[A]", "value": "1,068亿", "judgment": "正面", "note": "远超预期"},
                {"metric": "短期投资[A]", "value": "601亿", "judgment": "正面", "note": "Treasury investments"},
                {"metric": "合计可用资金[A]", "value": "1,669亿", "judgment": "正面", "note": "短期无流动性危机"},
                {"metric": "年消耗速度", "value": "~100-200亿/年", "judgment": "负面", "note": "OCF -138亿+持续补贴"},
                {"metric": "可支撑时间(无融资)", "value": "8-16年", "judgment": "正面", "note": "消耗战弹药极其充裕"},
                {"metric": "调整净现金(HKD)", "value": "1,366亿", "judgment": "正面", "note": "扣除预期消耗和债务后"},
            ],
            insight="美团在消耗战中最大的底牌：1669亿现金+投资。即使年消耗200亿也可支撑8年以上。对手中阿里FCF已转负、京东外卖投入意愿存疑——美团有最高概率'耗到最后'。",
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
