"""状态评分与等级分类（文档第三节）

状态分数 = Σ(层得分 × 层权重)，层得分 = checkbox 满足比例 × 100。
"""

from .checkboxes import LayerEvidence


# ── 分数 → 等级（文档第三节第 2 小节）──
def classify_score(score: float) -> str:
    if score < 40:
        return "未触发"
    if score < 60:
        return "观察"
    if score < 75:
        return "弱确认"
    if score < 85:
        return "有效确认"
    return "强确认"


# ── 分数 → 动作档位（文档第三节第 3 小节）──
def score_action_tier(score: float) -> str:
    if score < 60:
        return "不交易/只观察"
    if score < 75:
        return "允许小仓战术动作"
    if score < 85:
        return "允许标准战术动作"
    return "允许更高置信度动作（仍受组合约束）"


def weighted_total(layers: dict[str, LayerEvidence], weights: dict[str, float]) -> float:
    """加权总分 = Σ(层得分 × 层权重) / 100"""
    total = 0.0
    for layer, ev in layers.items():
        total += ev.score * weights[layer]
    return total / 100.0
