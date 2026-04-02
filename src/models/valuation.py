"""零增长估值模型

零增长估值 = OE / r，r 取 8-12%（港股）
安全边际判断：市值 < 零增长估值 + 可分配净现金

禁止使用多阶段 DCF。
"""

from dataclasses import dataclass


@dataclass
class ValuationResult:
    """估值结果"""
    zero_growth_value: float          # 零增长估值
    intrinsic_value: float            # 内在价值 = 零增长估值 + 可分配净现金
    market_cap: float                 # 当前市值
    safety_margin_pct: float          # 安全边际百分比
    has_safety_margin: bool           # 是否存在安全边际
    discount_rate: float              # 使用的折现率
    odds: float                       # 赔率 = (内在价值 - 市值) / 市值


class ValuationModel:
    """零增长估值模型（李录框架）"""

    def __init__(self, discount_rate: float = 0.10):
        if not 0.08 <= discount_rate <= 0.12:
            raise ValueError(f"折现率 {discount_rate:.1%} 超出港股合理范围 8%-12%")
        self.discount_rate = discount_rate

    def calculate(
        self,
        oe: float,
        distributable_net_cash: float,
        market_cap: float,
    ) -> ValuationResult:
        """计算零增长估值与安全边际

        Args:
            oe: Owner's Earnings（亿港币）
            distributable_net_cash: 可分配净现金（亿港币）
            market_cap: 当前市值（亿港币）
        """
        zero_growth_value = oe / self.discount_rate
        intrinsic_value = zero_growth_value + distributable_net_cash
        safety_margin_pct = (intrinsic_value - market_cap) / market_cap * 100
        odds = (intrinsic_value - market_cap) / market_cap

        return ValuationResult(
            zero_growth_value=round(zero_growth_value, 2),
            intrinsic_value=round(intrinsic_value, 2),
            market_cap=market_cap,
            safety_margin_pct=round(safety_margin_pct, 1),
            has_safety_margin=market_cap < intrinsic_value,
            discount_rate=self.discount_rate,
            odds=round(odds, 4),
        )

    def check_odds_tier(self, odds: float, asset_tier: str) -> str:
        """根据赔率和资产层级判断是否达标

        赔率分层：顶级资产>40%、中等质量>70%、高波动>100%
        """
        thresholds = {
            "顶级资产": 0.40,
            "中等质量": 0.70,
            "高波动": 1.00,
        }
        threshold = thresholds.get(asset_tier)
        if threshold is None:
            raise ValueError(f"未知资产层级: {asset_tier}")

        if odds >= threshold:
            return "达标"
        return "未达标"
