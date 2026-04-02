"""腾讯 FY2025 财报解析 + 完整 OE 分析

数据来源: tencent.pdf（腾讯控股 2025 年度业绩公告）
原始币种: 人民币，按 1 CNY ≈ 1.1 HKD 换算
"""

from datetime import date

from src.parsers.report_parser import ParsedReport, ExtractedField
from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput, ReportGenerator
from src.output.html_report import generate_html


# ═══════════════════════════════════════════════════════════
#  Step 1: 从 PDF 提取的原始数据（人民币百万元）
# ═══════════════════════════════════════════════════════════

# 来源: 第1页 财务摘要
# 总收入: 751,800 百万元 (7,518 亿)
# 资本开支: 79,198 百万元 (792 亿)
# 自由现金流: 182,600 百万元 (1,826 亿)
# 现金净额: 107,145 百万元 (1,071 亿)

# 来源: 第7页 财务状况表
# 流动资产:
#   定期存款: 236,801
#   受限制现金: 6,977
#   现金及现金等价物: 141,041
# 非流动资产:
#   定期存款: 70,302
# 流动负债:
#   借款: 42,618
#   应付票据: 10,542
# 非流动负债:
#   借款: 208,369
#   应付票据: 126,204

# ═══════════════════════════════════════════════════════════
#  Step 2: 换算为亿港币 (×1.1/100)
# ═══════════════════════════════════════════════════════════

FX = 1.1  # 1 CNY ≈ 1.1 HKD
TO_YI = 100  # 百万 → 亿: /100

def cnm_to_hkb(cnm: float) -> float:
    """人民币百万元 → 亿港币"""
    return round(cnm * FX / TO_YI, 2)


# ── OE 计算 ──
# CFO: 自由现金流 1,826 亿 + 资本开支 792 亿 = 经营性现金流 2,618 亿人民币
# (财报未直接给 CFO，但 FCF = CFO - Capex，所以 CFO = FCF + Capex)
cfo_cnb = 1826 + 792  # 2,618 亿人民币
cfo_hkb = round(cfo_cnb * FX, 2)  # 2,879.8 亿港币

total_capex_cnb = 792  # 亿人民币
total_capex_hkb = round(total_capex_cnb * FX, 2)  # 871.2 亿港币

# 维持性 Capex: 财报未拆分，需估算
# 腾讯 2025 年 Capex 大幅增长主要用于 AI 基础设施扩张
# 保守估计维持性 Capex 约为前几年正常水平 ~400 亿人民币
maintenance_capex_cnb = 400  # 保守估计
maintenance_capex_hkb = round(maintenance_capex_cnb * FX, 2)

# ── 净现金 ──
cash_equiv_cnm = 141_041  # 现金及等价物
short_term_dep_cnm = 236_801  # 流动定期存款
long_term_dep_cnm = 70_302  # 非流动定期存款
restricted_cnm = 6_977  # 受限制现金

# 有息负债
current_borrowing_cnm = 42_618
current_notes_cnm = 10_542
noncurrent_borrowing_cnm = 208_369
noncurrent_notes_cnm = 126_204
total_debt_cnm = (current_borrowing_cnm + current_notes_cnm
                  + noncurrent_borrowing_cnm + noncurrent_notes_cnm)

# 营收
revenue_cnm = 751_800

# ═══════════════════════════════════════════════════════════
#  Step 3: 构建 ParsedReport（展示解析结果）
# ═══════════════════════════════════════════════════════════

parsed = ParsedReport(
    company_name="腾讯控股",
    ticker="0700.HK",
    period="FY2025",
    original_currency="人民币",
    exchange_rate_note="按 1 CNY = 1.1 HKD 换算",
    cfo=ExtractedField(
        value=cfo_hkb,
        source="FCF(1,826亿)+Capex(792亿)=CFO(2,618亿人民币)→2,879.8亿港币",
    ),
    total_capex=ExtractedField(
        value=total_capex_hkb,
        source="第1页: 资本开支为人民币792亿元",
    ),
    maintenance_capex=ExtractedField(
        value=maintenance_capex_hkb,
        reason="财报未拆分维持性vs扩张性; 保守估计维持性~400亿人民币(前几年正常水平)",
        source="分析师估算",
    ),
    growth_capex=ExtractedField(
        value=round((total_capex_cnb - maintenance_capex_cnb) * FX, 2),
        source="总Capex 792 - 维持性 400 = 扩张性 392 亿人民币",
    ),
    cash_and_equivalents=ExtractedField(
        value=cnm_to_hkb(cash_equiv_cnm),
        source="第8页: 现金及现金等价物 141,041百万元",
    ),
    short_term_investments=ExtractedField(
        value=cnm_to_hkb(short_term_dep_cnm + long_term_dep_cnm),
        source="第8页: 流动定期存款236,801 + 非流动定期存款70,302 = 307,103百万元",
    ),
    interest_bearing_debt=ExtractedField(
        value=cnm_to_hkb(total_debt_cnm),
        source="第9页: 借款(42,618+208,369)+应付票据(10,542+126,204)=387,733百万元",
    ),
    revenue=ExtractedField(
        value=cnm_to_hkb(revenue_cnm),
        source="第1页: 总收入为人民币7,518亿元",
    ),
    committed_investments=ExtractedField(
        value=None,
        reason="业绩公告未披露资本承诺明细，需查阅完整年报附注",
    ),
    restricted_cash=ExtractedField(
        value=cnm_to_hkb(restricted_cnm),
        source="第8页: 受限制现金 6,977百万元",
    ),
    overseas_cash=ExtractedField(
        value=None,
        reason="财报未按地区拆分现金持有情况",
    ),
)

print("═" * 60)
print("  Step 1: PDF 解析结果")
print("═" * 60)
print(parsed.to_json())

missing = parsed.missing_fields()
if missing:
    print(f"\n缺失字段 ({len(missing)} 项):")
    for name, reason in missing:
        print(f"  • {name}: {reason}")


# ═══════════════════════════════════════════════════════════
#  Step 4: 构建 FinancialData 并运行完整分析
# ═══════════════════════════════════════════════════════════

# 缺失字段使用保守默认值
committed_inv_hkb = 100.0   # 保守估计已承诺投资 ~100 亿港币
overseas_cash_hkb = 200.0   # 国际游戏+海外云业务，估计海外现金 ~200 亿港币

# 腾讯当前市值约 4.2 万亿港币（2026年4月）
market_cap_hkb = 42000.0

financial_data = FinancialData(
    cfo=cfo_hkb,
    maintenance_capex=maintenance_capex_hkb,
    total_capex=total_capex_hkb,
    cash_and_equivalents=parsed.cash_and_equivalents.value,
    short_term_investments=parsed.short_term_investments.value,
    interest_bearing_debt=parsed.interest_bearing_debt.value,
    committed_investments=committed_inv_hkb,
    restricted_cash=parsed.restricted_cash.value,
    overseas_cash=overseas_cash_hkb,
    revenue=parsed.revenue.value,
    market_cap=market_cap_hkb,
    period="FY2025",
    ticker="0700.HK",
)

print(f"\n\n{'═' * 60}")
print("  Step 2-5: 完整 OE 分析报告")
print("═" * 60)\

# OE 计算
oe_result = OECalculator(discount_rate=0.10).calculate(financial_data)

# Combo A 扫描
# 腾讯为顶级资产，赔率阈值 40%
# 近4季度 OE 用 FY2025 各季度数据估算（CFO - 维持性Capex 按季均分）
quarterly_oe_est = [
    round((cfo_hkb - maintenance_capex_hkb) / 4, 1)
] * 4  # 简化为均匀分布

combo_a = ComboScanner().scan_combo_a(
    oe_result,
    ComboAInput(
        asset_tier="顶级资产",
        quarterly_oes=quarterly_oe_est,
        oe_multiple_percentile=40.0,  # 腾讯当前估值处于历史中位偏上
        structural_deterioration=False,
    ),
)

# 决策矩阵
matrix_result = OddsMatrix().evaluate(combo_a, oe_result.odds, "顶级资产")

# 生成文本报告
report_input = ReportInput(
    company_name="腾讯",
    ticker="0700.HK",
    asset_tier="顶级资产",
    focus="投资组合公允价值、回购力度、AI 投入 ROI",
    financial_data=financial_data,
    oe_result=oe_result,
    combo_a=combo_a,
    matrix_result=matrix_result,
    report_date=date(2026, 4, 2),
)

print(ReportGenerator().generate(report_input))

# 生成 HTML 报告
html = generate_html(report_input)
html_path = "data/tencent_report.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n\nHTML 报告已保存至: {html_path}")
