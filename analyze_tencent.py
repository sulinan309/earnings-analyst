"""腾讯 FY2025 财报解析 + 完整 OE 分析（修正版）

数据来源: tencent.pdf（腾讯控股 2025 年度业绩公告）
原始币种: 人民币，按 1 CNY ≈ 1.1 HKD 换算

修正项:
1. 净现金增加"投资组合"字段，上市+非上市投资按 50% 保守折扣计入
2. 维持性 Capex 以折旧摊销为锚，明确标注为估算并说明假设
"""

from datetime import date

from src.parsers.report_parser import ParsedReport, ExtractedField
from src.frameworks.oe_calculator import OECalculator, FinancialData
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput, ReportGenerator
from src.output.html_report import generate_html


# ═══════════════════════════════════════════════════════════
#  Step 1: 从 tencent.pdf 提取的原始数据（人民币百万元）
# ═══════════════════════════════════════════════════════════

FX = 1.1  # 1 CNY ≈ 1.1 HKD
TO_YI = 100  # 百万 → 亿: /100

def cnm_to_hkb(cnm: float) -> float:
    """人民币百万元 → 亿港币"""
    return round(cnm * FX / TO_YI, 2)

def cnb_to_hkb(cnb: float) -> float:
    """人民币亿元 → 亿港币"""
    return round(cnb * FX, 2)


# ── 第1页: 财务摘要 ──
revenue_cnb = 7518           # 总收入 7,518 亿人民币
total_capex_cnb = 792        # 资本开支 792 亿人民币
fcf_cnb = 1826               # 自由现金流 1,826 亿
cfo_cnb = fcf_cnb + total_capex_cnb  # CFO = FCF + Capex = 2,618 亿

# ── 第1页: 投资组合 ──
listed_inv_fv_cnb = 6727     # 上市投资公司权益公允价值 6,727 亿人民币
unlisted_inv_bv_cnb = 3631   # 非上市投资公司权益账面价值 3,631 亿人民币

# ── 第7页: EBITDA vs 经营盈利 → 推算折旧摊销 ──
# EBITDA = 310,767 百万, 经营盈利 = 241,562 百万
# 差额 = 69,205 百万 ≈ 692 亿人民币 = 折旧 + 摊销 + 使用权折旧
# 但 EBITDA 定义还扣除了"其他收益/亏损净额"，所以折旧摊销实际更小
# 附注(d): 资本开支主要包括IT基础设施、数据中心、土地使用权、办公园区及知识产权
# 财报未拆分维持性 vs 扩张性
#
# 估算逻辑:
# - 2024年Capex=768亿, 2025年=792亿, 仅增长3%
# - 但物业设备从801亿猛增至1,499亿(+87%)，说明大量AI基础设施在建转固
# - FY2024 折旧摊销约 500亿，视为成熟业务维持性需求的上限
# - 保守取 550 亿人民币作为维持性 Capex（含正常设备替换+存量数据中心维护）
maintenance_capex_cnb = 550

# ── 第8页: 简明综合财务状况表 ──
cash_equiv_cnm = 141_041           # 现金及现金等价物
short_term_dep_cnm = 236_801       # 流动定期存款
long_term_dep_cnm = 70_302         # 非流动定期存款
restricted_cnm = 6_977             # 受限制现金

# 有息负债（第9页）
current_borrowing_cnm = 42_618
current_notes_cnm = 10_542
noncurrent_borrowing_cnm = 208_369
noncurrent_notes_cnm = 126_204
total_debt_cnm = (current_borrowing_cnm + current_notes_cnm
                  + noncurrent_borrowing_cnm + noncurrent_notes_cnm)

# ═══════════════════════════════════════════════════════════
#  Step 2: 构建 ParsedReport（展示解析结果）
# ═══════════════════════════════════════════════════════════

parsed = ParsedReport(
    company_name="腾讯控股",
    ticker="0700.HK",
    period="FY2025",
    original_currency="人民币",
    exchange_rate_note="按 1 CNY = 1.1 HKD 换算",
    cfo=ExtractedField(
        value=cnb_to_hkb(cfo_cnb),
        source="FCF(1,826亿)+Capex(792亿)=CFO(2,618亿人民币)",
    ),
    total_capex=ExtractedField(
        value=cnb_to_hkb(total_capex_cnb),
        source="第1页: 资本开支为人民币792亿元，同比增加3%",
    ),
    maintenance_capex=ExtractedField(
        value=cnb_to_hkb(maintenance_capex_cnb),
        source="⚠ 估算值（财报附注(d)未拆分维持性vs扩张性）",
        reason=(
            "财报仅说明Capex主要包括IT基础设施/数据中心/土地/办公园区/知识产权，"
            "未拆分维持性与扩张性。以FY2024折旧摊销~500亿为锚，"
            "保守上浮至550亿人民币作为维持性Capex"
        ),
    ),
    growth_capex=ExtractedField(
        value=cnb_to_hkb(total_capex_cnb - maintenance_capex_cnb),
        source="总Capex 792 - 维持性估算 550 = 扩张性 242 亿人民币（主要为AI基础设施）",
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
        source="第9页: 借款(42,618+208,369) + 应付票据(10,542+126,204) = 387,733百万元",
    ),
    revenue=ExtractedField(
        value=cnb_to_hkb(revenue_cnb),
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
#  Step 3: 构建 FinancialData（含投资组合）并运行完整分析
# ═══════════════════════════════════════════════════════════

# 缺失字段使用保守默认值
committed_inv_hkb = 100.0   # 保守估计已承诺投资 ~100 亿港币
overseas_cash_hkb = 200.0   # 国际游戏+海外云业务，估计海外现金 ~200 亿港币

# 腾讯当前市值约 4.2 万亿港币（2026年4月）
market_cap_hkb = 42000.0

financial_data = FinancialData(
    cfo=cnb_to_hkb(cfo_cnb),
    maintenance_capex=cnb_to_hkb(maintenance_capex_cnb),
    total_capex=cnb_to_hkb(total_capex_cnb),
    cash_and_equivalents=parsed.cash_and_equivalents.value,
    short_term_investments=parsed.short_term_investments.value,
    interest_bearing_debt=parsed.interest_bearing_debt.value,
    committed_investments=committed_inv_hkb,
    restricted_cash=parsed.restricted_cash.value,
    overseas_cash=overseas_cash_hkb,
    revenue=parsed.revenue.value,
    market_cap=market_cap_hkb,
    # 投资组合（新增）
    listed_investments_fv=cnb_to_hkb(listed_inv_fv_cnb),   # 上市投资公允价值
    unlisted_investments_bv=cnb_to_hkb(unlisted_inv_bv_cnb),  # 非上市投资账面价值
    investment_discount=0.50,  # 保守50%折扣
    # 元数据
    period="FY2025",
    ticker="0700.HK",
    maintenance_capex_is_estimated=True,
    maintenance_capex_note=(
        "财报附注(d)仅说明Capex含IT基础设施/数据中心/土地/办公/知识产权，未拆分维持性vs扩张性。"
        "以EBITDA-经营盈利差额推算折旧摊销~692亿人民币为上限，"
        "取FY2024折旧摊销~500亿上浮至550亿人民币作为维持性Capex保守估计"
    ),
)

print(f"\n\n{'═' * 60}")
print("  Step 2-5: 完整 OE 分析报告")
print("═" * 60)\

# OE 计算
oe_result = OECalculator(discount_rate=0.10).calculate(financial_data)

# Combo A 扫描
quarterly_oe_est = [
    round((cnb_to_hkb(cfo_cnb) - cnb_to_hkb(maintenance_capex_cnb)) / 4, 1)
] * 4

combo_a = ComboScanner().scan_combo_a(
    oe_result,
    ComboAInput(
        asset_tier="顶级资产",
        quarterly_oes=quarterly_oe_est,
        oe_multiple_percentile=40.0,
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
