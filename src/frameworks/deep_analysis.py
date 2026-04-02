"""深度分析数据模块 — 6 家公司的 Executive Summary / Key Forces / 收入拆分 / 盈利趋势 / 竞争格局 / 6大投资哲学 / Pre-Mortem"""

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
    verdict: str       # "看多"/"看空"/"观望"/"轻多"
    reasoning: str


@dataclass
class PreMortem:
    failure_scenario: str
    failure_paths: list[dict] = field(default_factory=list)
    cognitive_biases: list[dict] = field(default_factory=list)


@dataclass
class DeepAnalysis:
    executive_summary: ExecutiveSummary
    key_forces: list[KeyForce]
    revenue_breakdown: RevenueBreakdown
    profitability: ProfitabilityTrend
    competition: CompetitionTable
    philosophies: list[InvestmentPhilosophy]
    pre_mortem: PreMortem


SIX_PHIL = [
    ("品质复利", "巴菲特/芒格"),
    ("想象力成长", "Baillie Gifford/ARK"),
    ("基本面多空", "Tiger Cubs"),
    ("深度价值", "Klarman/Marks"),
    ("催化剂驱动", "Tepper/Ackman"),
    ("宏观策略", "Druckenmiller"),
]
