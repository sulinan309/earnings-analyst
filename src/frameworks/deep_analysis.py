"""深度分析数据模块 — Executive Summary / Key Forces / 收入拆分 / 盈利趋势 / 竞争格局 /
8-Combo信号 / 核心产品分析 / 6大投资哲学 / Pre-Mortem"""

from dataclasses import dataclass, field


@dataclass
class ExecutiveSummary:
    headline: str
    action: str
    tldr: list[str]
    body: str


@dataclass
class KeyForce:
    title: str
    body: str
    oe_implication: str


@dataclass
class RevenueBreakdown:
    segments: list[dict] = field(default_factory=list)
    # segments dict keys: name, fy2025, yoy, share, trend
    # optional quarterly keys: q1, q2, q3, q4
    warning: str = ""  # 黄色警告框内容


@dataclass
class ProfitabilityTrend:
    metrics: list[dict] = field(default_factory=list)
    insight: str = ""


@dataclass
class CompetitionTable:
    dimensions: list[dict] = field(default_factory=list)
    moat_assessment: str = ""


@dataclass
class InvestmentPhilosophy:
    name: str
    representative: str
    verdict: str       # "看多"/"看空"/"观望"/"轻多"/"持有/买入"
    reasoning: str


@dataclass
class PreMortem:
    failure_scenario: str
    failure_paths: list[dict] = field(default_factory=list)
    cognitive_biases: list[dict] = field(default_factory=list)


@dataclass
class ComboSignal:
    """单个Combo信号（B-J）"""
    name: str           # e.g. "Combo B · 基本面拐点型"
    triggered: bool
    count: str          # e.g. "3/4"
    sub_conditions: list[dict] = field(default_factory=list)
    # sub_conditions dict keys: name, triggered (bool), detail (str)


@dataclass
class CoreProduct:
    """核心产品/业务深度分析"""
    name: str           # e.g. "可灵AI"
    subtitle: str       # e.g. "Reality Check"
    metrics: list[dict] = field(default_factory=list)
    # metrics dict keys: metric, value, judgment (str), note (str)
    insight: str = ""


@dataclass
class DeepAnalysis:
    executive_summary: ExecutiveSummary
    key_forces: list[KeyForce]
    revenue_breakdown: RevenueBreakdown
    profitability: ProfitabilityTrend
    competition: CompetitionTable
    philosophies: list[InvestmentPhilosophy]
    pre_mortem: PreMortem
    # 新增字段（可选）
    combo_signals: list[ComboSignal] = field(default_factory=list)
    core_products: list[CoreProduct] = field(default_factory=list)
    capex_warning: str = ""  # CapEx冲击模拟的警告文字
    header_subtitle: str = ""  # 简短副标题 e.g. "FY2025 Deep Dive"


SIX_PHIL = [
    ("品质复利", "巴菲特/芒格"),
    ("想象力成长", "Baillie Gifford/ARK"),
    ("基本面多空", "Tiger Cubs"),
    ("深度价值", "Klarman/Marks"),
    ("催化剂驱动", "Tepper/Ackman"),
    ("宏观策略", "Druckenmiller"),
]
