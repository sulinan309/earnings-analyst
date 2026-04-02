"""数据加载模块

数据来源优先级：
1. 公司财报原文
2. 港交所公告
3. 管理层业绩会纪要
4. 第三方数据仅作交叉验证
"""

import json
import os
from dataclasses import dataclass


CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


@dataclass
class CompanyConfig:
    """Watchlist 中的公司配置"""
    name: str
    ticker: str
    focus: str
    asset_tier: str
    odds_threshold: float
    key_metrics: list[str]


@dataclass
class GlobalParams:
    """全局分析参数"""
    discount_rate_range: tuple[float, float]
    default_discount_rate: float
    operating_reserve_months: float
    overseas_cash_discount: float
    currency: str
    precision_unit: str


class DataLoader:
    """数据加载与配置管理"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or os.path.join(CONFIG_DIR, "watchlist.json")
        self._config: dict | None = None

    def _load_config(self) -> dict:
        if self._config is None:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        return self._config

    def get_watchlist(self) -> list[CompanyConfig]:
        """加载 watchlist 中所有公司配置"""
        config = self._load_config()
        companies = []
        for item in config["watchlist"]:
            companies.append(CompanyConfig(
                name=item["name"],
                ticker=item["ticker"],
                focus=item["focus"],
                asset_tier=item["asset_tier"],
                odds_threshold=item["odds_threshold"],
                key_metrics=item["key_metrics"],
            ))
        return companies

    def get_company(self, ticker: str) -> CompanyConfig | None:
        """按代码查找公司配置"""
        for company in self.get_watchlist():
            if company.ticker == ticker:
                return company
        return None

    def get_global_params(self) -> GlobalParams:
        """加载全局分析参数"""
        config = self._load_config()
        p = config["global_params"]
        return GlobalParams(
            discount_rate_range=tuple(p["discount_rate_range"]),
            default_discount_rate=p["default_discount_rate"],
            operating_reserve_months=p["operating_reserve_months"],
            overseas_cash_discount=p["overseas_cash_discount"],
            currency=p["currency"],
            precision_unit=p["precision_unit"],
        )

    def load_assumption(self, company_name: str) -> str | None:
        """加载买入时的核心假设"""
        filepath = os.path.join(DATA_DIR, "assumptions", f"{company_name}.md")
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read().strip()
        return None

    def save_assumption(self, company_name: str, assumption: str) -> str:
        """保存买入核心假设（买入前必须执行）"""
        assumptions_dir = os.path.join(DATA_DIR, "assumptions")
        os.makedirs(assumptions_dir, exist_ok=True)
        filepath = os.path.join(assumptions_dir, f"{company_name}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(assumption.strip() + "\n")
        return filepath
