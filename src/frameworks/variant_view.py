"""Variant View — 市场共识 vs 我们的判断

参考框架核心："如果结论和市场共识完全一致，分析就没有价值"

输出：市场在想什么 → 我们认为什么 → 他们错在哪里
"""

from dataclasses import dataclass, field


@dataclass
class VariantView:
    """Variant View 分析"""
    company_name: str
    ticker: str

    # 市场共识
    consensus: str                    # 市场主流看法
    consensus_implied_growth: str     # 当前估值隐含的增长率
    consensus_valuation: str          # 卖方一致预期/目标价

    # 我们的判断
    our_view: str                     # 我们的核心论点
    why_market_wrong: str             # 市场错在哪

    # 关键分歧点
    key_debates: list[str] = field(default_factory=list)

    # 催化剂
    catalysts: list[str] = field(default_factory=list)      # 正面催化
    anti_catalysts: list[str] = field(default_factory=list)  # 负面催化

    # Kill condition — 什么情况下我们的论点被证伪
    kill_conditions: list[str] = field(default_factory=list)


# ── 预置数据 ──

def build_tencent_variant() -> VariantView:
    return VariantView(
        company_name="腾讯", ticker="0700.HK",
        consensus=(
            "市场共识：腾讯是中国最优质的互联网资产，AI加持下稳健增长，"
            "但4.2万亿市值已price in大部分增长，估值合理偏贵(~18x Non-IFRS PE)。"
        ),
        consensus_implied_growth="当前市值隐含Non-IFRS利润需年化增长~12-15%才能justify",
        consensus_valuation="卖方一致目标价约550-600港币，隐含~10-15%上涨空间",
        our_view=(
            "OE框架下零增长估值仅27,869亿(含投资组合)，市值42,000亿意味着市场隐含"
            "~12%的长期增长。AI确实在加速腾讯的增长（广告+19%、云+20%），但物业设备"
            "+87%的Capex增速说明AI投入的回报还在前期，OE质量需要观察。"
        ),
        why_market_wrong=(
            "市场可能低估了两件事：1) 投资组合1.04万亿(公允+账面)的隐含价值——按50%折扣"
            "仍有5697亿，占内在价值20%；2) 微信生态的AI渗透率还很低，视频号广告、"
            "搜一搜、企微的货币化空间远未释放。但市场可能高估了短期AI变现速度。"
        ),
        key_debates=[
            "投资组合应该打多少折扣？50%保守还是30%合理？差额~2300亿",
            "AI Capex (+87%) 是高回报投资还是军备竞赛式浪费？",
            "游戏增长(国内+18%,国际+33%)能否持续，还是周期性大年？",
        ],
        catalysts=[
            "元宝/混元大模型出现爆款应用 → 云收入加速",
            "投资组合公允价值回升（如美团/PDD反弹）",
            "继续大规模回购（年化800亿+）",
        ],
        anti_catalysts=[
            "游戏版号政策再次收紧",
            "AI Capex继续暴增但收入增速不匹配",
            "投资组合再次大幅减值",
        ],
        kill_conditions=[
            "连续2季度Non-IFRS利润增速 < 10%，且FCF margin开始下降",
            "管理层大幅缩减回购规模（从积极转向保守）",
            "核心游戏流水出现同比下滑（而非增速放缓）",
        ],
    )


def build_kuaishou_variant() -> VariantView:
    return VariantView(
        company_name="快手", ticker="1024.HK",
        consensus=(
            "市场共识：快手是'小腾讯'故事——广告+电商+AI，但用户增长已见顶，"
            "估值偏低(~12x经调整PE)是因为市场不确定增长质量。"
        ),
        consensus_implied_growth="市值2300亿隐含经调整利润增速~8-10%即可justify",
        consensus_valuation="卖方目标价65-80港币分歧大，市场定价偏谨慎",
        our_view=(
            "OE框架显示内在价值2846亿 vs 市值2300亿，安全边际+23.8%，Combo A已3/4触发。"
            "这是Watchlist中最接近买入区间的标的。可灵AI的商业化(ARR 2.4亿美元)是市场"
            "尚未fully price in的增量——大多数卖方模型中可灵收入占比<5%。"
        ),
        why_market_wrong=(
            "市场过度关注DAU增速放缓(+2.7%)而忽略了两个结构性改善：1) 可灵AI开辟了"
            "toB变现路径（视频生成基础设施），这和广告+电商形成三角结构；2) 海外亏损从"
            "9.34亿收窄至0.76亿，意味着国际化不再是利润黑洞。"
        ),
        key_debates=[
            "可灵AI的TAM有多大？视频生成工具vs通用AI平台，天花板差10倍",
            "DAU 4.1亿是否是天花板？如果是，ARPU提升能否支撑收入增长？",
            "电商GMV+15%还能持续几年？抖音电商的竞争压力？",
        ],
        catalysts=[
            "可灵AI季度收入突破10亿人民币 → 叙事从'短视频公司'变为'AI公司'",
            "海外业务正式盈利",
            "电商take rate提升 → 利润率再上一个台阶",
        ],
        anti_catalysts=[
            "DAU出现环比下滑",
            "可灵AI竞品(Sora等)大幅降价",
            "电商GMV增速跌至个位数",
        ],
        kill_conditions=[
            "经调整净利润连续2季度下滑",
            "可灵AI ARR增速跌至<50%",
            "管理层停止回购或开始减持",
        ],
    )


def build_pdd_variant() -> VariantView:
    return VariantView(
        company_name="拼多多", ticker="PDD",
        consensus=(
            "市场共识：增速断崖(+90%→+10%)后市场重新定价，Temu烧钱节奏不透明，"
            "估值已从溢价变为折价(~9x PE)。"
        ),
        consensus_implied_growth="市值1万亿隐含利润增速~5-8%即可justify",
        consensus_valuation="卖方目标价分歧极大（100-160美元），反映不确定性",
        our_view=(
            "OE框架显示内在价值14,898亿 vs 市值10,000亿，安全边际+49%。"
            "零有息负债+4223亿现金是极强的安全垫。问题不在估值（足够便宜），"
            "而在治理——管理层不透明是最大风险，Combo A仅2/4触发。"
        ),
        why_market_wrong=(
            "市场同时低估了两件矛盾的事：1) PDD的CFO造血能力(1069亿/年)和现金堆积"
            "(4223亿)被增速恐慌掩盖了；2) 但市场可能也低估了Temu的监管尾部风险。"
            "真正被忽略的是，即使Temu完全关停，国内业务的OE仍能justify当前市值。"
        ),
        key_debates=[
            "Temu是战略资产还是价值毁灭器？烧了多少钱完全不透明",
            "4223亿现金会不会永远锁在公司里？管理层治理意愿是最大未知数",
            "美国关税政策对Temu的影响——极端情况下Temu被迫退出美国",
        ],
        catalysts=[
            "宣布分红或大规模回购 → 治理折扣收窄",
            "Temu实现单区域盈利 → 烧钱恐惧缓解",
            "管理层开始给指引 → 信息不透明折扣收窄",
        ],
        anti_catalysts=[
            "美国对中国跨境电商加征关税/禁令",
            "国内反垄断再次聚焦PDD",
            "管理层仍拒绝回馈股东",
        ],
        kill_conditions=[
            "国内电商CFO连续2季度下滑（非Temu烧钱导致）",
            "重大监管处罚落地",
            "管理层出现非计划性减持",
        ],
    )


def build_xiaomi_variant() -> VariantView:
    return VariantView(
        company_name="小米", ticker="1810.HK",
        consensus=(
            "市场共识：汽车业务是最大看点，2026年55万辆目标令人兴奋，"
            "但9000亿市值(~23x经调整PE)已部分price in汽车故事。"
        ),
        consensus_implied_growth="市值隐含利润需年化增长~20%+",
        consensus_valuation="卖方目标价50-65港币分歧大，主要分歧在汽车估值",
        our_view=(
            "OE框架下内在价值仅6804亿 vs 市值9000亿，安全边际-24.4%。"
            "核心问题：汽车Capex(二期工厂+AI)正在吞噬OE。2025年汽车经营利润仅9亿，"
            "但消耗的Capex远超此数。市场在为'汽车年销100万辆'定价，"
            "但从OE视角这个故事需要更多季度的现金流验证。"
        ),
        why_market_wrong=(
            "市场被汽车叙事绑架了。用PE看小米（23x）和用OE看小米（-24.4%）给出"
            "完全相反的结论。分歧在于：如果汽车Capex是高回报扩张性投资，PE才有意义；"
            "如果回报不确定，应该用更保守的OE框架。Q4经营现金流仅6亿是一个警告信号。"
        ),
        key_debates=[
            "汽车Capex是'高回报投资'还是'军备竞赛'？单车利润拐点已到但规模待验证",
            "Q4经营现金流骤降至6亿是季节性还是结构性？",
            "配股425亿港币后ROE被稀释，增长能否消化稀释效应？",
        ],
        catalysts=[
            "2026年Q1汽车交付量超预期 → 55万辆目标可信度提升",
            "全年FCF转正 → 证明汽车投入不拖累现金流",
            "出海欧洲取得实质进展",
        ],
        anti_catalysts=[
            "汽车交付量不及预期/质量问题",
            "全年FCF为负 → '烧钱造车'标签坐实",
            "手机市占率被华为持续夺回",
        ],
        kill_conditions=[
            "汽车业务连续2季度经营亏损（从盈利重回亏损）",
            "全年CFO < 300亿（大幅低于利润）",
            "雷军减持或管理层变动",
        ],
    )


def build_alibaba_variant() -> VariantView:
    return VariantView(
        company_name="阿里", ticker="9988.HK",
        consensus=(
            "市场共识：阿里处于'重投入期'，AI+云和即时零售双线烧钱，"
            "短期利润承压，估值便宜(~10x经调整PE)但缺乏催化剂。"
        ),
        consensus_implied_growth="市值8500亿隐含利润增速~5-8%",
        consensus_valuation="卖方目标价100-140港币，大多数维持'买入'但目标价不断下调",
        our_view=(
            "OE框架显示安全边际-6.5%，几乎处于盈亏平衡。关键矛盾：年化Capex 1264亿"
            "已超过CFO 890亿，阿里正在用存量现金支撑AI投入。如果云业务AI收入"
            "能在2-3年内贡献500亿+增量利润，当前价格是极好的买入点；如果不能，"
            "就是价值陷阱。"
        ),
        why_market_wrong=(
            "市场可能过度悲观了。同口径收入+15%说明核心业务增长健康，"
            "云+26%加速增长是实质性的AI变现（不是PPT）。5602亿现金储备意味着即使"
            "烧3年也不会出现财务危机。但市场也有道理——利润率下降、FCF转负是真实的。"
            "分歧在于：这是'黎明前的黑暗'还是'无底洞的开始'？"
        ),
        key_debates=[
            "3800亿AI投入的回报期——2年？3年？5年？还是永远收不回来？",
            "即时零售(闪购)能否成为第二增长曲线？还是美团不可逾越？",
            "出售高鑫+银泰后，还有哪些资产可以剥离回血？",
        ],
        catalysts=[
            "云业务AI收入单季突破200亿 → AI投入回报可见",
            "FCF重新转正 → 最悲观的情景被排除",
            "管理层回购加速 → Combo D2 信号确认",
        ],
        anti_catalysts=[
            "FCF持续为负超过4个季度",
            "核心电商GMV出现下滑",
            "管理层继续追加投入超出3800亿承诺",
        ],
        kill_conditions=[
            "云业务AI收入增速跌至<15%（投入效率低下）",
            "核心电商OE连续3季度下滑",
            "管理层放弃回购",
        ],
    )


VARIANT_BUILDERS = {
    "0700.HK": build_tencent_variant,
    "1024.HK": build_kuaishou_variant,
    "PDD": build_pdd_variant,
    "1810.HK": build_xiaomi_variant,
    "9988.HK": build_alibaba_variant,
}


def get_variant_view(ticker: str) -> VariantView | None:
    builder = VARIANT_BUILDERS.get(ticker)
    return builder() if builder else None
