"""赔率/胜率决策矩阵

- 高胜率 + 高赔率 → 重仓
- 高胜率 + 中赔率 → 标准仓位
- 中胜率 + 高赔率 → 轻仓
- 其余 → 不参与

赔率分层：顶级资产>40%、中等质量>70%、高波动>100%
"""

from dataclasses import dataclass
from .signals.base import ComboResult


@dataclass
class DecisionResult:
    """决策输出"""
    action: str           # "重仓买入" / "标准买入" / "轻仓买入" / "不参与" / "减仓" / "清仓"
    conviction: str       # "高胜率+高赔率" / "高胜率+中赔率" / "中胜率+高赔率" / "不足"
    odds_level: str       # "高赔率" / "中赔率" / "低赔率"
    win_rate_level: str   # "高胜率" / "中胜率" / "低胜率"
    reasoning: str        # 决策理由
    active_buy_combos: list[str]    # 触发的买入Combo
    active_sell_combos: list[str]   # 触发的卖出Combo


class DecisionMatrix:
    """赔率/胜率决策矩阵"""

    def evaluate(
        self,
        odds: float,
        asset_tier: str,
        buy_results: list[ComboResult],
        sell_results: list[ComboResult],
    ) -> DecisionResult:
        """综合 Combo 信号与赔率生成仓位决策"""

        active_buy = [r for r in buy_results if r.triggered]
        active_sell = [r for r in sell_results if r.triggered]
        active_buy_names = [r.combo_name for r in active_buy]
        active_sell_names = [r.combo_name for r in active_sell]

        # 卖出信号优先级检查
        # Combo H（逻辑证伪）触发 → 直接清仓
        if any("Combo H" in name for name in active_sell_names):
            return DecisionResult(
                action="清仓",
                conviction="逻辑证伪",
                odds_level=self._classify_odds(odds, asset_tier),
                win_rate_level="不适用",
                reasoning="Combo H 逻辑证伪触发，核心假设被否定，必须退出",
                active_buy_combos=active_buy_names,
                active_sell_combos=active_sell_names,
            )

        # 其他核心卖出信号触发
        core_sell_triggered = [
            r for r in active_sell
            if r.weight == "核心" and "Combo H" not in r.combo_name
        ]
        if len(core_sell_triggered) >= 2:
            return DecisionResult(
                action="减仓",
                conviction="多重卖出信号",
                odds_level=self._classify_odds(odds, asset_tier),
                win_rate_level="不适用",
                reasoning=f"多个核心卖出信号触发: {', '.join(r.combo_name for r in core_sell_triggered)}",
                active_buy_combos=active_buy_names,
                active_sell_combos=active_sell_names,
            )

        # 买入决策
        odds_level = self._classify_odds(odds, asset_tier)
        win_rate_level = self._classify_win_rate(active_buy)

        action = self._determine_action(win_rate_level, odds_level)
        conviction = f"{win_rate_level}+{odds_level}"

        reasoning_parts = []
        if active_buy_names:
            reasoning_parts.append(f"买入信号: {', '.join(active_buy_names)}")
        if active_sell_names:
            reasoning_parts.append(f"卖出信号: {', '.join(active_sell_names)}")
        reasoning_parts.append(f"赔率 {odds:.1%} ({odds_level})，胜率判定 {win_rate_level}")

        return DecisionResult(
            action=action,
            conviction=conviction,
            odds_level=odds_level,
            win_rate_level=win_rate_level,
            reasoning="；".join(reasoning_parts),
            active_buy_combos=active_buy_names,
            active_sell_combos=active_sell_names,
        )

    def _classify_odds(self, odds: float, asset_tier: str) -> str:
        thresholds = {"顶级资产": 0.40, "中等质量": 0.70, "高波动": 1.00}
        threshold = thresholds.get(asset_tier, 0.70)
        if odds >= threshold:
            return "高赔率"
        if odds >= threshold * 0.5:
            return "中赔率"
        return "低赔率"

    def _classify_win_rate(self, active_buy: list[ComboResult]) -> str:
        """根据触发的买入 Combo 数量和质量判定胜率"""
        core_buys = [r for r in active_buy if r.weight == "核心"]
        has_combo_a = any("Combo A" in r.combo_name for r in active_buy)

        if has_combo_a and len(core_buys) >= 2:
            return "高胜率"
        if has_combo_a or len(core_buys) >= 1:
            return "中胜率"
        return "低胜率"

    def _determine_action(self, win_rate: str, odds: str) -> str:
        matrix = {
            ("高胜率", "高赔率"): "重仓买入",
            ("高胜率", "中赔率"): "标准买入",
            ("高胜率", "低赔率"): "不参与",
            ("中胜率", "高赔率"): "轻仓买入",
            ("中胜率", "中赔率"): "不参与",
            ("中胜率", "低赔率"): "不参与",
            ("低胜率", "高赔率"): "不参与",
            ("低胜率", "中赔率"): "不参与",
            ("低胜率", "低赔率"): "不参与",
        }
        return matrix.get((win_rate, odds), "不参与")
