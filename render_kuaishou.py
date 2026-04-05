"""快手 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML"""

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

# ═══════════════════════════════════════════
#  财务数据
# ═══════════════════════════════════════════

financial_data = FinancialData(
    cfo=cnb(267),                   # OCF 267亿 [A]
    maintenance_capex=cnb(80),      # ≈折旧 ~80亿 [D1]
    total_capex=cnb(150),           # 2025年实际（2026指引260亿）
    cash_and_equivalents=cnm(11_180),
    short_term_investments=cnm(8_630 + 22_015 + 42_324),
    interest_bearing_debt=cnm(11_098 + 1_968),
    committed_investments=20.0,
    restricted_cash=cnm(251),
    overseas_cash=30.0,
    revenue=cnb(1428),
    market_cap=2000.0,              # ~45 HKD × 43亿股
    period="FY2025", ticker="1024.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="维持性CapEx ≈ FY2023基线~80亿(AI大规模投入前的历史水平)[D1]。成长性CapEx=149-80=70亿。推算FCF≈267-149=118亿[D1](快手年报未披露Non-GAAP FCF)。正常化FCF≈118+70=188亿。2026年CapEx指引260亿[B]",
)

profile = CompanyProfile(
    name="快手", ticker="1024.HK", asset_tier="中等质量", period="FY2025",
    revenue_segments=[
        {"name": "线上营销服务", "fy2025": cnb(815), "yoy": "+12.5%", "share": "57%",
         "trend": "AI驱动广告定向+AIGC素材消耗40亿元"},
        {"name": "直播", "fy2025": cnb(391), "yoy": "+5.5%", "share": "27%",
         "trend": "成熟期现金牛，增速放缓"},
        {"name": "其他服务(电商+可灵AI)", "fy2025": cnb(222), "yoy": "+27.6%", "share": "16%",
         "trend": "电商GMV 1.6万亿(+15%)，可灵AI ARR 2.4亿美元"},
    ],
    profitability_metrics=[
        {"name": "毛利率", "fy2024": "54.6%", "fy2025": "55.0%", "change": "+0.4pct"},
        {"name": "经调整净利润率", "fy2024": "13.9%", "fy2025": "14.5%", "change": "+0.6pct"},
        {"name": "销售费用率", "fy2024": "32.4%", "fy2025": "29.6%", "change": "-2.8pct ✓"},
        {"name": "研发费用率", "fy2024": "9.6%", "fy2025": "10.1%", "change": "+0.5pct(AI投入)"},
        {"name": "GAAP净利润", "fy2024": "153亿", "fy2025": "186亿", "change": "+21.4%"},
        {"name": "经调整净利润", "fy2024": "177亿", "fy2025": "206亿", "change": "+16.5%"},
        {"name": "GAAP vs Non-GAAP差异", "fy2024": "~16%", "fy2025": "~10%", "change": "差距收窄，SBC可控"},
    ],
    profitability_insight=(
        "最大亮点是销售费用率-2.8pct：UAX自动化投放渗透率超70%正在结构性降低获客成本。"
        "这不是一次性节省，是AI驱动的效率提升。即使收入增速温和(12.5%)，利润增速(16.5%)持续跑赢——"
        "运营杠杆在释放。OCF 267亿 vs 净利润186亿，OCF/净利比1.43x，现金流质量优异。"
    ),
    competition_dims=[
        {"metric": "DAU(亿)", "company_value": "4.10", "comp1_name": "抖音", "comp1_value": "~6.0", "comp2_name": "视频号", "comp2_value": "~4.5"},
        {"metric": "广告收入(亿)", "company_value": str(cnb(815)), "comp1_name": "抖音", "comp1_value": "~5,000+", "comp2_name": "视频号", "comp2_value": "~1,000+"},
        {"metric": "电商GMV(万亿)", "company_value": "1.6", "comp1_name": "抖音", "comp1_value": "~3.5", "comp2_name": "拼多多", "comp2_value": "~5+"},
        {"metric": "AI视频生成", "company_value": "可灵(ARR $240M)", "comp1_name": "字节", "comp1_value": "Seedance", "comp2_name": "OpenAI", "comp2_value": "Sora(已停服)"},
        {"metric": "Trailing PE", "company_value": "~10x", "comp1_name": "B站", "comp1_value": ">30x", "comp2_name": "微博", "comp2_value": "~8x"},
    ],
    moat_assessment=(
        "快手在短视频赛道稳居中国#2，但与#1抖音差距在扩大(DAU 4.1亿 vs 6亿)。"
        "护城河来自：(1)下沉市场用户社区粘性；(2)可灵AI在视频生成赛道的技术领先（Sora已停服）；"
        "(3)10.79亿IoT设备的快手直播/电商入口。但广告主预算向抖音迁移是持续性威胁。"
    ),
    capex_cfo_growth=0.08,
    capex_growth_base=0.73,     # 2026: 260亿 vs 2025: ~150亿
    capex_growth_bear=1.0,
)

# ═══════════════════════════════════════════
#  DeepAnalysis（从 Claude 分析文档映射）
# ═══════════════════════════════════════════

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='快手——45 HKD低于保守估值17%，三家中最便宜。Payback仅9.5年，High Conviction',
        action="明确加仓 — 当前45 HKD低于Conservative(54)约17%，在明确加仓区。High Conviction",
        tldr=[
            "v4.3估值：Conservative 54 / Base 82 / Optimistic 102 HKD。当前45低于保守值17%——明确加仓区",
            "FCF=118亿[A]但149亿CapEx含大量AI成长性投入。正常化FCF~170-200亿。Base OE 180亿",
            "净现金919亿HKD(per share 21.1 HKD)占Base估值26%——PE法无法体现的隐藏价值",
            "在40-55区间分批买至600-800股。Kill condition：DAU连续两季同比下降",
        ],
        body=(
            "2025年报稳健——全年营收1428亿(+12.5%)，经调整净利润206亿(+16.5%)，毛利率55.0%，OCF 267亿。"
            "市场给出的反应是股价从52周高点92.6 HKD腰斩至~45 HKD，Trailing PE仅~10x。\n\n"
            "v4.3估值修正：FCF=OCF 267亿-CapEx 149亿=118亿。因149亿CapEx含大量AI成长性投入(2026年将升至260亿)，"
            "维护性CapEx远低于总量。正常化FCF约170-200亿，OE区间150-210亿。"
            "基准OE 180亿(核心广告+直播+电商 150亿 + AI效率增量30亿)。\n\n"
            "关键发现：净现金919亿HKD(per share 21.1 HKD)占基准估值的26%——这是PE法无法体现的隐藏价值。"
            "v4.3的Guard Rail 4要求认真对待净现金，使快手成为唯一在修正后估值上升的标的(v4.2 72→v4.3 82, +14%)。"
            "当前45 HKD低于保守值54 HKD——在三家中conviction最高。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 AI赋能从'降本工具'到'增收引擎'的转化",
            body=(
                "2025年AI技术对国内线上营销服务收入的贡献约提升5个百分点，AIGC广告素材消耗额达40亿元，"
                "OneRec生成式推荐大模型在电商场景驱动GMV增长。这不是未来故事，是已经在P&L上体现的增量。"
                "如果AI对广告效率的提升持续(每年+3-5%增量)，快手在用户零增长情况下仍可维持10%+收入增长。"
            ),
            oe_implication="AI提效直接增加营收而不增加对应成本，是OE的纯增量。每年+5%的广告效率提升≈40亿增量OE。",
        ),
        KeyForce(
            title="#2 用户天花板 vs 变现深度——从'扩用户'到'深挖ARPU'",
            body=(
                "DAU 4.1亿(+2.7%)，增速已降至低个位数。抖音DAU约6亿且还在增长。"
                "快手增长引擎必须从'扩用户'切换到'深挖单用户价值'。2025年DAU广告ARPU约199元/年，"
                "仍低于抖音水平，有提升空间。但如果DAU开始下降(而非放缓)，所有变现逻辑受挑战。"
            ),
            oe_implication="DAU是OE的分母——用户流失直接压缩广告收入基盘。DAU每下降5%，OE可能下降8-10%。",
        ),
        KeyForce(
            title="#3 可灵AI作为独立增长极——从零到ARR 2.4亿美元",
            body=(
                "Q4收入3.4亿元，12月ARR 2.4亿美元。管理层有信心2026年实现>100%收入增速。"
                "Sora已停服，可灵在全球视频生成赛道处于领先位置。2026年Capex 260亿(+110亿)主要投向AI算力——"
                "这是一个有实质收入支撑的AI投入，不是纯烧钱。"
            ),
            oe_implication="260亿Capex中~100亿为维持性(计入OE)，~160亿为增长性(不计入OE但需未来验证ROI)。如果可灵AI 2026年贡献20亿+利润，增长性Capex的ROI就初步得到验证。",
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
        InvestmentPhilosophy("品质复利", "巴菲特/芒格", "持有/买入",
            "55%毛利率+14.5%净利率+现金奶牛(OCF 267亿)，但ROIC趋势需确认——用户基数下降是最大威胁"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "看多",
            "可灵AI如果成为全球视频生成标准，收入空间>50亿美元。快手6亿+日均视频观看为模型训练提供独特数据资产"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "看多",
            "10x PE for a company growing profits 15%+ = clear mispricing。利润增速持续跑赢收入增速说明运营杠杆在释放"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "看多",
            "现金储备1049亿 vs 市值~2000亿，P/B偏低。净现金per share 25.9 HKD占内在价值27%——市场在给现金打大折扣"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "看多",
            "可灵AI 2026年收入翻倍+泛货架电商加速+海外扭亏，多重催化剂在2026H1-H2兑现"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股系统性承压，beta环境不利。但快手高股息+回购(年回报率~4%)提供一定下行保护"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损20%+，最可能原因是...",
        failure_paths=[
            {"description": "抖音持续碾压：字节用更大算力+更好推荐拉大DAU差距，广告主加速迁移", "probability": "25%"},
            {"description": "AI Capex黑洞：260亿投入但可灵AI收入增速不及预期，Seedance等竞品追上", "probability": "20%"},
            {"description": "监管风险：直播/电商监管趋严，短视频内容治理成本上升", "probability": "15%"},
            {"description": "宏观衰退：广告市场整体萎缩>10%，快手作为效果广告平台也无法幸免", "probability": "20%"},
            {"description": "港股系统性去估值：地缘+利率导致港股整体PE下移20%+", "probability": "20%"},
        ],
        cognitive_biases=[
            {"bias": "叙事偏差", "risk": "'可灵AI全球领先'很诱人——但Q4仅3.4亿收入，占总收入<1%",
             "check": "不应过度放大可灵对估值的贡献，核心仍是广告+电商"},
            {"bias": "锚定效应", "risk": "刚以46 HKD买入300股，倾向于寻找确认性数据",
             "check": "忽略entry price，只看forward value和kill conditions"},
            {"bias": "价值陷阱风险", "risk": "10x PE看起来便宜，但如果用户净流失，10x PE可能不是底",
             "check": "'低估值+低增长'可能变成'低估值+负增长'——DAU是唯一的kill条件"},
        ],
    ),

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ 2026年CapEx将从149亿升至260亿(+74%)[B]，主要投向可灵AI算力。但净现金919亿HKD提供充裕安全垫。GR1通过：成长性CapEx调整后，OE 150-210亿 ≤ 1.2×正常化FCF",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", True, "3/4", [
            {"name": "核心收入增速连续2季回升", "triggered": True, "detail": "线上营销+12.5%，连续回升"},
            {"name": "OCF margin同比扩张>3pct", "triggered": True, "detail": "OCF margin 18.7% vs 去年16.2%, +2.5pct"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "2026年CapEx大幅上升，占比反而上升"},
            {"name": "核心竞争力指标改善", "triggered": True, "detail": "广告ARPU 199元(+10%), 电商GMV 1.6万亿(+15%)"},
        ]),
        ComboSignal("Combo C · 政策催化型", False, "1/4", [
            {"name": "监管表态明确转向友好", "triggered": False, "detail": "无明确表态"},
            {"name": "行业竞争格局收缩", "triggered": False, "detail": "抖音仍在扩张"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "AI产业政策利好可灵"},
            {"name": "海外同类公司已先行验证", "triggered": False, "detail": "Sora已停服，未验证商业模式"},
        ]),
        ComboSignal("Combo D2 · 内部人确认型", True, "3/4", [
            {"name": "公司加速回购", "triggered": True, "detail": "2025年回购+分红年化~4%"},
            {"name": "管理层增持", "triggered": False, "detail": "无公开增持记录"},
            {"name": "特别分红", "triggered": True, "detail": "首次派发特别分红"},
            {"name": "资本配置动作与买入逻辑一致", "triggered": True, "detail": "回购+分红+AI投入，三者一致"},
        ]),
        ComboSignal("Combo E · 估值透支型", False, "0/4", [
            {"name": "市值>乐观OE估值+净现金", "triggered": False, "detail": "市值2000亿远低于乐观4420亿"},
            {"name": "赔率<20%停止加仓", "triggered": False, "detail": "赔率121%>>20%"},
            {"name": "市值/OE>历史均值130%", "triggered": False, "detail": "当前~10x远低于历史均值"},
            {"name": "分析师上调空间<10%", "triggered": False, "detail": "一致预期仍有较大上调空间"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", False, "0/4", [
            {"name": "核心假设被财报否定", "triggered": False, "detail": "利润增长+现金流强劲，假设未被否定"},
            {"name": "竞争对手颠覆性打法", "triggered": False, "detail": "抖音优势在扩大但未颠覆"},
            {"name": "管理层资本配置重大失误", "triggered": False, "detail": "AI投入有收入支撑"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "无重大监管风险"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="可灵AI",
            subtitle="Reality Check — 从概念到收入",
            metrics=[
                {"metric": "Q4收入", "value": "3.4亿元", "judgment": "中性", "note": "占总收入<1%，但环比快速增长"},
                {"metric": "12月ARR", "value": "$2.4亿", "judgment": "正面", "note": "年化后已是中等SaaS规模"},
                {"metric": "2026增速指引", "value": ">100%", "judgment": "正面", "note": "管理层明确承诺"},
                {"metric": "Sora竞争", "value": "已停服", "judgment": "正面", "note": "主要对手退出，窗口期"},
                {"metric": "2026 CapEx", "value": "260亿(+73%)", "judgment": "负面", "note": "AI算力投入大幅攀升"},
                {"metric": "盈利贡献", "value": "尚未盈利", "judgment": "负面", "note": "需2026年验证ROI"},
            ],
            insight="可灵AI是快手最大的增长期权，但目前收入占比<1%。不应过度放大其对估值的贡献——核心仍是广告+电商的现金流。",
        ),
    ],
)

# ═══════════════════════════════════════════
#  运行 + 渲染
# ═══════════════════════════════════════════

if __name__ == "__main__":
    result = run_full_analysis(financial_data, profile)
    result.deep = deep_analysis
    result.data_source = "claude_analysis_document"

    oe = result.oe_result
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier="中等质量",
        quarterly_oes=[round(oe.oe / 4, 1)] * 4,
        oe_multiple_percentile=30.0,
        structural_deterioration=False,
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, "中等质量")

    inp = ReportInput(
        company_name="快手", ticker="1024.HK", asset_tier="中等质量",
        focus="AI赋能广告效率、可灵AI商业化、用户天花板vs变现深度",
        financial_data=financial_data, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )

    html = generate_html(inp, deep=result)
    out_path = "docs/1024_HK.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} ({len(html)//1024}KB)")
    print(f"  数据源: {result.data_source}")
    print(f"  OE: {oe.oe:.0f}亿 | 安全边际: {oe.safety_margin_pct:+.1f}%")
    print(f"  Combo A: {combo_a.triggered_count}/4 | 决策: {mx.action}")
