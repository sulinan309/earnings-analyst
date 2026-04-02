"""批量分析 Watchlist 公司 — 从财报 PDF 提取数据并生成报告

数据来源:
- 腾讯 (0700.HK): tencent.pdf FY2025 ✓ 完整提取
- 快手 (1024.HK): kuaishou.pdf FY2025 ✓ 部分提取（无现金流量表，CFO需估算）
- PDD (PDD.US→参考): PDD.pdf FY2025 ✓ 完整提取
- 小米 (1810.HK): Xiaomi.pdf FY2025 ✗ PDF字体编码问题，需Claude API
- 阿里 (9988.HK): alibaba.pdf FY2025 ✗ PDF字体编码问题，需Claude API
"""

from datetime import date

from src.frameworks.oe_calculator import OECalculator, FinancialData, ScenarioResult
from src.signals.combo_scanner import ComboScanner, ComboAInput
from src.frameworks.odds_matrix import OddsMatrix
from src.output.report_generator import ReportInput, ReportGenerator
from src.output.html_report import generate_html


FX = 1.1  # 1 CNY ≈ 1.1 HKD


def cnb(v: float) -> float:
    """人民币亿 → 港币亿"""
    return round(v * FX, 2)


def cnm(v: float) -> float:
    """人民币百万 → 港币亿"""
    return round(v * FX / 100, 2)


# ═══════════════════════════════════════════════════════════
#  5 家公司财务数据
# ═══════════════════════════════════════════════════════════

COMPANIES = {
    # ── 腾讯 FY2025（tencent.pdf 完整提取）──
    "0700.HK": {
        "name": "腾讯",
        "asset_tier": "顶级资产",
        "focus": "投资组合公允价值、回购力度、AI投入ROI",
        "market_cap": 42000.0,
        "data": FinancialData(
            cfo=cnb(2618),               # FCF 1826 + Capex 792
            maintenance_capex=cnb(550),   # 估算：折旧摊销~500亿上浮
            total_capex=cnb(792),
            cash_and_equivalents=cnm(141_041),
            short_term_investments=cnm(236_801 + 70_302),  # 流动+非流动定期存款
            interest_bearing_debt=cnm(42_618 + 10_542 + 208_369 + 126_204),
            committed_investments=100.0,  # 估算
            restricted_cash=cnm(6_977),
            overseas_cash=200.0,          # 估算
            revenue=cnb(7518),
            market_cap=42000.0,
            listed_investments_fv=cnb(6727),
            unlisted_investments_bv=cnb(3631),
            investment_discount=0.50,
            period="FY2025", ticker="0700.HK",
            maintenance_capex_is_estimated=True,
            maintenance_capex_note="附注未拆分，以折旧摊销~500亿人民币上浮至550亿作为保守估计",
        ),
        "quarterly_oes": [cnb(2618 - 550) / 4] * 4,
        "oe_percentile": 40.0,
    },

    # ── 快手 FY2025（kuaishou.pdf 部分提取）──
    # 总收入 1428亿, 经营利润 206亿, 经调整EBITDA 298亿
    # 可利用资金 1049亿
    # 资产负债表：现金111.8亿, 短期存款86.3亿, 长期存款220.2亿
    # 金融资产(流动)423.2亿, 借款(非流动)111.0亿, 借款(流动)19.7亿
    # 折旧摊销: 物业设备39.0亿 + 使用权32.2亿 + 无形0.8亿 = 72.0亿
    # 无现金流量表 → CFO = 经调整EBITDA + 营运资金变动（估算 ~280亿）
    "1024.HK": {
        "name": "快手",
        "asset_tier": "中等质量",
        "focus": "电商GMV变现率、可灵AI商业化、海外投入节奏",
        "market_cap": 2300.0,  # 2026年4月约2300亿港币
        "data": FinancialData(
            cfo=cnb(280),                # 估算：经调整净利润206+折旧72+营运资金~=280亿
            maintenance_capex=cnb(72),   # 折旧摊销作为维持性Capex代理
            total_capex=cnb(120),        # 估算：物业设备大幅增长(148→229亿)
            cash_and_equivalents=cnm(11_180),
            short_term_investments=cnm(8_630 + 22_015 + 42_324),  # 短期存款+长期存款+金融资产
            interest_bearing_debt=cnm(11_098 + 1_968),
            committed_investments=20.0,  # 估算
            restricted_cash=cnm(251),
            overseas_cash=30.0,          # 海外业务较小
            revenue=cnb(1428),
            market_cap=2300.0,
            period="FY2025", ticker="1024.HK",
            maintenance_capex_is_estimated=True,
            maintenance_capex_note="无现金流量表，CFO由EBITDA估算；维持性Capex取折旧摊销72亿人民币",
        ),
        "quarterly_oes": [cnb(280 - 72) / 4] * 4,
        "oe_percentile": 30.0,
    },

    # ── PDD FY2025（PDD.pdf 完整提取，美股上市但参考用）──
    # 总收入 431,846百万, CFO 106,939百万
    # 现金 108,901百万, 短期投资 313,408百万, 受限现金 73,831百万
    # 无借款（零有息负债）
    # Capex极低（轻资产模式）
    "PDD": {
        "name": "拼多多",
        "asset_tier": "中等质量",
        "focus": "Temu海外烧钱节奏、国内电商变现率、监管风险",
        "market_cap": 10000.0,  # 约1万亿港币（美股市值折算）
        "data": FinancialData(
            cfo=cnm(106_939),
            maintenance_capex=cnm(500),    # 极轻资产，Capex极低
            total_capex=cnm(1_000),        # 估算
            cash_and_equivalents=cnm(108_901),
            short_term_investments=cnm(313_408),
            interest_bearing_debt=0.0,     # 零借款
            committed_investments=0.0,
            restricted_cash=cnm(73_831),
            overseas_cash=cnb(300),         # Temu海外大量现金
            revenue=cnm(431_846),
            market_cap=10000.0,
            period="FY2025", ticker="PDD",
            maintenance_capex_is_estimated=True,
            maintenance_capex_note="轻资产平台模式，Capex极低，取5亿人民币保守估计",
        ),
        "quarterly_oes": [cnm(106_939 - 500) / 4] * 4,
        "oe_percentile": 35.0,
    },

    # ── 小米 FY2025（PDF字体损坏，数据来自联网搜索公开信息）──
    # 总收入 4573亿, 经调整净利润 392亿, 现金储备 2326亿
    # Q4经营现金流仅6亿（异常低），全年CFO券商预估~676亿
    # 借款总额 ~306亿(2024末), 研发投入 331亿
    "1810.HK": {
        "name": "小米",
        "asset_tier": "中等质量",
        "focus": "汽车业务Capex对OE的侵蚀、IoT生态变现",
        "market_cap": 9000.0,  # 约9000亿港币
        "data": FinancialData(
            cfo=cnb(676),                 # 券商预估全年CFO ~676亿
            maintenance_capex=cnb(150),   # 手机/IoT存量业务维护（不含汽车扩张）
            total_capex=cnb(400),         # 汽车工厂+AI投入
            cash_and_equivalents=cnb(800),  # 现金储备2326亿中的现金部分
            short_term_investments=cnb(1200),  # 定期存款+理财
            interest_bearing_debt=cnb(350),  # 借款~306亿(2024) + 增长
            committed_investments=cnb(100),
            restricted_cash=cnb(30),
            overseas_cash=cnb(150),
            revenue=cnb(4573),
            market_cap=9000.0,
            period="FY2025", ticker="1810.HK",
            maintenance_capex_is_estimated=True,
            maintenance_capex_note="PDF字体损坏，CFO取券商预估676亿；维持性Capex取手机/IoT存量维护~150亿",
        ),
        "quarterly_oes": [cnb(676 - 150) / 4] * 4,
        "oe_percentile": 50.0,
    },

    # ── 阿里 FY2026前三季度（2025.4-12）+ 2025财年数据 ──
    # FY2026前三季度: CFO累计668亿, Capex累计~948亿, 现金5602亿
    # FY2025全年: 收入9963亿
    # 有息负债: 银行借款899亿 + 优先票据1208亿 = 2107亿
    # 年化CFO: 668/9*12 ≈ 890亿
    "9988.HK": {
        "name": "阿里",
        "asset_tier": "中等质量",
        "focus": "云业务利润率拐点、资产剥离进度、AI+即时零售投入",
        "market_cap": 8500.0,
        "data": FinancialData(
            cfo=cnb(890),                # 年化: 前三季度668/9*12
            maintenance_capex=cnb(350),  # 存量电商/云维护（Capex年化~1264亿中大部分是AI扩张）
            total_capex=cnb(1264),       # 年化: 948/9*12
            cash_and_equivalents=cnb(2000),  # 现金5602亿中的现金部分
            short_term_investments=cnb(3000),  # 短期投资+定期存款
            interest_bearing_debt=cnb(2107),  # 借款899+票据1208
            committed_investments=cnb(200),
            restricted_cash=cnb(50),
            overseas_cash=cnb(800),       # 国际业务+Lazada大量海外现金
            revenue=cnb(9963),            # FY2025全年收入
            market_cap=8500.0,
            listed_investments_fv=cnb(800),  # 持有的上市公司股权（大幅减持后）
            unlisted_investments_bv=cnb(300),
            investment_discount=0.50,
            period="FY2026E(年化)", ticker="9988.HK",
            maintenance_capex_is_estimated=True,
            maintenance_capex_note="年化Capex~1264亿中大部分为AI+云扩张；维持性取存量业务维护~350亿",
        ),
        "quarterly_oes": [cnb(890 - 350) / 4] * 4,
        "oe_percentile": 25.0,
    },
}


# ═══════════════════════════════════════════════════════════
#  批量分析
# ═══════════════════════════════════════════════════════════

print("=" * 80)
print("  Watchlist 批量分析 · 基于李录 Owner's Earnings 框架")
print("=" * 80)

all_results = []

for ticker, co in COMPANIES.items():
    fd = co["data"]
    oe = OECalculator(discount_rate=0.10).calculate(fd)
    combo_a = ComboScanner().scan_combo_a(oe, ComboAInput(
        asset_tier=co["asset_tier"],
        quarterly_oes=co["quarterly_oes"],
        oe_multiple_percentile=co["oe_percentile"],
        structural_deterioration=False,
    ))
    mx = OddsMatrix().evaluate(combo_a, oe.odds, co["asset_tier"])
    scenarios = OECalculator(discount_rate=0.10).scenario_analysis(fd)

    all_results.append({
        "name": co["name"], "ticker": ticker, "tier": co["asset_tier"],
        "oe": oe, "combo_a": combo_a, "mx": mx, "scenarios": scenarios,
        "fd": fd, "focus": co["focus"],
    })

    # 生成 HTML 报告
    inp = ReportInput(
        company_name=co["name"], ticker=ticker, asset_tier=co["asset_tier"],
        focus=co["focus"], financial_data=fd, oe_result=oe,
        combo_a=combo_a, matrix_result=mx, report_date=date.today(),
    )
    html = generate_html(inp)
    safe = ticker.replace(".", "_")
    path = f"data/{safe}_report.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


# ═══════════════════════════════════════════════════════════
#  汇总表
# ═══════════════════════════════════════════════════════════

print(f"\n{'─'*96}")
print(f"{'公司':<6} {'代码':<10} {'OE(亿)':>8} {'内在价值':>10} {'市值':>10} {'边际':>8} {'ComboA':>8} {'决策':>8}")
print(f"{'─'*96}")

for r in all_results:
    oe = r["oe"]
    print(
        f"{r['name']:<6} {r['ticker']:<10} {oe.oe:>8.0f} {oe.intrinsic_value:>10.0f}"
        f" {oe.market_cap:>10.0f} {oe.safety_margin_pct:>+8.1f}%"
        f" {r['combo_a'].triggered_count}/4{'✓' if r['combo_a'].triggered else ' '}"
        f"  {r['mx'].action:>6}"
    )

print(f"{'─'*96}")

# ═══════════════════════════════════════════════════════════
#  三情景对比
# ═══════════════════════════════════════════════════════════

print(f"\n\n{'='*96}")
print(f"  三情景估值对比（亿港币）")
print(f"{'='*96}")
print(f"{'公司':<6} {'市值':>10} │ {'保守估值':>10} {'保守边际':>8} │ {'中性估值':>10} {'中性边际':>8} │ {'乐观估值':>10} {'乐观边际':>8}")
print(f"{'─'*96}")

for r in all_results:
    s = r["scenarios"]
    mc = r["oe"].market_cap
    print(
        f"{r['name']:<6} {mc:>10.0f}"
        f" │ {s[0].intrinsic_value:>10.0f} {s[0].safety_margin_pct:>+8.1f}%"
        f" │ {s[1].intrinsic_value:>10.0f} {s[1].safety_margin_pct:>+8.1f}%"
        f" │ {s[2].intrinsic_value:>10.0f} {s[2].safety_margin_pct:>+8.1f}%"
    )

print(f"{'─'*96}")
print(f"\n保守: r=12%, 零增长, Capex×1.2, 储备2月, 投资组合70%折扣")
print(f"中性: r=10%, 零增长, 当前OE, 保守净现金, 投资组合50%折扣")
print(f"乐观: r=8%, g=5%, Capex×0.9, 完整净现金, 投资组合30%折扣")

# 数据质量说明
print(f"\n\n数据质量:")
print(f"  ✓ 腾讯: tencent.pdf 完整提取")
print(f"  △ 快手: kuaishou.pdf 部分提取（无现金流量表，CFO由EBITDA估算）")
print(f"  △ 拼多多: PDD.pdf 完整提取（美股，仅供参考）")
print(f"  △ 小米: Xiaomi.pdf 字体损坏，数据来自联网搜索公开信息")
print(f"  △ 阿里: alibaba.pdf 字体损坏，数据来自联网搜索（FY2026前三季度年化）")

print(f"\nHTML 报告已保存至 data/ 目录")
