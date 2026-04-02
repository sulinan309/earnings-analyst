"""核心分析器 - 串联所有模块

每个分析必须包含：OE计算过程、净现金口径、安全边际判断、Combo信号状态、仓位建议
"""

from dataclasses import dataclass

from .models import OwnerEarningsCalculator, NetCashCalculator, ValuationModel
from .models.owner_earnings import OwnerEarningsInput, OwnerEarningsResult
from .models.net_cash import NetCashInput, NetCashResult
from .models.valuation import ValuationResult
from .signals import BUY_COMBOS, SELL_COMBOS
from .signals.base import ComboResult
from .decision import DecisionMatrix, DecisionResult
from .data_loader import DataLoader, CompanyConfig


@dataclass
class AnalysisResult:
    """完整分析结果"""
    company: CompanyConfig
    oe_result: OwnerEarningsResult
    net_cash_result: NetCashResult
    valuation_result: ValuationResult
    buy_signals: list[ComboResult]
    sell_signals: list[ComboResult]
    decision: DecisionResult


class EarningsAnalyzer:
    """港股财报分析器 - 李录 Owner's Earnings 框架"""

    def __init__(self, config_path: str | None = None):
        self.data_loader = DataLoader(config_path)
        self.oe_calculator = OwnerEarningsCalculator()
        self.net_cash_calculator = NetCashCalculator()
        self.decision_matrix = DecisionMatrix()

    def analyze(
        self,
        ticker: str,
        oe_input: OwnerEarningsInput,
        net_cash_input: NetCashInput,
        market_cap: float,
        revenue: float | None = None,
        signal_data: dict | None = None,
        discount_rate: float | None = None,
    ) -> AnalysisResult:
        """执行完整的单标的分析

        Args:
            ticker: 股票代码，如 "3690.HK"
            oe_input: OE 计算输入
            net_cash_input: 净现金计算输入
            market_cap: 当前市值（亿港币）
            revenue: 营收（亿港币），用于计算 OE margin
            signal_data: Combo 信号评估所需的额外数据
            discount_rate: 折现率，默认从配置读取
        """
        company = self.data_loader.get_company(ticker)
        if company is None:
            raise ValueError(f"未在 watchlist 中找到 {ticker}")

        params = self.data_loader.get_global_params()
        r = discount_rate or params.default_discount_rate

        # 1. 计算 Owner's Earnings
        oe_result = self.oe_calculator.calculate(oe_input, revenue)

        # 2. 计算保守净现金
        net_cash_result = self.net_cash_calculator.calculate(net_cash_input)

        # 3. 零增长估值
        valuation_model = ValuationModel(discount_rate=r)
        valuation_result = valuation_model.calculate(
            oe=oe_result.oe,
            distributable_net_cash=net_cash_result.distributable_net_cash,
            market_cap=market_cap,
        )

        # 4. 准备信号评估数据
        combo_data = self._build_combo_data(
            company, oe_result, net_cash_result, valuation_result,
            market_cap, signal_data or {},
        )

        # 5. 评估所有 Combo 信号
        buy_signals = [combo().run(combo_data) for combo in BUY_COMBOS]
        sell_signals = [combo().run(combo_data) for combo in SELL_COMBOS]

        # 6. 决策矩阵
        decision = self.decision_matrix.evaluate(
            odds=valuation_result.odds,
            asset_tier=company.asset_tier,
            buy_results=buy_signals,
            sell_results=sell_signals,
        )

        return AnalysisResult(
            company=company,
            oe_result=oe_result,
            net_cash_result=net_cash_result,
            valuation_result=valuation_result,
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            decision=decision,
        )

    def _build_combo_data(
        self,
        company: CompanyConfig,
        oe_result: OwnerEarningsResult,
        net_cash_result: NetCashResult,
        valuation_result: ValuationResult,
        market_cap: float,
        extra_data: dict,
    ) -> dict:
        """构建 Combo 信号评估所需的统一数据字典"""
        base = {
            "company_name": company.name,
            "ticker": company.ticker,
            "asset_tier": company.asset_tier,
            "odds_threshold": company.odds_threshold,
            "market_cap": market_cap,
            "intrinsic_value": valuation_result.intrinsic_value,
            "odds": valuation_result.odds,
            "ttm_oe": oe_result.oe,
            "distributable_net_cash": net_cash_result.distributable_net_cash,
        }
        base.update(extra_data)
        return base
