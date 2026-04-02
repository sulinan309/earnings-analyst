"""报告生成模块

输出规范：
- 语言：中文
- 风格：密集、数据驱动、行动导向
- 数字精确到亿元（港币），百分比精确到小数点后一位
- 每个分析必须包含：OE计算过程、净现金口径、安全边际判断、Combo信号状态、仓位建议
"""

from .analyzer import AnalysisResult


class ReportGenerator:
    """分析报告生成器"""

    def generate(self, result: AnalysisResult) -> str:
        """生成完整的分析报告"""
        sections = [
            self._header(result),
            self._oe_section(result),
            self._net_cash_section(result),
            self._valuation_section(result),
            self._buy_signals_section(result),
            self._sell_signals_section(result),
            self._decision_section(result),
        ]
        return "\n\n".join(sections)

    def _header(self, r: AnalysisResult) -> str:
        return (
            f"# {r.company.name} ({r.company.ticker}) 财报分析\n"
            f"关注重点: {r.company.focus}\n"
            f"资产层级: {r.company.asset_tier} | 赔率阈值: {r.company.odds_threshold:.0%}"
        )

    def _oe_section(self, r: AnalysisResult) -> str:
        oe = r.oe_result
        lines = [
            "## Owner's Earnings 计算",
            f"- 期间: {oe.period}",
            f"- 经营性现金流 (CFO): {oe.cfo:.2f} 亿",
            f"- 维持性资本支出: {oe.maintenance_capex:.2f} 亿",
            f"- **Owner's Earnings: {oe.oe:.2f} 亿**",
            f"- 扩张性资本支出: {oe.growth_capex:.2f} 亿",
        ]
        if oe.oe_margin is not None:
            lines.append(f"- OE Margin: {oe.oe_margin:.1f}%")
        return "\n".join(lines)

    def _net_cash_section(self, r: AnalysisResult) -> str:
        nc = r.net_cash_result
        lines = [
            "## 净现金（保守口径）",
            f"- 毛净现金: {nc.gross_net_cash:.2f} 亿",
            "- 扣除项:",
        ]
        for key, val in nc.deductions_detail.items():
            lines.append(f"  - {key}: {val:.2f} 亿")
        lines.append(f"- **可分配净现金: {nc.distributable_net_cash:.2f} 亿**")
        return "\n".join(lines)

    def _valuation_section(self, r: AnalysisResult) -> str:
        v = r.valuation_result
        margin_status = "存在" if v.has_safety_margin else "不存在"
        return "\n".join([
            "## 零增长估值",
            f"- 折现率: {v.discount_rate:.1%}",
            f"- 零增长估值: {v.zero_growth_value:.2f} 亿",
            f"- 内在价值（含净现金）: {v.intrinsic_value:.2f} 亿",
            f"- 当前市值: {v.market_cap:.2f} 亿",
            f"- **安全边际: {v.safety_margin_pct:+.1f}% ({margin_status})**",
            f"- 赔率: {v.odds:.1%}",
        ])

    def _buy_signals_section(self, r: AnalysisResult) -> str:
        lines = ["## 买入信号"]
        for signal in r.buy_signals:
            status = "🟢 触发" if signal.triggered else "⚪ 未触发"
            lines.append(f"\n### {signal.combo_name} [{signal.triggered_count}/{signal.total_count}] {status}")
            lines.append(f"权重: {signal.weight}")
            for sub in signal.sub_results:
                icon = "✓" if sub.triggered else "✗"
                lines.append(f"- {icon} {sub.name}: {sub.detail}")
        return "\n".join(lines)

    def _sell_signals_section(self, r: AnalysisResult) -> str:
        lines = ["## 卖出信号"]
        for signal in r.sell_signals:
            status = "🔴 触发" if signal.triggered else "⚪ 未触发"
            lines.append(f"\n### {signal.combo_name} [{signal.triggered_count}/{signal.total_count}] {status}")
            lines.append(f"权重: {signal.weight}")
            for sub in signal.sub_results:
                icon = "✓" if sub.triggered else "✗"
                lines.append(f"- {icon} {sub.name}: {sub.detail}")
        return "\n".join(lines)

    def _decision_section(self, r: AnalysisResult) -> str:
        d = r.decision
        return "\n".join([
            "## 仓位建议",
            f"- **行动: {d.action}**",
            f"- 判定: {d.conviction}",
            f"- 赔率等级: {d.odds_level} | 胜率等级: {d.win_rate_level}",
            f"- 理由: {d.reasoning}",
        ])
