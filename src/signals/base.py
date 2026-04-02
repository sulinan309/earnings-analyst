"""Combo 信号基类

所有 Combo 信号共享的基础逻辑：
- 每个 Combo 包含4个子条件
- ≥3/4 子条件触发才判定该 Combo 有效
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SubConditionResult:
    """单个子条件的评估结果"""
    name: str
    triggered: bool
    detail: str          # 具体数据说明
    data_source: str     # 数据来源


@dataclass
class ComboResult:
    """Combo 信号评估结果"""
    combo_name: str
    combo_type: str                           # "买入" 或 "卖出"
    triggered: bool                           # ≥3/4 子条件触发
    sub_results: list[SubConditionResult]
    triggered_count: int
    total_count: int
    weight: str                               # "核心" / "加分项" / "确认器" / "辅助"
    summary: str


class ComboSignal(ABC):
    """Combo 信号基类"""

    COMBO_NAME: str = ""
    COMBO_TYPE: str = ""      # "买入" 或 "卖出"
    WEIGHT: str = "核心"      # "核心" / "加分项" / "确认器" / "辅助"
    THRESHOLD: int = 3        # 触发阈值，默认 3/4

    @abstractmethod
    def evaluate(self, data: dict) -> list[SubConditionResult]:
        """评估所有子条件，返回子条件结果列表"""

    def run(self, data: dict) -> ComboResult:
        """运行完整 Combo 评估"""
        sub_results = self.evaluate(data)
        triggered_count = sum(1 for r in sub_results if r.triggered)
        triggered = triggered_count >= self.THRESHOLD

        summary_parts = []
        for r in sub_results:
            status = "✓" if r.triggered else "✗"
            summary_parts.append(f"  {status} {r.name}: {r.detail}")

        summary = f"{self.COMBO_NAME} [{triggered_count}/{len(sub_results)}] {'触发' if triggered else '未触发'}\n"
        summary += "\n".join(summary_parts)

        return ComboResult(
            combo_name=self.COMBO_NAME,
            combo_type=self.COMBO_TYPE,
            triggered=triggered,
            sub_results=sub_results,
            triggered_count=triggered_count,
            total_count=len(sub_results),
            weight=self.WEIGHT,
            summary=summary,
        )
