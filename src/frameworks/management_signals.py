"""管理层信号与行为分析

对标参考框架 Module D + Module I：
- 管理层指引 vs 实际兑现
- 回购/增持/减持行为
- 资本配置动作一致性
- 业绩会 tone 变化
"""

from dataclasses import dataclass, field


@dataclass
class GuidanceItem:
    """单条指引对比"""
    metric: str            # 指标名
    guidance: str          # 管理层指引
    actual: str            # 实际结果
    hit: bool              # 是否达成
    note: str = ""


@dataclass
class InsiderAction:
    """内部人行为"""
    action_type: str       # "回购" / "增持" / "减持" / "特别分红"
    amount: str            # 金额/数量
    period: str            # 时间段
    signal: str            # "正面" / "负面" / "中性"
    detail: str = ""


@dataclass
class ManagementSignals:
    """管理层信号汇总"""
    company_name: str
    ticker: str
    period: str

    # 指引兑现
    guidance_track: list[GuidanceItem] = field(default_factory=list)
    guidance_credibility: str = ""   # "高" / "中" / "低" + 说明

    # 内部人行为
    insider_actions: list[InsiderAction] = field(default_factory=list)

    # 资本配置
    capital_allocation_summary: str = ""
    capital_allocation_aligned: bool = True  # 行为是否与战略一致

    # 业绩会 tone
    tone_summary: str = ""
    tone_shift: str = ""  # vs 上季度

    # 风险信号
    red_flags: list[str] = field(default_factory=list)


# ── 预置数据 ──

def build_tencent_signals() -> ManagementSignals:
    return ManagementSignals(
        company_name="腾讯", ticker="0700.HK", period="FY2025",
        guidance_track=[
            GuidanceItem("AI投入方向", "加大AI基础设施投入", "物业设备+87%至1499亿",
                         hit=True, note="超额兑现"),
            GuidanceItem("广告业务", "AI驱动广告定向", "广告收入+19%",
                         hit=True, note="视频号+搜一搜持续贡献"),
            GuidanceItem("股东回报", "持续回购", "800亿港币回购",
                         hit=True, note="连续大手笔回购"),
        ],
        guidance_credibility="高 — 过去4个季度指引兑现率接近100%，马化腾风格一贯保守承诺超额兑现",
        insider_actions=[
            InsiderAction("回购", "800亿港币/1.534亿股", "FY2025全年", "正面",
                          "回购金额创历史新高，内部人强烈看好"),
        ],
        capital_allocation_summary=(
            "三大方向：1)AI基础设施(Capex+87%) 2)股东回报(800亿回购) 3)战略投资组合管理。"
            "在增长投入和股东回报之间保持了优秀的平衡。"
        ),
        capital_allocation_aligned=True,
        tone_summary=(
            "马化腾：'核心业务富有韧性并产生充足的现金流，为我们加大AI投入提供支撑。'"
            "定调积极但不激进，强调'AI赋能用户'而非'AI颠覆一切'。"
        ),
        tone_shift="vs FY2024更自信，AI从'探索'变为'落地成效'",
        red_flags=[],
    )


def build_kuaishou_signals() -> ManagementSignals:
    return ManagementSignals(
        company_name="快手", ticker="1024.HK", period="FY2025",
        guidance_track=[
            GuidanceItem("可灵AI商业化", "加速变现", "Q4收入3.4亿，ARR达2.4亿美元",
                         hit=True, note="从概念到收入验证"),
            GuidanceItem("盈利改善", "持续改善", "经调整净利润率14.5%(+0.6pct)",
                         hit=True),
            GuidanceItem("海外扭亏", "缩窄亏损", "海外经营亏损仅0.76亿(去年9.34亿)",
                         hit=True, note="接近盈亏平衡"),
        ],
        guidance_credibility="中高 — 程一笑团队近两年兑现能力显著提升，可灵AI超预期",
        insider_actions=[
            InsiderAction("回购", "31.2亿港币/5678万股", "FY2025全年", "正面",
                          "规模不大但持续回购，信号正面"),
        ],
        capital_allocation_summary="AI投入(可灵+算力中心)+适度回购+控制海外烧钱，资本配置纪律性改善",
        capital_allocation_aligned=True,
        tone_summary="程一笑：'AI能力已成为驱动快手长期增长的核心引擎' — 从谨慎转向自信",
        tone_shift="明显更自信，可灵AI给了管理层底气",
        red_flags=[],
    )


def build_pdd_signals() -> ManagementSignals:
    return ManagementSignals(
        company_name="拼多多", ticker="PDD", period="FY2025",
        guidance_track=[],
        guidance_credibility="极低 — PDD几乎不给前瞻指引，业绩会信息量极少，投资者处于'盲飞'状态",
        insider_actions=[],
        capital_allocation_summary="巨额现金堆积(4223亿)但不分红不回购，资本配置不透明",
        capital_allocation_aligned=False,
        tone_summary="管理层一贯低调，信息披露在大型中概股中最不透明",
        tone_shift="无显著变化，始终保持沉默",
        red_flags=[
            "管理层不给指引，投资者无法追踪兑现度",
            "4223亿现金零回馈股东，资本配置意图不明",
            "公司注册在爱尔兰，VIE架构+低信息披露=治理折扣",
        ],
    )


def build_xiaomi_signals() -> ManagementSignals:
    return ManagementSignals(
        company_name="小米", ticker="1810.HK", period="FY2025",
        guidance_track=[
            GuidanceItem("汽车交付", "2025年目标30万辆", "实际交付超额(收入1061亿推算~25-30万辆)",
                         hit=True, note="从SU7到更多车型"),
            GuidanceItem("汽车盈利", "尽快实现盈利", "年度经营利润首次转正至9亿",
                         hit=True, note="比市场预期提前"),
        ],
        guidance_credibility="高 — 雷军团队汽车业务兑现度极高，从发布到盈利节奏超预期",
        insider_actions=[
            InsiderAction("配股融资", "425亿港币", "2025年3月", "中性",
                          "高位融资稀释股东，但资金用于汽车+AI投入"),
        ],
        capital_allocation_summary=(
            "重注汽车(二期工厂+2026目标55万辆)+AI(未来3年600亿)，"
            "配股融资425亿港币筹集弹药，激进但有执行力背书"
        ),
        capital_allocation_aligned=True,
        tone_summary="雷军持续高调，2026年冲刺55万辆，出海首站欧洲",
        tone_shift="更加激进，从'造车新势力'向'全球化科技公司'叙事升级",
        red_flags=[
            "配股融资425亿港币，高位稀释股东",
            "Q4经营现金流仅6亿，全年现金流质量待验证",
        ],
    )


def build_alibaba_signals() -> ManagementSignals:
    return ManagementSignals(
        company_name="阿里", ticker="9988.HK", period="FY2026E",
        guidance_track=[
            GuidanceItem("AI+云投入", "3年投3800亿", "前4季度已投1200亿(占31.6%)",
                         hit=True, note="节奏符合预期"),
            GuidanceItem("资产剥离", "出售非核心资产", "已出售高鑫零售+银泰",
                         hit=True, note="聚焦核心电商+云"),
        ],
        guidance_credibility="中 — 吴泳铭战略方向清晰，但利润端兑现持续低于预期",
        insider_actions=[],
        capital_allocation_summary=(
            "双重烧钱：AI+云Capex年化1264亿 + 即时零售(闪购)持续投入。"
            "FCF已转负，用存量现金支撑。出售非核心资产回血。"
        ),
        capital_allocation_aligned=True,
        tone_summary="吴泳铭：'构建AI技术基础设施与大消费平台的关键投入期，短期利润承压'",
        tone_shift="从'降本增效'180度转向'全面重投入'，市场仍在消化",
        red_flags=[
            "FCF前三季度累计净流出293亿，阿里历史首次",
            "Capex年化1264亿 > CFO年化890亿，入不敷出",
            "利润率持续恶化，看不到投入回报的时间表",
        ],
    )


SIGNAL_BUILDERS = {
    "0700.HK": build_tencent_signals,
    "1024.HK": build_kuaishou_signals,
    "PDD": build_pdd_signals,
    "1810.HK": build_xiaomi_signals,
    "9988.HK": build_alibaba_signals,
}


def get_management_signals(ticker: str) -> ManagementSignals | None:
    builder = SIGNAL_BUILDERS.get(ticker)
    return builder() if builder else None
