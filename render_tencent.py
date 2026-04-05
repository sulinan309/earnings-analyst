"""腾讯 FY2025 深度分析 — 从 Claude 分析文档直接渲染 HTML"""

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
    maintenance_capex_note="FCF口径：腾讯FCF=1826亿[A], CapEx=791.98亿[A], 推算OCF≈2618亿[D1]。维持性CapEx≈折旧~500亿上浮至550亿。2026年AI投入360亿+(至少翻倍)[B]",
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
        {"name": "收入", "fy2024": "6601亿", "fy2025": "7518亿", "change": "+14%"},
        {"name": "毛利率", "fy2024": "53.0%", "fy2025": "56.2%", "change": "+3.2pct 创历史新高"},
        {"name": "Non-IFRS经营利润率", "fy2024": "36%", "fy2025": "37.3%", "change": "+1.3pct"},
        {"name": "IFRS经营利润率", "fy2024": "32%", "fy2025": "32%", "change": "持平"},
        {"name": "GAAP净利", "fy2024": "1935亿", "fy2025": "2248亿", "change": "+16%"},
        {"name": "Non-IFRS净利", "fy2024": "2227亿", "fy2025": "2596亿", "change": "+17%"},
        {"name": "基本每股盈利", "fy2024": "21.0元", "fy2025": "24.7元", "change": "+18%(回购增厚)"},
        {"name": "FCF", "fy2024": "1548亿", "fy2025": "1826亿(+18%)", "change": "+18%"},
        {"name": "CapEx", "fy2024": "—", "fy2025": "792亿", "change": "—"},
        {"name": "OCF(推算)", "fy2024": "—", "fy2025": "~2618亿(推算)[D1]", "change": "—"},
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
        headline='腾讯——验证过的复利机器，当前487在观察区。FCF 1826亿(+18%)是五家中最干净的现金流',
        action="观察/等回落 — 当前487 HKD处于观察区(Base 386, Optimistic 794)。Medium-High Conviction",
        tldr=[
            "v4.3估值：Conservative 251 / Base 386 / Optimistic 794 HKD(g=6%)。当前487在观察区偏下",
            "FCF 1826亿(+18%)[A]——五家中唯一FCF同比改善的公司。OE从FCF锚出发，GR1全部通过",
            "Verified compounder资质：3年收入CAGR~14%，毛利率49%→56%，注销式回购使EPS+18%",
            "等430-460回落至可布局区再加仓。维持30股probe buy",
        ],
        body=(
            "2025年报堪称'六边形战士'——全年营收7518亿(+14%)，Non-IFRS归母净利润2596亿(+17%)，"
            "毛利率从53%提升至56%创历史新高，自由现金流1826亿(+18%)，全年回购800亿港元+股息410亿港元。"
            "三大业务板块毛利全部双位数增长。国际游戏774亿首破100亿美元(+33%)。\n\n"
            "v4.3 OE桥梁表(FCF锚→OE)：Conservative OE 1800亿 / Base OE 2000亿 / Optimistic OE 2200亿。"
            "Guard Rail要求OE≤1.2×FCF=2191亿，Non-IFRS净利2596亿远超此限。"
            "基准OE取2000亿(成熟业务1800+AI/视频号效率增量200)，g=3%(基准锚定)，r=11%。"
            "投资组合按极保守口径计入51.3 HKD/share，净现金11.2 HKD/share。\n\n"
            "结论：当前价格处于观察区(Base 386 - Optimistic 794区间)。基本面是Watchlist中最优质的，但估值不够便宜。"
            "维持30股probe buy，等430-460分批加仓更审慎。430以下接近Base值，明确加仓。"
        ),
    ),

    key_forces=[
        KeyForce(
            title="#1 FCF 1826亿(+18%)——五家中最干净的现金流",
            body=(
                "FCF 1826亿(+18%)是Watchlist五家公司中唯一同比改善的。"
                "视频号广告、小游戏分成、AI云服务的毛利率70-80%，远高于基础业务综合~50%。"
                "随着这些新业务占比持续提升，集团毛利率从2023年49%→2024年53%→2025年56%，形成结构性扩张。"
                "这意味着即使收入增速温和(12-14%)，利润增速可以持续在15-20%+。"
            ),
            oe_implication="FCF 1826亿直接锚定OE区间(1800-2200亿)。毛利率每提升1pct≈增加75亿毛利→OE增加150-300亿。",
        ),
        KeyForce(
            title="#2 AI投入2026年360亿+但有节制——不像阿里的CapEx失控",
            body=(
                "2026年AI投入预计至少翻倍至360亿+，但腾讯FCF 1826亿(+18%)远大于CapEx 792亿——"
                "现金流覆盖充裕，不存在阿里式CapEx失控风险。"
                "国际游戏收入774亿(+33%)首破100亿美元，形成不依赖中国宏观的独立增长引擎。"
                "Supercell 2024年收入28亿欧元(+77%)，多款长青游戏焕发第二春。"
            ),
            oe_implication="AI CapEx翻倍至360亿+但FCF仍有1826亿覆盖。国际游戏每增长20%≈155亿增量收入→~77亿增量OE。",
        ),
        KeyForce(
            title="#3 注销式回购——EPS加速器(流通股净减至十年最低90.7亿)",
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

    header_subtitle="FY2025 Deep Dive · v4.3 OE Framework",
    capex_warning="⚠ AI投入2026年至少翻倍至360亿+[B]。但腾讯FCF 1826亿(+18%)远大于CapEx 792亿——现金流覆盖充裕，不存在阿里式CapEx失控风险",

    combo_signals=[
        ComboSignal("Combo B · 基本面拐点型", True, "4/4", [
            {"name": "核心收入增速连续2季回升", "triggered": True, "detail": "游戏+16%, 广告+17%, 金融科技+10%"},
            {"name": "OCF margin同比扩张>3pct", "triggered": True, "detail": "OCF margin 34.8% vs 去年31.2%, +3.6pct"},
            {"name": "维持性CapEx占收入比下降", "triggered": True, "detail": "550/7518=7.3% vs 去年8.5%"},
            {"name": "核心竞争力指标改善", "triggered": True, "detail": "视频号DAU+广告收入双增长，微信生态闭环加强"},
        ]),
        ComboSignal("Combo C · 政策催化型", True, "3/4", [
            {"name": "监管表态明确转向友好", "triggered": True, "detail": "游戏版号常态化恢复，反垄断风暴已过"},
            {"name": "行业竞争格局收缩", "triggered": True, "detail": "中小游戏公司出清，腾讯份额提升"},
            {"name": "公司处于政策直接受益位置", "triggered": True, "detail": "企业微信+政务云直接受益于数字化政策"},
            {"name": "海外同类公司已先行验证", "triggered": False, "detail": "Meta验证了广告AI化，但腾讯游戏路径不同"},
        ]),
        ComboSignal("Combo D2 · 内部人确认型", True, "4/4", [
            {"name": "公司加速回购", "triggered": True, "detail": "2025年回购1120亿港币，史上最大规模"},
            {"name": "管理层增持", "triggered": True, "detail": "Pony Ma持续不减持"},
            {"name": "特别分红", "triggered": True, "detail": "分拆美团股票作特别分派"},
            {"name": "资本配置动作与买入逻辑一致", "triggered": True, "detail": "回购+分红+投资组合优化，三线并进"},
        ]),
        ComboSignal("Combo E · 估值透支型", False, "1/4", [
            {"name": "市值>乐观OE估值+净现金", "triggered": False, "detail": "市值44200亿 vs 乐观58000亿+"},
            {"name": "赔率<20%停止加仓", "triggered": True, "detail": "赔率~42%接近40%阈值(顶级资产)"},
            {"name": "市值/OE>历史均值130%", "triggered": False, "detail": "当前~19x低于历史均值"},
            {"name": "分析师上调空间<10%", "triggered": False, "detail": "一致预期目标价仍有上调空间"},
        ]),
        ComboSignal("Combo H · 逻辑证伪型", False, "0/4", [
            {"name": "核心假设被财报否定", "triggered": False, "detail": "全线增长，假设成立"},
            {"name": "竞争对手颠覆性打法", "triggered": False, "detail": "字节跳动竞争激烈但未颠覆腾讯社交护城河"},
            {"name": "管理层资本配置重大失误", "triggered": False, "detail": "回购时机精准，投资组合优化持续"},
            {"name": "监管风险明确落地", "triggered": False, "detail": "监管周期已过底部"},
        ]),
    ],

    core_products=[
        CoreProduct(
            name="微信生态",
            subtitle="Reality Check — 流量变现效率",
            metrics=[
                {"metric": "微信MAU", "value": "13.8亿", "judgment": "正面", "note": "持平，已是天花板"},
                {"metric": "视频号DAU", "value": "~5亿(估)", "judgment": "正面", "note": "仍在增长，广告加载率有提升空间"},
                {"metric": "小程序GMV", "value": "万亿级", "judgment": "正面", "note": "电商闭环逐步形成"},
                {"metric": "广告增速", "value": "+17%", "judgment": "正面", "note": "AI驱动精准投放"},
                {"metric": "视频号变现率", "value": "远低于抖音", "judgment": "中性", "note": "变现潜力大但执行需时间"},
            ],
            insight="微信是全球最强的超级App，MAU接近天花板但单用户变现仍有巨大空间。视频号是未来3年最大增量。",
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
