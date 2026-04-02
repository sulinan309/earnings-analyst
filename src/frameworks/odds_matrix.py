"""赔率/胜率决策矩阵

CLAUDE.md 规则：
- 高胜率 + 高赔率 → 重仓
- 高胜率 + 中赔率 → 标准仓位
- 中胜率 + 高赔率 → 轻仓
- 其余 → 不参与
- 赔率分层：顶级资产>40%、中等质量>70%、高波动>100%

胜率由 Combo 触发数量和质量决定：
- Combo A 4/4 触发 → 胜率 5
- Combo A 3/4 + 其他核心 Combo 触发 → 胜率 4
- Combo A 3/4 → 胜率 3
- Combo A 2/4 → 胜率 2
- Combo A <2/4 → 胜率 1

赔率由安全边际 vs 资产层级阈值决定：
- 赔率 ≥ 阈值×1.5 → 赔率评分 5
- 赔率 ≥ 阈值 → 赔率评分 4
- 赔率 ≥ 阈值×0.5 → 赔率评分 3
- 赔率 > 0 → 赔率评分 2
- 赔率 ≤ 0 → 赔率评分 1
"""

from dataclasses import dataclass

from src.signals.combo_scanner import ComboScanResult


ODDS_THRESHOLDS = {
    "顶级资产": 0.40,
    "中等质量": 0.70,
    "高波动": 1.00,
}

# ── 决策矩阵：(胜率等级, 赔率等级) → 操作 ──
# 胜率: "高"=4-5, "中"=3, "低"=1-2
# 赔率: "高"=4-5, "中"=3, "低"=1-2
ACTION_MATRIX = {
    ("高", "高"): ("重仓", "高胜率+高赔率，核心底仓"),
    ("高", "中"): ("标准仓位", "高胜率+中赔率，可建仓但控制规模"),
    ("高", "低"): ("不参与", "赔率不足，安全边际不够"),
    ("中", "高"): ("轻仓", "中胜率+高赔率，小仓位试探"),
    ("中", "中"): ("不参与", "胜率赔率均一般，等待更好机会"),
    ("中", "低"): ("不参与", "赔率不足"),
    ("低", "高"): ("不参与", "胜率太低，信号不足"),
    ("低", "中"): ("不参与", "胜率赔率均不足"),
    ("低", "低"): ("不参与", "无投资价值"),
}

POSITION_SIZES = {
    "重仓": "15%-25%",
    "标准仓位": "8%-15%",
    "轻仓": "3%-8%",
    "不参与": "0%",
}


@dataclass
class MatrixResult:
    """决策矩阵输出"""
    win_rate_score: int          # 1-5
    win_rate_level: str          # "高" / "中" / "低"
    win_rate_reasoning: str

    odds_score: int              # 1-5
    odds_level: str              # "高" / "中" / "低"
    odds_reasoning: str

    action: str                  # "重仓" / "标准仓位" / "轻仓" / "不参与"
    position_range: str          # "15%-25%" 等
    reasoning: str               # 综合理由

    def summary(self) -> str:
        lines = [
            f"{'='*50}",
            f"赔率/胜率决策矩阵",
            f"{'='*50}",
            f"",
            f"胜率评分: {self.win_rate_score}/5 ({self.win_rate_level})",
            f"  {self.win_rate_reasoning}",
            f"",
            f"赔率评分: {self.odds_score}/5 ({self.odds_level})",
            f"  {self.odds_reasoning}",
            f"",
            f"{'─'*50}",
            f"建议操作: {self.action}",
            f"建议仓位: {self.position_range}",
            f"理由: {self.reasoning}",
        ]
        return "\n".join(lines)


class OddsMatrix:
    """赔率/胜率决策矩阵

    输入 Combo A 扫描结果 + 赔率 + 资产层级，
    输出评分、仓位建议和理由。
    """

    def evaluate(
        self,
        combo_a: ComboScanResult,
        odds: float,
        asset_tier: str,
        extra_buy_combos: list[ComboScanResult] | None = None,
    ) -> MatrixResult:
        """执行决策矩阵评估

        Args:
            combo_a: Combo A 扫描结果
            odds: 赔率（来自 OEResult.odds）
            asset_tier: 资产层级
            extra_buy_combos: 其他已触发的买入 Combo（B/C/D1/D2），用于加分
        """
        win_score, win_level, win_reason = self._score_win_rate(
            combo_a, extra_buy_combos or []
        )
        odds_score, odds_level, odds_reason = self._score_odds(odds, asset_tier)

        action, base_reason = ACTION_MATRIX[(win_level, odds_level)]
        position_range = POSITION_SIZES[action]

        # 构建综合理由
        reasoning_parts = [base_reason]
        if combo_a.missing:
            missing_names = [s.name.split("（")[0] for s in combo_a.missing]
            reasoning_parts.append(f"Combo A 缺 {len(combo_a.missing)} 条: {', '.join(missing_names)}")
        if odds < 0:
            reasoning_parts.append(f"赔率为负 ({odds:.1%})，无安全边际")
        elif action == "不参与" and odds > 0:
            threshold = ODDS_THRESHOLDS.get(asset_tier, 0.70)
            reasoning_parts.append(f"赔率 {odds:.1%} 未达 {asset_tier} 阈值 {threshold:.0%}")

        return MatrixResult(
            win_rate_score=win_score,
            win_rate_level=win_level,
            win_rate_reasoning=win_reason,
            odds_score=odds_score,
            odds_level=odds_level,
            odds_reasoning=odds_reason,
            action=action,
            position_range=position_range,
            reasoning="；".join(reasoning_parts),
        )

    def _score_win_rate(
        self,
        combo_a: ComboScanResult,
        extra_combos: list[ComboScanResult],
    ) -> tuple[int, str, str]:
        """胜率评分 1-5"""
        a_count = combo_a.triggered_count
        extra_triggered = [c for c in extra_combos if c.triggered]

        if a_count == 4:
            score, reason = 5, f"Combo A 满分 4/4"
        elif a_count == 3 and len(extra_triggered) >= 1:
            extra_names = [c.combo_name for c in extra_triggered]
            score, reason = 4, f"Combo A 3/4 + {', '.join(extra_names)} 触发"
        elif a_count == 3:
            score, reason = 3, f"Combo A 3/4 触发，无其他 Combo 加分"
        elif a_count == 2:
            score, reason = 2, f"Combo A 仅 2/4，信号不足"
        else:
            score, reason = 1, f"Combo A {a_count}/4，信号极弱"

        if score >= 4:
            level = "高"
        elif score == 3:
            level = "中"
        else:
            level = "低"

        return score, level, reason

    def _score_odds(
        self, odds: float, asset_tier: str
    ) -> tuple[int, str, str]:
        """赔率评分 1-5"""
        threshold = ODDS_THRESHOLDS.get(asset_tier)
        if threshold is None:
            raise ValueError(f"未知资产层级: {asset_tier}")

        if odds >= threshold * 1.5:
            score = 5
            reason = f"赔率 {odds:.1%} 远超阈值 {threshold:.0%}（×1.5={threshold*1.5:.0%}），极度低估"
        elif odds >= threshold:
            score = 4
            reason = f"赔率 {odds:.1%} ≥ 阈值 {threshold:.0%}，达标"
        elif odds >= threshold * 0.5:
            score = 3
            reason = f"赔率 {odds:.1%} 接近阈值 {threshold:.0%}（半程 {threshold*0.5:.0%}），有一定空间"
        elif odds > 0:
            score = 2
            reason = f"赔率 {odds:.1%} 为正但远低于阈值 {threshold:.0%}，空间不足"
        else:
            score = 1
            reason = f"赔率 {odds:.1%} 为负或零，无安全边际"

        if score >= 4:
            level = "高"
        elif score == 3:
            level = "中"
        else:
            level = "低"

        return score, level, reason
