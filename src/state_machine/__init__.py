"""个股状态机（量化状态识别器 v2.0）

基于《量化状态机设计 v2.0》业务文档实现。

系统不输出"买/卖"信号，而是输出 7 项：
  1. 当前状态  2. 状态置信度  3. 触发证据  4. 数据质量
  5. 组合约束  6. 建议动作    7. 是否需要写 Decision Log

量化负责"稳定识别状态"，人工保留价值锚、基本面判断、组合约束与最终决策。
"""

from .states import State, BASE_WEIGHTS, RISK_STATES, STATE_DESCRIPTIONS
from .market_data import Bar, MarketData, KeyLevels, FlowData, Features
from .profile import TargetProfile, resolve_weights, PROFILE_ADJUSTMENTS
from .engine import StateEngine, StateResult, EngineInput, PortfolioConstraint
from .report import format_report

__all__ = [
    "State",
    "BASE_WEIGHTS",
    "RISK_STATES",
    "STATE_DESCRIPTIONS",
    "Bar",
    "MarketData",
    "KeyLevels",
    "FlowData",
    "Features",
    "TargetProfile",
    "resolve_weights",
    "PROFILE_ADJUSTMENTS",
    "StateEngine",
    "StateResult",
    "EngineInput",
    "PortfolioConstraint",
    "format_report",
]
