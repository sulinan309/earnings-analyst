"""腾讯 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.frameworks.auto_analysis import CompanyProfile, run_full_analysis
from src.frameworks.deep_analysis import (
    DeepAnalysis, ExecutiveSummary, KeyForce, RevenueBreakdown,
    ProfitabilityTrend, CompetitionTable, InvestmentPhilosophy, PreMortem,
)
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput
from src.output.html_report import generate_html

FX = 1.1
def cnb(v): return round(v * FX, 2)
def cnm(v): return round(v * FX / 100, 2)

# ═══════════════════════════════════════════
#  财务数据（tencent.pdf 完整提取）
# ═══════════════════════════════════════════

financial_data = FinancialData(
    cfo=cnb(2618),                  # FCF 1826 + Capex 792
    maintenance_capex=cnb(550),     # 折旧摊销~500亿上浮
    total_capex=cnb(792),
    cash_and_equivalents=cnm(141_041),
    short_term_investments=cnm(236_801 + 70_302),
    interest_bearing_debt=cnm(42_618 + 10_542 + 208_369 + 126_204),
    committed_investments=100.0,
    restricted_cash=cnm(6_977),
    overseas_cash=200.0,
    revenue=cnb(7518),
    market_cap=44200.0,             # ~487 HKD × 90.7亿股
    listed_investments_fv=cnb(7143),
    unlisted_investments_bv=cnb(3423),
    investment_discount=0.30,       # 上市75%+非上市55% ≈ 综合30%折扣
    period="FY2025", ticker="0700.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note="附注未拆分，以折旧摊销~500亿上浮至550亿作为保守估计。2026年AI投入预计翻倍至360亿+",
)

profile = CompanyProfile(
    name="腾讯", ticker="0700.HK", asset_tier="顶级资产", period="FY2025",
    revenue_segments=[
        {"name": "增值服务(游戏+社交)", "fy2025": cnb(3693), "yoy": "+16%", "share": "49%",
         "trend": "国内游戏+18%(三角洲行动),国际+33%(Supercell),社交+5%"},
        {"name": "— 本土游戏", "fy2025": cnb(1642), "yoy": "+18%", "share": "22%",
         "trend": "王者荣耀+和平精英长青，三角洲行动爆款"},
        {"name": "— 国际游戏", "fy2025": cnb(774), "yoy": "+33%", "share": "10%",
         "trend": "首破100亿美元，Supercell+PUBG Mobile+鸣潮"},
        {"name": "— 社交网络", "fy2025": cnb(1277), "yoy": "+5%", "share": "17%",
         "trend": "视频号直播+音乐付费会员"},
        {"name": "营销服务(广告)", "fy2025": cnb(1450), "yoy": "+19%", "share": "19%",
         "trend": "AI驱动广告定向+视频号商业化+闭环广告占比提升"},
        {"name": "金融科技及企业服务", "fy2025": cnb(2294), "yoy": "+8%", "share": "31%",
         "trend": "云+~20%(AI需求)+规模化盈利,支付高个位数"},
    ],
    profitability_metrics=[
        {"name": "毛利率", "fy2024": "53.0%", "fy2025": "56.2%", "change": "+3.2pct 创历史新高"},
        {"name": "Non-IFRS经营利润率", "fy2024": "36%", "fy2025": "37.3%", "change": "+1.3pct"},
        {"name": "IFRS经营利润率", "fy2024": "32%", "fy2025": "32%", "change": "持平"},
        {"name": "Non-IFRS归母净利润", "fy2024": str(cnb(2227)), "fy2025": str(cnb(2596)), "change": "+17%"},
        {"name": "GAAP归母净利润", "fy2024": str(cnb(1935)), "fy2025": str(cnb(2248)), "change": "+16%"},
        {"name": "基本每股盈利", "fy2024": "21.0元", "fy2025": "24.7元", "change": "+18%(回购增厚)"},
        {"name": "FCF", "fy2024": str(cnb(1548)), "fy2025": str(cnb(1826)), "change": "+18%"},
    ],
    profitability_insight=(
        "毛利率+3.2pct至56%创历史新高——核心驱动力是高毛利新业务(视频号广告70-80%、小游戏分成、AI云)占比持续提升。"
        "这是结构性扩张而非一次性改善。利润增速(+17%)持续快于收入增速(+14%)——运营杠杆+高毛利迁移双轮驱动。"
        "EPS增速(+18%)又快于利润增速——注销式回购压降股本至90.7亿股(十年最低)。"
        "这形成了'收入+14%→利润+17%→EPS+18%'的递进增长范式。"
    ),
    competition_dims=[
        {"metric": "总收入(亿港币)", "company_value": str(cnb(7518)), "comp1_name": "阿里", "comp1_value": "~10,960", "comp2_name": "字节(参考)", "comp2_value": "~13,000+"},
        {"metric": "毛利率", "company_value": "56%", "comp1_name": "Meta", "comp1_value": "~80%", "comp2_name": "阿里", "comp2_value": "~40%"},
        {"metric": "游戏收入(亿港币)", "company_value": str(cnb(2416)), "comp1_name": "网易", "comp1_value": "~990", "comp2_name": "米哈游", "comp2_value": "~330+"},
        {"metric": "广告收入(亿港币)", "company_value": str(cnb(1450)), "comp1_name": "字节", "comp1_value": "~6,600+", "comp2_name": "快手", "comp2_value": str(cnb(815))},
        {"metric": "FCF(亿港币)", "company_value": str(cnb(1826)), "comp1_name": "阿里", "comp1_value": "FCF为负", "comp2_name": "PDD", "comp2_value": str(cnb(1069))},
        {"metric": "Trailing PE", "company_value": "~17x", "comp1_name": "Meta", "comp1_value": "~23x", "comp2_name": "阿里", "comp2_value": "~10x"},
    ],
    moat_assessment=(
        "微信生态是中国互联网最深的护城河之一——14.18亿MAU+支付+小程序+视频号+企微形成超级闭环。"
        "游戏IP储备(王者/和平)和全球化投资组合(Supercell/Riot/Epic)是第二护城河。"
        "国际游戏收入首破100亿美元(+33%)形成不依赖中国宏观的独立增长引擎。"
        "56%毛利率在全球大型科技公司中处于较高位置(Meta~80%、Google~58%、阿里~40%)。"
    ),
    capex_cfo_growth=0.10,
    capex_growth_base=0.20,     # AI投入翻倍
    capex_growth_bear=0.50,
)

# ═══════════════════════════════════════════
#  DeepAnalysis（从 Claude 分析文档映射）
# ═══════════════════════════════════════════

deep_analysis = DeepAnalysis(
    executive_summary=ExecutiveSummary(
        headline='腾讯是中国互联网最接近"永续复利机器"的标的——14亿微信用户×AI变现提速×注销式回购=EPS增速>利润增速>收入增速的增长范式',
        action="买入（优先建仓标的） — 当前~487 HKD低于Action Price(~520 HKD)约6%，High Conviction",
        tldr=[
            "OE ~2400亿(28.8 HKD/股)，内在价值~690 HKD vs 当前~487 HKD，折价~30%，IRR ~19%/年 ✅超15%铁律",
            "毛利率56%创历史新高——高毛利新业务(视频号广告70-80%、AI云)占比持续提升，结构性扩张非一次性",
            "国际游戏收入774亿首破100亿美元(+33%)——不依赖中国宏观的第二增长引擎",
            "注销式回购800亿港元+股息410亿=股东回报率2.7%，总股本降至90.7亿(十年最低)",
        ],
        body=(
            "2025年报堪称'六边形战士'——全年营收7518亿(+14%)，Non-IFRS归母净利润2596亿(+17%)，"
            "毛利率从53%提升至56%创历史新高，自由现金流1826亿(+18%)，全年回购800亿港元+股息410亿港元。"
            "三大业务板块毛利全部双位数增长：增值服务毛利+22%、营销服务毛利+24%、金融科技及企业服务毛利+17%。\n\n"
            "核心亮点：(1)高毛利新业务(自研游戏、视频号广告、AI云服务)占比持续提升，驱动毛利率结构性扩张；"
            "(2)国际游戏收入774亿首破100亿美元(+33%)，成为第二增长引擎；"
            "(3)腾讯云首次实现规模化盈利，企业服务收入+20%；"
            "(4)注销式回购持续压降总股本至~90.7亿股(十年最低)，使EPS增速(+18%)持续快于利润增速(+17%)。\n\n"
            "K0估值：OE 2400亿(GAAP与Non-IFRS中间值) × (1+g) / (r-g) + 净现金 + 投资组合 = 内在价值~690 HKD。"
            "扣除25%安全边际后Action Price ~520 HKD。当前487 HKD低于Action Price约6%——处于Buy zone边缘。"
            "这是Watchlist中conviction最高的标的。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 高毛利收入结构性迁移——56%毛利率不是天花板",
            body=(
                "视频号广告、小游戏分成、AI云服务的毛利率70-80%，远高于基础业务综合~50%。"
                "随着这些新业务占比持续提升，集团毛利率从2023年49%→2024年53%→2025年56%，形成结构性扩张。"
                "这意味着即使收入增速温和(12-14%)，利润增速可以持续在15-20%+。"
            ),
            oe_implication="毛利率每提升1pct≈增加75亿毛利。如果毛利率从56%继续升至58-60%，OE可增加150-300亿。",
        ),
        KeyForce(
            title="#2 国际游戏的'第二飞轮'——首破100亿美元",
            body=(
                "国际游戏收入774亿(+33%)。Supercell 2024年收入28亿欧元(+77%)，多款长青游戏焕发第二春。"
                "目标国际游戏占游戏总收入50%(当前约32%)。这是一个不依赖中国宏观的独立增长引擎——"
                "即使国内监管收紧或消费疲软，国际游戏仍可贡献增量。"
            ),
            oe_implication="国际游戏收入每增长20%≈155亿增量收入。以~50%边际利润率计≈77亿增量OE。",
        ),
        KeyForce(
            title="#3 注销式回购——EPS复合增长加速器",
            body=(
                "2024年回购1120亿港元注销3.07亿股，2025年回购800亿港元注销1.53亿股。"
                "总股本从2021年的~96亿股降至~90.7亿股(十年最低)。在利润+17%的基础上EPS增长+18%。"
                "管理层已将'注销式回购+分红'确立为持续的资本配置范式——不是一次性行为。"
            ),
            oe_implication="每年减少1.5-2%股本意味着OE per share的增速永久性地快于总OE增速2个百分点。10年复利效应显著。",
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
        InvestmentPhilosophy("品质复利", "巴菲特/芒格", "强烈看多",
            "微信是中国最深的社交护城河之一，ROIC持续提升，20年后大概率更强。56%毛利率+年1826亿FCF+注销式回购=教科书级复利机器"),
        InvestmentPhilosophy("想象力成长", "Baillie Gifford/ARK", "看多",
            "AI+视频号+国际游戏的optionality巨大。国际游戏已证明第二曲线(+33%)，AI云刚进入正循环"),
        InvestmentPhilosophy("基本面多空", "Tiger Cubs", "看多",
            "17x PE for 18% EPS growth = PEG<1，在全球大型科技股中属于相对低估。市场对中国资产施加了过多的地缘折价"),
        InvestmentPhilosophy("深度价值", "Klarman/Marks", "看多",
            "万亿投资组合+1071亿净现金+年1826亿FCF。私有化买家会出比487 HKD更高的价格——仅FCF yield就有4%"),
        InvestmentPhilosophy("催化剂驱动", "Tepper/Ackman", "看多",
            "混元3.0发布(4月)+新游pipeline(三角洲行动海外版)+视频号电商加速——2026H1催化剂密集"),
        InvestmentPhilosophy("宏观策略", "Druckenmiller", "持有",
            "港股beta承压(美伊冲突+Fed鹰派)，但腾讯alpha足够强——高股东回报率2.7%提供下行保护"),
    ],

    pre_mortem=PreMortem(
        failure_scenario="假设18个月后亏损15%+，最可能原因是...",
        failure_paths=[
            {"description": "监管2.0：版号政策收紧+数据隐私新规+反垄断再聚焦腾讯，估值压缩至12x PE", "probability": "25%"},
            {"description": "中美脱钩加剧：国际游戏业务受制裁影响，Supercell等海外资产被要求剥离", "probability": "15%"},
            {"description": "AI投入黑洞：AI Capex翻倍至360亿+但云收入增速未加速，利润率被侵蚀", "probability": "20%"},
            {"description": "广告市场萎缩：宏观衰退导致广告预算大幅削减，营销服务收入增速转负", "probability": "15%"},
            {"description": "港股系统性去估值：地缘+利率导致港股整体PE下移20%+，腾讯被拖累", "probability": "25%"},
        ],
        cognitive_biases=[
            {"bias": "权威偏差", "risk": "'腾讯是中国最好的公司'这个共识可能让你忽视真实风险",
             "check": "列出3个腾讯可能不如预期的具体情景"},
            {"bias": "锚定效应", "risk": "K0内在价值690 HKD是模型输出，对g极度敏感(g每变1pct估值变15-25%)",
             "check": "用K4敏感性矩阵检查——g=6%时内在价值仅~571 HKD"},
            {"bias": "确认偏差", "risk": "已持有30股probe buy，倾向于寻找加仓理由",
             "check": "Bear case 20%概率下目标价359 HKD(-26%)——这个损失你能承受吗？"},
        ],
    ),
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
        asset_tier="顶级资产",
        quarterly_oes=[round(oe.oe / 4, 1)] * 4,
        oe_multiple_percentile=35.0,
        structural_deterioration=False,
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, "顶级资产")

    inp = ReportInput(
        company_name="腾讯", ticker="0700.HK", asset_tier="顶级资产",
        focus="高毛利业务迁移、国际游戏第二曲线、注销式回购复利",
        financial_data=financial_data, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )

    html = generate_html(inp, deep=result)
    out_path = "docs/0700_HK.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ {out_path} ({len(html)//1024}KB)")
    print(f"  数据源: {result.data_source}")
    print(f"  OE: {oe.oe:.0f}亿 | 安全边际: {oe.safety_margin_pct:+.1f}%")
    print(f"  Combo A: {combo_a.triggered_count}/4 | 决策: {mx.action}")
