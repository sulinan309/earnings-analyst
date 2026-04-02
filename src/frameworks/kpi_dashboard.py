"""核心 KPI 仪表盘

每家公司 2-5 个最能反映业务健康度的「体温计」指标。
按公司类型自动匹配 KPI 模板，支持同比/环比追踪。
"""

from dataclasses import dataclass, field


@dataclass
class KPIItem:
    """单个 KPI"""
    name: str                     # 指标名
    current: float | str          # 当前值
    prior: float | str | None = None   # 上期值（环比）
    yoy: float | str | None = None     # 同比值
    unit: str = ""                # 单位（%、亿、万等）
    trend: str = ""               # "↑" / "↓" / "→"
    is_positive: bool = True      # 趋势是否正面
    note: str = ""                # 补充说明


@dataclass
class KPIDashboard:
    """KPI 仪表盘"""
    company_name: str
    ticker: str
    period: str
    business_type: str            # "社交平台" / "电商" / "综合互联网" 等
    kpis: list[KPIItem] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)  # 1-3 句核心发现
    concerns: list[str] = field(default_factory=list)    # 1-3 句核心隐忧


# ── 预置的 Watchlist 公司 KPI 数据 ──

def build_tencent_kpis() -> KPIDashboard:
    return KPIDashboard(
        company_name="腾讯", ticker="0700.HK", period="FY2025",
        business_type="综合互联网",
        kpis=[
            KPIItem("总收入增速", 14, 7, unit="%", trend="↑", is_positive=True,
                    note="从FY2024的+7%加速至+14%"),
            KPIItem("Non-IFRS经营利润率", 37, 36, unit="%", trend="↑", is_positive=True,
                    note="连续改善，规模效应显现"),
            KPIItem("游戏收入增速(国内)", 18, None, unit="%", trend="↑", is_positive=True,
                    note="三角洲行动+长青游戏驱动"),
            KPIItem("游戏收入增速(国际)", 33, None, unit="%", trend="↑", is_positive=True,
                    note="Supercell+PUBG Mobile+鸣潮"),
            KPIItem("广告收入增速", 19, None, unit="%", trend="↑", is_positive=True,
                    note="AI驱动广告定向+视频号商业化"),
            KPIItem("云收入增速", "~20", None, unit="%", trend="↑", is_positive=True,
                    note="企业服务含AI相关需求"),
            KPIItem("FCF", 1826, 1548, unit="亿", trend="↑", is_positive=True,
                    note="同比+18%，现金造血强劲"),
            KPIItem("年度回购", 800, None, unit="亿港币", trend="↑", is_positive=True,
                    note="1.534亿股，内部人确认信号"),
            KPIItem("Capex/收入比", 10.5, 11.7, unit="%", trend="↓", is_positive=True,
                    note="物业设备猛增87%但收入增长消化"),
        ],
        highlights=[
            "收入增速从7%加速至14%，全线业务回暖，AI成为横向加速器",
            "FCF 1826亿+800亿港币回购，资本回报意愿强烈（Combo D2 信号）",
            "Non-IFRS利润率37%创新高，规模效应+AI提效双轮驱动",
        ],
        concerns=[
            "物业设备从801亿猛增至1499亿(+87%)，AI Capex拐点尚未到来",
            "投资组合公允价值从Q3的8008亿降至年末6727亿(-16%)，市场波动影响",
            "Capex/收入比虽下降但绝对额仍大，维持性vs扩张性拆分不透明",
        ],
    )


def build_kuaishou_kpis() -> KPIDashboard:
    return KPIDashboard(
        company_name="快手", ticker="1024.HK", period="FY2025",
        business_type="短视频/直播/电商",
        kpis=[
            KPIItem("DAU", 4.10, 3.99, unit="亿", trend="↑", is_positive=True,
                    note="同比+2.7%，增长放缓但仍为正"),
            KPIItem("电商GMV", 15981, 13896, unit="亿", trend="↑", is_positive=True,
                    note="同比+15%，电商仍为核心增长引擎"),
            KPIItem("总收入增速", 12.5, None, unit="%", trend="↑", is_positive=True),
            KPIItem("经调整净利润率", 14.5, 13.9, unit="%", trend="↑", is_positive=True,
                    note="盈利能力持续改善"),
            KPIItem("经调整净利润", 206, 177, unit="亿", trend="↑", is_positive=True,
                    note="同比+16.5%"),
            KPIItem("可灵AI ARR", 2.4, None, unit="亿美元", trend="↑", is_positive=True,
                    note="12月单月突破2000万美元，商业化加速"),
            KPIItem("海外经营亏损", -0.76, -9.34, unit="亿", trend="↑", is_positive=True,
                    note="海外亏损大幅收窄，接近盈亏平衡"),
            KPIItem("国内经营利润", 212, 164, unit="亿", trend="↑", is_positive=True,
                    note="同比+29%"),
        ],
        highlights=[
            "可灵AI从0到ARR 2.4亿美元，验证了视频生成模型的商业化路径",
            "国内经营利润212亿(+29%)，海外亏损接近归零，利润质量大幅改善",
            "AIGC营销素材Q4消耗40亿元，AI对核心广告业务的提效已兑现收入",
        ],
        concerns=[
            "DAU增速仅2.7%，用户天花板隐现，后续增长依赖ARPU提升",
            "物业设备从148亿增至229亿(+54%)，AI算力投入加速",
            "直播收入仅+5.5%，传统打赏模式增长乏力",
        ],
    )


def build_pdd_kpis() -> KPIDashboard:
    return KPIDashboard(
        company_name="拼多多", ticker="PDD", period="FY2025",
        business_type="电商平台",
        kpis=[
            KPIItem("总收入增速", 10, 90, unit="%", trend="↓", is_positive=False,
                    note="从FY2024的+90%骤降至+10%，增速悬崖"),
            KPIItem("经营利润率", 22, 25, unit="%", trend="↓", is_positive=False,
                    note="Temu投入侵蚀利润率"),
            KPIItem("CFO", 1069, 1219, unit="亿", trend="↓", is_positive=False,
                    note="同比-12%，但绝对额仍强"),
            KPIItem("现金储备", 4223, 3316, unit="亿", trend="↑", is_positive=True,
                    note="现金+短期投资4223亿，零负债"),
            KPIItem("营销费用增速", "~15", None, unit="%", trend="↑", is_positive=False,
                    note="Temu持续烧钱获客"),
        ],
        highlights=[
            "零有息负债+4223亿现金储备，资产负债表极度健康",
            "即使增速大幅放缓，CFO仍有1069亿，造血能力一流",
            "轻资产模式Capex极低，几乎全部CFO转化为FCF",
        ],
        concerns=[
            "收入增速从90%断崖至10%，市场对增长故事的信仰正在动摇",
            "Temu海外监管风险（关税、合规），且商业模式可持续性待验证",
            "管理层极度低调不透明，信息披露质量在大型中概股中最低",
        ],
    )


def build_xiaomi_kpis() -> KPIDashboard:
    return KPIDashboard(
        company_name="小米", ticker="1810.HK", period="FY2025",
        business_type="硬件+互联网+汽车",
        kpis=[
            KPIItem("总收入增速", 25, None, unit="%", trend="↑", is_positive=True,
                    note="4573亿创历史新高"),
            KPIItem("经调整净利润", 392, 272, unit="亿", trend="↑", is_positive=True,
                    note="同比+43.8%"),
            KPIItem("汽车收入", 1061, None, unit="亿", trend="↑", is_positive=True,
                    note="首破千亿，同比+224%，首次年度盈利"),
            KPIItem("汽车经营利润", 9, None, unit="亿", trend="↑", is_positive=True,
                    note="首次转正，单车盈利拐点"),
            KPIItem("IoT收入增速", 18.3, None, unit="%", trend="↑", is_positive=True),
            KPIItem("互联网服务收入", 374, 341, unit="亿", trend="↑", is_positive=True,
                    note="高毛利业务+9.7%"),
            KPIItem("现金储备", 2326, 1751, unit="亿", trend="↑", is_positive=True,
                    note="含配股融资425亿港币"),
            KPIItem("研发投入", 331, 241, unit="亿", trend="↑", is_positive=True,
                    note="同比+37.8%，未来3年AI投入600亿"),
        ],
        highlights=[
            "汽车业务年收入破千亿且首次盈利，从0到1的故事已完成0到0.5",
            "全业务线增长，4573亿收入+43.8%利润增长，执行力极强",
            "雷军个人品牌+生态协同仍是独特的不可复制护城河",
        ],
        concerns=[
            "Q4经营现金流仅6亿，全年现金流可能远低于利润（需验证）",
            "汽车Capex二期工厂+AI投入600亿/3年，对OE的侵蚀才刚开始",
            "手机业务收入增速放缓，IoT+手机的传统业务可能已近天花板",
        ],
    )


def build_alibaba_kpis() -> KPIDashboard:
    return KPIDashboard(
        company_name="阿里", ticker="9988.HK", period="FY2026E(前三季度年化)",
        business_type="电商+云+本地生活",
        kpis=[
            KPIItem("收入增速(同口径)", "9-15", None, unit="%", trend="↑", is_positive=True,
                    note="剔除出售高鑫/银泰后同口径+15%"),
            KPIItem("云收入增速", 26, None, unit="%", trend="↑", is_positive=True,
                    note="AI需求驱动加速"),
            KPIItem("AI+云Capex(近4季)", 1200, None, unit="亿", trend="↑", is_positive=False,
                    note="3年计划3800亿的1/3已投出"),
            KPIItem("FCF(前三季度)", -293, None, unit="亿", trend="↓", is_positive=False,
                    note="累计净流出，AI投入吞噬现金流"),
            KPIItem("现金储备", 5602, None, unit="亿", trend="→", is_positive=True,
                    note="仍有充足弹药"),
            KPIItem("经调整EBITA利润率", "~下降", None, unit="", trend="↓", is_positive=False,
                    note="即时零售+AI投入双重压力"),
        ],
        highlights=[
            "云业务+26%加速增长，AI需求成为真正的收入驱动力而非概念",
            "同口径收入+15%，剥离低效资产后核心业务增速健康",
            "5602亿现金储备，即使FCF为负也有充足弹药支撑3800亿AI投入",
        ],
        concerns=[
            "前三季度FCF累计净流出293亿，这是阿里历史上罕见的",
            "Capex年化1264亿vs CFO年化890亿，资本支出已超过造血能力",
            "即时零售(闪购)烧钱+AI Capex双重压力，利润率短期看不到底",
        ],
    )


KPI_BUILDERS = {
    "0700.HK": build_tencent_kpis,
    "1024.HK": build_kuaishou_kpis,
    "PDD": build_pdd_kpis,
    "1810.HK": build_xiaomi_kpis,
    "9988.HK": build_alibaba_kpis,
}


def get_kpi_dashboard(ticker: str) -> KPIDashboard | None:
    builder = KPI_BUILDERS.get(ticker)
    return builder() if builder else None
