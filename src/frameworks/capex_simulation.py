"""CapEx 冲击模拟 — 程序化推演 FY2026 不同情景下 CFO→OE→FCF

无需 AI，纯数学计算。
"""

from dataclasses import dataclass


@dataclass
class CapexScenario:
    label: str           # "FY2025 实际" / "FY2026 基准" / "FY2026 悲观"
    cfo: float
    total_capex: float
    maintenance_capex: float
    oe: float            # CFO - maintenance
    fcf: float           # CFO - total_capex


def simulate_capex(
    fy_cfo: float,
    fy_total_capex: float,
    fy_maintenance_capex: float,
    cfo_growth: float = 0.05,        # 基准 CFO 增速
    capex_growth_base: float = 0.0,  # 基准 Capex 增速
    capex_growth_bear: float = 0.30, # 悲观 Capex 增速
    maint_ratio: float = 0.0,       # 如果>0, 按此比例算维持性
) -> list[CapexScenario]:
    """从当年实际数据推演下一年的 CFO→OE→FCF"""

    actual_oe = fy_cfo - fy_maintenance_capex
    actual_fcf = fy_cfo - fy_total_capex

    # 基准: CFO 温和增长, Capex 持平或小幅增长
    base_cfo = fy_cfo * (1 + cfo_growth)
    base_capex = fy_total_capex * (1 + capex_growth_base)
    base_maint = fy_maintenance_capex * 1.05  # 维持性小幅增长
    base_oe = base_cfo - base_maint
    base_fcf = base_cfo - base_capex

    # 悲观: CFO 不增长, Capex 大幅增长
    bear_cfo = fy_cfo
    bear_capex = fy_total_capex * (1 + capex_growth_bear)
    bear_maint = fy_maintenance_capex * 1.10
    bear_oe = bear_cfo - bear_maint
    bear_fcf = bear_cfo - bear_capex

    return [
        CapexScenario("FY2025 实际", round(fy_cfo, 1), round(fy_total_capex, 1),
                      round(fy_maintenance_capex, 1), round(actual_oe, 1), round(actual_fcf, 1)),
        CapexScenario("FY2026 基准", round(base_cfo, 1), round(base_capex, 1),
                      round(base_maint, 1), round(base_oe, 1), round(base_fcf, 1)),
        CapexScenario("FY2026 悲观", round(bear_cfo, 1), round(bear_capex, 1),
                      round(bear_maint, 1), round(bear_oe, 1), round(bear_fcf, 1)),
    ]
