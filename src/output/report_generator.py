"""分析报告生成器

整合三个模块的输出：
1. OECalculator → OEResult（OE、净现金、估值、安全边际）
2. ComboScanner → ComboScanResult（Combo A 子条件触发状态）
3. OddsMatrix → MatrixResult（胜率/赔率评分、仓位建议）

输出规范（来自 CLAUDE.md）：
- 语言：中文
- 风格：密集、数据驱动、行动导向
- 每个分析必须包含：OE计算过程、净现金口径、安全边际判断、Combo信号状态、仓位建议
- 数字精确到亿元（港币），百分比精确到小数点后一位
"""

from dataclasses import dataclass
from datetime import date

from src.frameworks.oe_calculator import OEResult, FinancialData
from src.signals.combo_scanner import ComboScanResult
from src.frameworks.odds_matrix import MatrixResult


@dataclass
class ReportInput:
    """报告生成所需的全部输入"""
    company_name: str
    ticker: str
    asset_tier: str
    focus: str
    financial_data: FinancialData
    oe_result: OEResult
    combo_a: ComboScanResult
    matrix_result: MatrixResult
    report_date: date | None = None


class ReportGenerator:
    """中文分析报告生成器"""

    def generate(self, inp: ReportInput) -> str:
        """生成完整分析报告"""
        d = inp.report_date or date.today()
        sections = [
            self._header(inp, d),
            self._oe_section(inp),
            self._net_cash_section(inp),
            self._valuation_section(inp),
            self._sensitivity_section(inp),
            self._combo_section(inp),
            self._decision_section(inp),
            self._next_steps(inp),
        ]
        return "\n\n".join(sections)

    # ── 各段落 ──

    def _header(self, inp: ReportInput, d: date) -> str:
        return "\n".join([
            f"{'#' * 60}",
            f"  {inp.company_name} ({inp.ticker}) 深度分析报告",
            f"  报告日期: {d.isoformat()}  |  财报期间: {inp.oe_result.period}",
            f"  资产层级: {inp.asset_tier}  |  关注重点: {inp.focus}",
            f"{'#' * 60}",
        ])

    def _oe_section(self, inp: ReportInput) -> str:
        oe = inp.oe_result
        fd = inp.financial_data
        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  1. Owner's Earnings 计算                       │",
            "└─────────────────────────────────────────────────┘",
            "",
            f"  经营性现金流 (CFO)       {oe.cfo:>10.2f} 亿",
            f"- 维持性资本支出            {oe.maintenance_capex:>10.2f} 亿  ← 从附注拆分",
            f"{'─' * 40}",
            f"= Owner's Earnings (OE)    {oe.oe:>10.2f} 亿",
            "",
            f"  OE Margin:               {oe.oe_margin_pct:.1f}%  (OE {oe.oe:.1f} / 营收 {fd.revenue:.1f})",
            f"  扩张性 Capex:            {oe.growth_capex:>10.2f} 亿  (总Capex {fd.total_capex:.1f} - 维持性 {oe.maintenance_capex:.1f})",
        ]
        return "\n".join(lines)

    def _net_cash_section(self, inp: ReportInput) -> str:
        oe = inp.oe_result
        fd = inp.financial_data
        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  2. 净现金（保守口径）                           │",
            "└─────────────────────────────────────────────────┘",
            "",
            f"  现金及等价物             {fd.cash_and_equivalents:>10.2f} 亿",
            f"+ 短期理财                 {fd.short_term_investments:>10.2f} 亿",
            f"- 有息负债                 {fd.interest_bearing_debt:>10.2f} 亿",
            f"{'─' * 40}",
            f"= 毛净现金                 {oe.gross_net_cash:>10.2f} 亿",
            "",
            "  扣除项:",
            f"    运营储备 (1.5个月营收)  {oe.operating_reserve:>10.2f} 亿",
            f"    已承诺投资款            {fd.committed_investments:>10.2f} 亿",
            f"    受限资金                {fd.restricted_cash:>10.2f} 亿",
            f"    海外现金回流折扣 (15%)  {fd.overseas_cash * 0.15:>10.2f} 亿",
            f"  {'─' * 38}",
            f"  扣除合计                 {oe.total_deductions:>10.2f} 亿",
            "",
            f"= 可分配净现金             {oe.distributable_net_cash:>10.2f} 亿",
        ]
        return "\n".join(lines)

    def _valuation_section(self, inp: ReportInput) -> str:
        oe = inp.oe_result
        margin_tag = "存在安全边际" if oe.has_safety_margin else "无安全边际"
        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  3. 零增长估值与安全边际                         │",
            "└─────────────────────────────────────────────────┘",
            "",
            f"  零增长估值 = OE / r = {oe.oe:.1f} / {oe.discount_rate:.0%} = {oe.zero_growth_value:.2f} 亿",
            f"  内在价值   = {oe.zero_growth_value:.1f} + {oe.distributable_net_cash:.1f} = {oe.intrinsic_value:.2f} 亿",
            f"  当前市值   = {oe.market_cap:.2f} 亿",
            "",
            f"  安全边际   = {oe.intrinsic_value:.1f} - {oe.market_cap:.1f} = {oe.safety_margin:+.2f} 亿 ({oe.safety_margin_pct:+.1f}%)",
            f"  赔率       = {oe.odds:.1%}",
            f"  判定: {margin_tag}",
        ]
        return "\n".join(lines)

    def _sensitivity_section(self, inp: ReportInput) -> str:
        """折现率敏感性表格"""
        from src.frameworks.oe_calculator import OECalculator
        results = OECalculator(discount_rate=0.10).sensitivity(inp.financial_data)
        lines = [
            "  折现率敏感性分析:",
            f"  {'折现率':>8} {'零增长估值':>10} {'内在价值':>10} {'安全边际':>10} {'赔率':>8}",
            f"  {'─' * 52}",
        ]
        for r in results:
            lines.append(
                f"  {r.discount_rate:>8.0%} {r.zero_growth_value:>10.1f} {r.intrinsic_value:>10.1f}"
                f" {r.safety_margin_pct:>+10.1f}% {r.odds:>8.1%}"
            )
        return "\n".join(lines)

    def _combo_section(self, inp: ReportInput) -> str:
        ca = inp.combo_a
        status = "触发" if ca.triggered else "未触发"
        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  4. Combo A · 估值安全边际型                     │",
            "└─────────────────────────────────────────────────┘",
            "",
            f"  总体判定: [{ca.triggered_count}/{ca.total_count}] {status}  (≥3/4 即有效)",
            "",
        ]
        for sc in ca.sub_conditions:
            icon = "✅" if sc.triggered else "❌"
            lines.append(f"  {icon} {sc.name}")
            lines.append(f"     {sc.detail}")
            if sc.gap:
                lines.append(f"     → 差距: {sc.gap}")
            lines.append("")

        if ca.missing:
            lines.append(f"  未达标项 ({len(ca.missing)} 条):")
            for sc in ca.missing:
                lines.append(f"    • {sc.name}")
                lines.append(f"      {sc.gap}")
        return "\n".join(lines)

    def _decision_section(self, inp: ReportInput) -> str:
        m = inp.matrix_result
        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  5. 仓位决策                                     │",
            "└─────────────────────────────────────────────────┘",
            "",
            f"  胜率: {m.win_rate_score}/5 ({m.win_rate_level}胜率)",
            f"    {m.win_rate_reasoning}",
            "",
            f"  赔率: {m.odds_score}/5 ({m.odds_level}赔率)",
            f"    {m.odds_reasoning}",
            "",
            f"  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓",
            f"  ┃  建议操作: {m.action:<10}  建议仓位: {m.position_range:<10}  ┃",
            f"  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛",
            "",
            f"  理由: {m.reasoning}",
        ]
        return "\n".join(lines)

    def _next_steps(self, inp: ReportInput) -> str:
        m = inp.matrix_result
        oe = inp.oe_result

        lines = [
            "┌─────────────────────────────────────────────────┐",
            "│  6. 后续跟踪要点                                 │",
            "└─────────────────────────────────────────────────┘",
            "",
        ]

        if m.action == "不参与":
            lines.append("  当前不建议建仓，关注以下触发条件：")
            if oe.odds < 0.70:  # 中等质量阈值
                target_mcap = oe.intrinsic_value / 1.70
                lines.append(f"  • 赔率达标: 需市值降至 {target_mcap:.0f} 亿以下（当前 {oe.market_cap:.0f} 亿）")
            lines.append(f"  • 或 OE 提升: 需 OE 从 {oe.oe:.0f} 亿提升至使内在价值覆盖 70% 赔率")
            lines.append(f"  • 关注下季财报是否出现 Combo B（基本面拐点）信号")
        elif m.action in ("轻仓", "标准仓位", "重仓"):
            lines.append(f"  已达建仓条件 ({m.action})，执行前必须：")
            lines.append(f"  • 写入核心假设至 data/assumptions/{inp.company_name}.md")
            lines.append(f"  • 设定止损: 关注 Combo H（逻辑证伪）触发条件")
            lines.append(f"  • 设定止盈: 关注 Combo E（估值透支）触发条件")

        lines.append(f"\n  数据来源: 公司财报原文 > 港交所公告 > 管理层业绩会纪要")
        return "\n".join(lines)
