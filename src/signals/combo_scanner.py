"""Combo 信号扫描器

接收 OEResult + 补充数据，逐条评估 Combo 子条件，
输出触发状态、未达标项及差距分析。
"""

from dataclasses import dataclass

from src.frameworks.oe_calculator import OEResult


@dataclass
class SubCondition:
    """单个子条件评估结果"""
    name: str
    triggered: bool
    detail: str           # 具体数值说明
    gap: str | None       # 未触发时的差距描述，触发时为 None


@dataclass
class ComboScanResult:
    """Combo 扫描结果"""
    combo_name: str
    sub_conditions: list[SubCondition]
    triggered_count: int
    total_count: int
    triggered: bool                     # ≥3/4
    missing: list[SubCondition]         # 未触发的子条件

    def summary(self) -> str:
        status = "触发" if self.triggered else "未触发"
        lines = [
            f"{'='*50}",
            f"{self.combo_name}  [{self.triggered_count}/{self.total_count}] {status}",
            f"{'='*50}",
        ]
        for sc in self.sub_conditions:
            icon = "✅" if sc.triggered else "❌"
            lines.append(f"  {icon} {sc.name}")
            lines.append(f"     {sc.detail}")
            if sc.gap:
                lines.append(f"     ⚠ 差距: {sc.gap}")
        if self.missing:
            lines.append(f"\n未达标项 ({len(self.missing)} 条):")
            for sc in self.missing:
                lines.append(f"  - {sc.name}: {sc.gap}")
        return "\n".join(lines)


@dataclass
class ComboAInput:
    """Combo A 评估所需的补充数据（OEResult 之外的部分）

    Attributes:
        asset_tier: 资产层级 "顶级资产" / "中等质量" / "高波动"
        quarterly_oes: 最近4个季度的 OE（亿港币），用于稳定性判断
        oe_multiple_percentile: 当前市值/OE在历史中的分位数 (0-100)
        structural_deterioration: 增长质量是否出现结构性恶化
    """
    asset_tier: str
    quarterly_oes: list[float]
    oe_multiple_percentile: float
    structural_deterioration: bool


ODDS_THRESHOLDS = {
    "顶级资产": 0.40,
    "中等质量": 0.70,
    "高波动": 1.00,
}


class ComboScanner:
    """Combo 信号扫描器"""

    def scan_combo_a(self, oe_result: OEResult, extra: ComboAInput) -> ComboScanResult:
        """扫描 Combo A · 估值安全边际型

        4个子条件：
        1. 市值 < 零增长OE估值 + 可分配净现金
        2. 赔率达标（顶级资产>40%、中等质量>70%、高波动>100%）
        3. 过去12个月OE为正且稳定（非一次性）
        4. 市值/OE处于历史低分位，且当前增长质量无结构性恶化
        """
        subs: list[SubCondition] = []

        # ── 条件1: 市值 < 内在价值 ──
        c1 = oe_result.has_safety_margin
        gap1 = None
        if not c1:
            shortfall = oe_result.market_cap - oe_result.intrinsic_value
            gap1 = f"市值高出内在价值 {shortfall:.1f} 亿，需下跌 {shortfall / oe_result.market_cap * 100:.1f}% 或 OE 提升"
        subs.append(SubCondition(
            name="市值 < 零增长OE估值 + 可分配净现金",
            triggered=c1,
            detail=f"市值 {oe_result.market_cap:.1f} 亿 vs 内在价值 {oe_result.intrinsic_value:.1f} 亿 (边际 {oe_result.safety_margin_pct:+.1f}%)",
            gap=gap1,
        ))

        # ── 条件2: 赔率达标 ──
        threshold = ODDS_THRESHOLDS.get(extra.asset_tier)
        if threshold is None:
            raise ValueError(f"未知资产层级: {extra.asset_tier}")
        c2 = oe_result.odds >= threshold
        gap2 = None
        if not c2:
            needed_odds = threshold
            # 反推达标所需市值: intrinsic / (1 + threshold)
            target_mcap = oe_result.intrinsic_value / (1 + needed_odds)
            gap2 = (
                f"当前赔率 {oe_result.odds:.1%}，{extra.asset_tier}需 ≥{threshold:.0%}，"
                f"需市值降至 {target_mcap:.0f} 亿或内在价值提升至 {oe_result.market_cap * (1 + threshold):.0f} 亿"
            )
        subs.append(SubCondition(
            name=f"赔率达标（{extra.asset_tier} ≥{threshold:.0%}）",
            triggered=c2,
            detail=f"赔率 {oe_result.odds:.1%}，阈值 {threshold:.0%}",
            gap=gap2,
        ))

        # ── 条件3: 过去12个月OE为正且稳定 ──
        oes = extra.quarterly_oes
        all_positive = len(oes) >= 4 and all(q > 0 for q in oes[-4:])
        stable = False
        if all_positive:
            avg = sum(oes[-4:]) / 4
            max_dev = max(abs(q - avg) / avg for q in oes[-4:])
            stable = max_dev <= 0.30  # 波动率 ≤30% 视为稳定
        c3 = all_positive and stable
        gap3 = None
        if not c3:
            if not all_positive:
                negatives = [f"Q{i+1}={q:.1f}" for i, q in enumerate(oes[-4:]) if q <= 0]
                gap3 = f"OE 存在非正值: {', '.join(negatives) if negatives else '数据不足4季'}"
            else:
                avg = sum(oes[-4:]) / 4
                max_dev = max(abs(q - avg) / avg for q in oes[-4:])
                gap3 = f"OE 波动率 {max_dev:.1%} 超过 30% 阈值，疑似一次性收益"
        oe_display = [f"{q:.1f}" for q in oes[-4:]] if len(oes) >= 4 else [f"{q:.1f}" for q in oes]
        subs.append(SubCondition(
            name="过去12个月OE为正且稳定",
            triggered=c3,
            detail=f"近4季OE: [{', '.join(oe_display)}] 亿，全正={'是' if all_positive else '否'}，稳定={'是' if stable else '否'}",
            gap=gap3,
        ))

        # ── 条件4: 市值/OE处于历史低分位 + 无结构性恶化 ──
        low_percentile = extra.oe_multiple_percentile <= 30
        no_deterioration = not extra.structural_deterioration
        c4 = low_percentile and no_deterioration
        gap4 = None
        if not c4:
            parts = []
            if not low_percentile:
                parts.append(f"市值/OE 分位 {extra.oe_multiple_percentile:.0f}%（需 ≤30%）")
            if not no_deterioration:
                parts.append("增长质量存在结构性恶化")
            gap4 = "；".join(parts)
        subs.append(SubCondition(
            name="市值/OE历史低分位 + 无结构性恶化",
            triggered=c4,
            detail=f"历史分位 {extra.oe_multiple_percentile:.0f}%，结构性恶化={'是' if extra.structural_deterioration else '否'}",
            gap=gap4,
        ))

        # ── 汇总 ──
        triggered_count = sum(1 for s in subs if s.triggered)
        missing = [s for s in subs if not s.triggered]

        return ComboScanResult(
            combo_name="Combo A · 估值安全边际型",
            sub_conditions=subs,
            triggered_count=triggered_count,
            total_count=len(subs),
            triggered=triggered_count >= 3,
            missing=missing,
        )
