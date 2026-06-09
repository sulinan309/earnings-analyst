"""标的画像 + 权重映射

对应文档第七节。最终权重 = 基础状态权重 + 标的画像修正项，
约束：单层 10%-45%，四层合计 100%，每次修正后重新归一化。
"""

from dataclasses import dataclass, field

from .states import State, BASE_WEIGHTS


# ── 画像修正项（文档第七节第 2 小节 A–I）──
# 每项为 {layer: delta}，layer ∈ price/volume/index/flow
PROFILE_ADJUSTMENTS: dict[str, dict[str, float]] = {
    "港股科技":     {"index": +10, "flow": +5, "price": -5, "volume": -10},
    "A股成长":      {"index": +5, "volume": +5, "price": -5, "flow": -5},
    "美股大型科技": {"index": +5, "price": +5, "flow": -5, "volume": -5},
    "周期商品":     {"index": +10, "price": -5, "flow": -5, "volume": 0},
    "红利银行":     {"index": +5, "price": +5, "volume": -5, "flow": -5},
    "小盘高波动":   {"price": +5, "volume": -10, "flow": -5, "index": +10},
    "高流动性大盘": {"price": +5, "volume": +5, "flow": -5, "index": -5},
    "强政策敏感":   {"index": +10, "price": -5, "volume": -5, "flow": 0},
    "强事件驱动":   {"price": +5, "volume": +10, "index": -5, "flow": -10},
}

LAYER_MIN = 10.0
LAYER_MAX = 45.0
LAYERS = ("price", "volume", "index", "flow")


@dataclass
class TargetProfile:
    """标的画像（文档第七节第 1 小节字段的精简版）

    tags 为生效的画像修正标签，须存在于 PROFILE_ADJUSTMENTS。
    policy_pending / event_pending 用于"政策未落地/事件未结束时置信度降级"。
    """

    name: str
    ticker: str
    tags: list[str] = field(default_factory=list)
    asset_tier: str = "中等质量"          # 顶级资产/中等质量/高波动（接入 v1.3 赔率阈值）
    policy_pending: bool = False          # 强政策敏感且政策尚未落地 → 置信度降级
    event_pending: bool = False           # 强事件驱动且事件未结束 → 置信度降级

    def __post_init__(self):
        for t in self.tags:
            if t not in PROFILE_ADJUSTMENTS:
                raise ValueError(f"未知画像标签: {t}，可选: {list(PROFILE_ADJUSTMENTS)}")


def resolve_weights(state: State, tags: list[str]) -> dict[str, float]:
    """计算某状态在给定画像下的四层最终权重（文档第九节 Step 1-4、第七节第 3 小节）

    流程：基础权重 → 叠加画像修正 → 裁剪 10%-45% → 归一化到 100。
    裁剪与归一化迭代收敛，确保最终仍满足 10%-45% 边界（文档"单层不得低于10%"硬约束）。
    """
    weights = dict(BASE_WEIGHTS[state])

    for tag in tags:
        adj = PROFILE_ADJUSTMENTS[tag]
        for layer, delta in adj.items():
            weights[layer] += delta

    # 迭代 clip + normalize，直到边界稳定（单次归一化可能令贴边层越界）
    for _ in range(20):
        for layer in LAYERS:
            weights[layer] = min(max(weights[layer], LAYER_MIN), LAYER_MAX)
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("权重合计非正，无法归一化")
        for layer in LAYERS:
            weights[layer] = weights[layer] / total * 100
        if all(LAYER_MIN - 0.05 <= weights[layer] <= LAYER_MAX + 0.05 for layer in LAYERS):
            break

    return weights
