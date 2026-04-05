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
    cfo=cnb(1635.09),               # OCF 1635.09亿 [A]
    maintenance_capex=cnb(500),     # 正常化维持性CapEx（存量电商+云维护，v3桥梁表基准CapEx 550亿中的维持性部分）
    total_capex=cnb(896.39),        # FCF口径CapEx 896.39亿 [A]（不含办公园区土地/在建工程/版权媒体）
    cash_and_equivalents=cnb(2000),
    short_term_investments=cnb(3000),
    interest_bearing_debt=cnb(2107),
    committed_investments=cnb(200),
    restricted_cash=cnb(50),
    overseas_cash=cnb(800),
    revenue=cnb(9963),
    market_cap=22870.0,             # ~118.5 HKD × 193亿股（v3统一稀释股本193亿）
    listed_investments_fv=cnb(800),
    unlisted_investments_bv=cnb(300),
    investment_discount=0.50,
    period="FY2025", ticker="9988.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="FCF口径CapEx从264亿激增至896亿(+240%)[A]。增量632亿主要为AI/云基建+闪购投入。正常化CapEx(基准)~550亿→正常化OE~1140亿RMB。预计FY2027-2028兑现",
)

profile = CompanyProfile(
    name="阿里", ticker="9988.HK", asset_tier="中等质量", period="FY2025",
    revenue_segments=[
        {"name": "淘天集团", "fy2025": 4498, "yoy": "+3%", "share": "45%",
         "trend": "CMR(Q4+12%)靠Take Rate提升非GMV驱动。88VIP破5000万[A]"},
        {"name": "— 淘天CMR", "fy2025": 2457, "yoy": "+6%", "share": "25%",
         "trend": "客户管理收入，核心利润来源"},
        {"name": "AIDC（国际）", "fy2025": 1323, "yoy": "+29%", "share": "13%",
         "trend": "Lazada/AliExpress增长强劲但仍亏损[A]"},
        {"name": "云智能", "fy2025": 1180, "yoy": "+11%", "share": "12%",
         "trend": "FY2026Q3加速至+36%[A]，AI产品连续多季三位数增长"},
        {"name": "本地生活", "fy2025": 671, "yoy": "+10%", "share": "7%",
         "trend": "饿了么+高德。闪购投入FY2026Q3已缩减[B]"},
        {"name": "其他（含剥离）", "fy2025": 2291, "yoy": "下降", "share": "23%",
         "trend": "出售高鑫零售+银泰，聚焦核心[A]"},
    ],
    profitability_metrics=[
        {"name": "收入", "fy2024": "9,393亿", "fy2025": "9,963亿[A]", "change": "+6%"},
        {"name": "经营利润", "fy2024": "1,135亿", "fy2025": "1,409亿[A]", "change": "+24%"},
        {"name": "GAAP净利润", "fy2024": "713亿", "fy2025": "1,259.76亿[A]", "change": "+77%"},
        {"name": "Non-GAAP净利润", "fy2024": "1,581亿", "fy2025": "1,581亿[A]", "change": "持平 ⚠"},
        {"name": "OCF", "fy2024": "1,826亿", "fy2025": "1,635亿[A]", "change": "-10%"},
        {"name": "FCF口径CapEx", "fy2024": "264亿", "fy2025": "896亿[A]", "change": "+240% ⚠⚠"},
        {"name": "FCF", "fy2024": "1,562亿", "fy2025": "738.70亿[A]", "change": "-53% ⚠⚠"},
        {"name": "Non-GAAP PE vs FCF PE", "fy2024": "-", "fy2025": "~10x vs ~26x", "change": "巨大裂缝"},
    ],
    profitability_insight=(
        "核心矛盾：Non-GAAP利润1581亿(PE=10x)看似便宜，但FCF仅738.70亿(PE=26x)[A]——"
        "差额被CapEx从264亿暴增至896亿(+240%)吞噬，增量主要为AI/云基建+闪购投入[A]。"
        "FY2026H1 FCF更是净流出407亿[A]。FY2026Q3回正至+113亿[A]——闪购缩减初见效，但单季不代表趋势。"
        "用Non-GAAP定价是幻觉，FCF才是股东真正能拿到的钱。"
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
        headline='阿里的争议不在于"有没有利润"，而在于"利润能否重新变成高质量自由现金流"——以及被投出去的3800亿能否形成超额回报',
        action="Hold(1手占座) — 当前118.5 HKD接近Optimistic(129)，定价偏贵。Medium-Low Conviction",
        tldr=[
            "v3估值：Conservative 56 / Base 98 / Optimistic 129 HKD。当前118.5接近观察区上沿(距Optimistic仅9%)",
            "核心矛盾：Non-GAAP PE 10x是幻觉，FCF 738.70亿(PE=26x)才是真实定价[A]。FY2026H1 FCF净流出407亿[A]",
            "正常化OE 1140亿需要2-3年兑现(CapEx从峰值896亿回落+闪购止血)——当前是在预付未来盈利能力",
            "按当前价买阿里=赌CapEx周期回归+闪购止血+云AI变现三件事同时发生。conviction不够",
        ],
        body=(
            "FY2025年报(截至2025年3月31日)：收入9963亿(+6%)，经营利润1409亿(+24%)，GAAP净利1,259.76亿(+77%)，"
            "Non-GAAP净利1,581亿(持平)[A]。FCF从1562亿暴跌53%至738.70亿[A]——CapEx从264亿激增至896亿(+240%)[A]，"
            "增量632亿主要来自云基础设施支出和即时零售(闪购)投入[A]。\n\n"
            "正常化估值：四步桥梁表推导正常化OE——正常化OCF 1700亿 - 正常化CapEx 550亿 = "
            "Base OE 1140亿 RMB。但GR1校验：1140亿 = 1.54×FY2025 FCF——超出1.2×上限，标注为需要CapEx回落证据支持。"
            "正常化OE预计FY2027-2028才能兑现。在那之前，实际FCF可能在零附近波动。\n\n"
            "当前118.5 HKD高于Base(98)约21%，距Optimistic(129)仅9%——几乎pricing in了全部上行，安全边际极薄。"
            "FY2026Q3 FCF回正至+113亿[A]是初步改善信号，但单季不代表趋势。当前接近Optimistic上沿，安全边际极薄。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 FCF从1562亿暴跌至739亿——CapEx +240%是核心矛盾",
            body=(
                "FCF口径CapEx从264亿激增至896亿(+240%)[A]。增量632亿主要来自AI/云基础设施+即时零售(闪购)投入[A]。"
                "OCF仍有1635亿(-10%)[A]——经营活动本身还在产出现金，问题在于CapEx吞噬速度远超预期。"
                "FY2026H1 FCF净流出407亿[A]，FY2026Q3回正至+113亿[A]——闪购缩减初见效。"
                "正常化需要CapEx从峰值896亿回落至~550亿(基准假设)——预计最早FY2027。"
            ),
            oe_implication="正常化OE 1140亿 = OCF 1700亿 - CapEx 550亿。当前实际FCF仅739亿。差距401亿的弥合需要2-3年。这段时间是你为未来盈利能力预付的'时间溢价'。",
        ),
        KeyForce(
            title="#2 淘天CMR靠Take Rate而非GMV——可持续性存疑",
            body=(
                "淘天FY2025收入4498亿仅+3%[A]。Q4 CMR+12%依靠Take Rate提升而非GMV增长——"
                "商家在为同样的流量付更多钱，长期可持续性存疑。"
                "抖音电商蚕食高客单价品类，拼多多牢占下沉市场，微信小店+视频号电商崛起——三面夹击。"
                "88VIP破5000万是正面信号但GMV增速仍然低迷。"
            ),
            oe_implication="淘天CMR~2457亿[A]是Layer A核心。基准假设CMR利润率20%→540亿。如果GMV负增长+Take Rate见顶，可能降至17%→459亿(保守)。",
        ),
        KeyForce(
            title="#3 3800亿AI投入——回报路径可见但时间窗口紧",
            body=(
                "阿里云FY2026Q3收入+36%[A]，AI产品连续多季度三位数增长。千问开源模型全球下载3亿+。"
                "3800亿三年AI投入(FY2026~2028)≈年均1267亿CapEx。管理层'不排除追加投入'更增不确定性。"
                "AWS/Azure已验证云AI变现路径——阿里云有机会，但中国云市场价格战也可能压缩利润率。"
            ),
            oe_implication="云收入1180亿[A]+18%增长→~1390亿。基准利润率9%→125亿。乐观13%→181亿。云Layer是OE上行的最大驱动力。",
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
            "电商绝对垄断已弱化为多业务组合。ROIC在AI投入期大幅下降。FCF从1562→739亿(-53%)[A]——赚钱能力在萎缩"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "轻多",
            "阿里云+AI如果成为中国版AWS，收入空间万亿级。千问开源3亿下载+FY2026Q3云+36%[A]是有意义的起点"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "观望",
            "Non-GAAP PE 10x是幻觉，FCF PE 26x不便宜[A]。利润和现金流的巨大裂缝是最大警告。当前118.5已pricing in Optimistic"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "观望",
            "正常化OE 1140亿需2-3年兑现。当前价格=预付未来盈利能力的时间溢价。不够安全"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "轻多",
            "闪购止血(FY2026Q3 FCF回正[A])+云加速(+36%)+资产剥离——催化剂存在但118.5已反映大部分"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "观望",
            "港股beta承压+中美脱钩对AIDC威胁+VIE架构折扣。阿里是港股中地缘风险暴露最大的标的之一"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损20%+，最可能原因是...",
        failure_paths=[
            {"description": "AI资本黑洞：3800亿砸下去但云收入增速回落至<20%，CapEx无法回落至550亿", "probability": "30%"},
            {"description": "淘天份额加速流失：GMV负增长+Take Rate见顶，CMR利润下滑", "probability": "25%"},
            {"description": "正常化不兑现：FY2027 FCF仍<800亿，市场重新定价为价值陷阱", "probability": "20%"},
            {"description": "地缘冲击AIDC：中美脱钩加剧，国际业务受制裁或合规限制", "probability": "15%"},
            {"description": "回购缩减：FCF萎缩→回购力度下降→股本下降的复利效应中断", "probability": "10%"},
        ],
        cognitive_biases=[
            {"bias": "'10x PE好便宜'陷阱", "risk": "Non-GAAP PE 10x是幻觉，FCF视角下真实PE~26x[A]",
             "check": "永远用FCF而非利润定价。FCF是股东真正能拿到的钱"},
            {"bias": "阿里历史光环", "risk": "曾经的王者≠当前的护城河。不要因为历史地位给溢价",
             "check": "和当前的抖音/拼多多/腾讯横向对比，而非和5年前的阿里纵向对比"},
            {"bias": "沉没成本偏差", "risk": "如果已持有阿里，可能不愿承认3800亿AI投入可能回报不足",
             "check": "问自己：如果今天没有持仓，以118.5会买入吗？当前太接近Optimistic(129)，答案大概率是不会"},
        ],
    ),

    header_subtitle="FY2025 Deep Dive · OE Framework",
    capex_warning="⚠ FCF口径CapEx从264亿激增至896亿(+240%)[A]。3年3800亿AI投入(FY2026~2028)。FY2026H1 FCF净流出407亿[A]，Q3回正+113亿[A]——峰值可能已过，但正常化需至FY2027",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", True, "3/4", [
            {"name": "核心收入增速连续2季回升", "triggered": True, "detail": "云+36%(FY2026Q3)[A]，AIDC+29%，淘天CMR+12%"},
            {"name": "OCF margin同比扩张>3pct", "triggered": False, "detail": "OCF -10% YoY[A]，因闪购投入+CapEx侵蚀"},
            {"name": "维持性CapEx占收入比下降", "triggered": False, "detail": "FCF口径CapEx占比从3%升至9%[A]"},
            {"name": "核心竞争力指标改善", "triggered": True, "detail": "88VIP破5000万[A]，云AI收入三位数增长[A]"},
        ]),
        ComboSignal("Combo C · 政策催化型", True, "3/4", [
            {"name": "监管表态明确转向友好", "triggered": True, "detail": "反垄断罚款已落地，监管转向支持"},
            {"name": "行业竞争格局收缩", "triggered": False, "detail": "拼多多+抖音电商仍在抢份额"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "AI云基建直接受益于数字经济政策"},
            {"name": "海外同类公司已先行验证", "triggered": True, "detail": "AWS/Azure验证了云AI变现路径"},
        ]),
        ComboSignal("Combo D2 · 内部人确认型", True, "3/4", [
            {"name": "公司加速回购", "triggered": True, "detail": "FY2025回购119亿美元，流通股净减5.1%[A]"},
            {"name": "管理层增持", "triggered": False, "detail": "蔡崇信/吴泳铭未公开增持"},
            {"name": "特别分红", "triggered": True, "detail": "分红+回购年化收益率~5%"},
            {"name": "资本配置动作与买入逻辑一致", "triggered": True, "detail": "回购+剥离非核心+AI投入，战略聚焦"},
        ]),
        ComboSignal("Combo F · 基本面恶化型", True, "2/4", [
            {"name": "OE连续2季下滑", "triggered": False, "detail": "经营利润+24%[A]，OE口径仍增长"},
            {"name": "FCF转负且非高回报扩张", "triggered": True, "detail": "FCF -53%至739亿[A]。FY2026H1净流出407亿[A]。AI投入ROI 2-3年才能验证"},
            {"name": "CapEx扩张无回报路径", "triggered": False, "detail": "云AI收入三位数增长[A]，有初步验证"},
            {"name": "核心市场份额持续下滑", "triggered": True, "detail": "淘天CMR+6%靠Take Rate而非GMV[A]——质量存疑"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", False, "0/4", [
            {"name": "核心假设被财报否定", "triggered": False, "detail": "云拐点(+36%)[A]+淘天企稳(CMR+12%)——假设尚未被否定"},
            {"name": "竞争对手颠覆性打法", "triggered": False, "detail": "拼多多增速放缓，威胁边际减弱"},
            {"name": "管理层资本配置重大失误", "triggered": False, "detail": "3800亿AI投入有初步回报信号，需持续观察"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "监管已过最坏时期"},
        ]),
        ComboSignal("Combo J · 时间成本型", True, "3/4", [
            {"name": "核心逻辑未证伪但2-3季未兑现", "triggered": True, "detail": "正常化OE需FY2027-2028兑现——2-3年等待期"},
            {"name": "管理层持续讲故事兑现度低", "triggered": False, "detail": "云增速确实在加速(+36%)[A]，不是纯故事"},
            {"name": "资金占用过久替代机会更优", "triggered": True, "detail": "快手(明确加仓区)赔率远优于阿里"},
            {"name": "市场不给估值的关键原因未变", "triggered": True, "detail": "FCF萎缩+AI投入不确定性——市场打折有合理性"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="FCF→OE正常化桥梁",
            subtitle="从FCF现实到OE假设的四步推导",
            metrics=[
                {"metric": "FY2025 OCF[A]", "value": "1,635亿", "judgment": "正面", "note": "经营活动仍在产出现金(-10% YoY)"},
                {"metric": "FY2025 FCF口径CapEx[A]", "value": "896亿(+240%)", "judgment": "负面", "note": "增量632亿为AI/云基建+闪购"},
                {"metric": "FY2025 FCF[A]", "value": "738.70亿", "judgment": "负面", "note": "-53% YoY，腰斩"},
                {"metric": "FY2026H1 FCF[A]", "value": "-407亿", "judgment": "负面", "note": "半年净流出——投入峰值期"},
                {"metric": "FY2026Q3 FCF[A]", "value": "+113亿", "judgment": "正面", "note": "单季回正——闪购缩减初见效"},
                {"metric": "正常化CapEx(基准)", "value": "~550亿", "judgment": "观察", "note": "AI进入维护期+闪购归零后"},
                {"metric": "正常化OCF(基准)", "value": "~1,700亿", "judgment": "观察", "note": "闪购减亏+云收入增长"},
                {"metric": "正常化OE=OCF-CapEx", "value": "~1,140亿", "judgment": "观察", "note": "=1700-550。预计FY2027-2028兑现"},
                {"metric": "GR1校验", "value": "1.54×FCF", "judgment": "负面", "note": "超出1.2×上限——需CapEx回落证据"},
            ],
            insight="正常化OE 1140亿 vs 当前FCF 739亿——差距401亿。弥合需要：(1)CapEx从896→550亿(AI进入维护期)，(2)OCF从1635→1700亿(闪购止血)。预计2-3年。买入=预付时间溢价。",
        ),
        CoreProduct(
            name="分层OE拆解",
            subtitle="Layer A(淘天+云) + Layer B(AIDC+本地) + CapEx消耗",
            metrics=[
                {"metric": "淘天CMR(FY2025)[A]", "value": "~2,457亿", "judgment": "中性", "note": "基准利润率20%→540亿"},
                {"metric": "云智能(FY2025)[A]", "value": "1,180亿", "judgment": "正面", "note": "+18%增长→~1390亿，利润率9%→125亿"},
                {"metric": "Layer A合计", "value": "~665亿", "judgment": "正面", "note": "淘天+云稳定贡献"},
                {"metric": "AIDC(FY2025)[A]", "value": "1,323亿", "judgment": "负面", "note": "+29%但利润率~0%(基准)"},
                {"metric": "本地生活+其他", "value": "671亿[A]", "judgment": "负面", "note": "利润率-1%(基准)→-7亿"},
                {"metric": "Layer B合计", "value": "~-7亿", "judgment": "中性", "note": "基本打平"},
                {"metric": "集团CapEx消耗", "value": "-520亿", "judgment": "负面", "note": "正常化后仍需520亿/年CapEx"},
                {"metric": "合并OE(基准)", "value": "~1,140亿", "judgment": "观察", "note": "665-7-520+OCF调整≈1140"},
            ],
            insight="Layer A(淘天+云)是盈利核心~665亿。Layer B(AIDC+本地)基本打平。CapEx消耗520亿/年——即使正常化后，阿里仍是一家'赚得多但花得也多'的公司。",
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
        focus="FCF→OE正常化桥梁 · 3800亿AI投入ROI · 淘天CMR vs GMV · 正常化时间线FY2027-2028",
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
