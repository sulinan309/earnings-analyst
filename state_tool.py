"""个股状态识别工具 - 命令行入口（量化状态机 v2.0 Phase 1）

用法：
    python state_tool.py                      # 内置腾讯示例（有效反弹场景）
    python state_tool.py --demo distribution  # 放量派发示例
    python state_tool.py --csv data.csv --ticker 0700.HK --tags 港股科技 高流动性大盘

CSV 格式（升序，最后一行为评估日）：
    date,open,high,low,close,volume
可选附带指数列：index_open,index_high,index_low,index_close,index_volume

输出为文档第十节标准模板。本工具只识别状态，不替代价值锚、基本面与最终决策。
"""

import argparse
import csv
from datetime import date

from src.state_machine import (
    Bar, MarketData, KeyLevels, FlowData,
    TargetProfile, StateEngine, EngineInput, PortfolioConstraint,
    State, format_report,
)
from src.state_machine.report import format_candidates


# ── 内置示例数据 ──

def _demo_valid_rebound() -> tuple[MarketData, TargetProfile, PortfolioConstraint]:
    """腾讯式有效反弹：缩量止跌后放量上攻、收复关键位、指数同步企稳"""
    bars = [
        Bar("D-09", 320, 322, 312, 314, 95),
        Bar("D-08", 314, 316, 305, 307, 130),   # 放量下跌
        Bar("D-07", 307, 309, 298, 300, 145),   # 创新低放量
        Bar("D-06", 300, 303, 295, 297, 120),   # 续创新低
        Bar("D-05", 297, 301, 296, 299, 70),     # 缩量止跌
        Bar("D-04", 299, 304, 297, 302, 75),     # 缩量企稳，下影线
        Bar("D-03", 302, 308, 301, 307, 80),     # 低点抬高
        Bar("D-02", 307, 312, 305, 310, 95),     # 温和回升
        Bar("D-01", 310, 314, 308, 312, 105),
        Bar("D-00", 312, 326, 311, 324, 165),    # 放量上攻，收上影偏上、收复关键位
    ]
    index = [
        Bar("D-09", 4200, 4220, 4150, 4160, 0),
        Bar("D-08", 4160, 4170, 4080, 4090, 0),
        Bar("D-07", 4090, 4100, 4010, 4020, 0),
        Bar("D-06", 4020, 4040, 3990, 4005, 0),
        Bar("D-05", 4005, 4030, 3995, 4015, 0),
        Bar("D-04", 4015, 4050, 4010, 4040, 0),
        Bar("D-03", 4040, 4080, 4035, 4070, 0),
        Bar("D-02", 4070, 4110, 4060, 4100, 0),
        Bar("D-01", 4100, 4140, 4090, 4130, 0),
        Bar("D-00", 4130, 4200, 4125, 4190, 0),  # 指数同步修复
    ]
    flow = FlowData(
        net_flow=8.0, prev_net_flow=-3.0,
        big_order_net=5.0, prev_big_order_net=-2.0,
        active_buy_ratio=0.58,
        southbound_net=12.0, prev_southbound_net=4.0,
    )
    md = MarketData(
        ticker="0700.HK", bars=bars, index_bars=index, flow=flow,
        key_levels=KeyLevels(prior_low=295, prior_high=322, first_key_level=308, core_level=315),
    )
    profile = TargetProfile(
        name="腾讯", ticker="0700.HK",
        tags=["港股科技", "高流动性大盘"], asset_tier="顶级资产",
    )
    pf = PortfolioConstraint(current_position_pct=0.05, max_position_pct=0.15, holding_tactical=False)
    return md, profile, pf


def _demo_distribution() -> tuple[MarketData, TargetProfile, PortfolioConstraint]:
    """放量派发：高位显著放量、收盘低于开盘与均价线、冲高回落"""
    bars = [
        Bar("D-09", 300, 305, 298, 304, 80),
        Bar("D-08", 304, 312, 303, 310, 95),
        Bar("D-07", 310, 320, 309, 318, 110),
        Bar("D-06", 318, 330, 316, 328, 125),
        Bar("D-05", 328, 340, 326, 338, 140),
        Bar("D-04", 338, 348, 336, 346, 150),
        Bar("D-03", 346, 352, 344, 350, 130),
        Bar("D-02", 350, 356, 347, 352, 120),
        Bar("D-01", 352, 358, 349, 351, 135),    # 滞涨
        Bar("D-00", 351, 360, 340, 343, 240),    # 显著放量冲高回落、收盘低于开盘/均价线
    ]
    index = [
        Bar("D-09", 4100, 4120, 4090, 4115, 0),
        Bar("D-08", 4115, 4140, 4110, 4135, 0),
        Bar("D-07", 4135, 4160, 4130, 4155, 0),
        Bar("D-06", 4155, 4180, 4150, 4175, 0),
        Bar("D-05", 4175, 4200, 4170, 4195, 0),
        Bar("D-04", 4195, 4210, 4190, 4205, 0),
        Bar("D-03", 4205, 4215, 4198, 4208, 0),
        Bar("D-02", 4208, 4218, 4200, 4206, 0),
        Bar("D-01", 4206, 4212, 4190, 4195, 0),
        Bar("D-00", 4195, 4200, 4150, 4160, 0),  # 指数同步走弱
    ]
    flow = FlowData(
        net_flow=-15.0, prev_net_flow=5.0,
        big_order_net=-12.0, prev_big_order_net=3.0,
        active_buy_ratio=0.40,
    )
    md = MarketData(
        ticker="0700.HK", bars=bars, index_bars=index, flow=flow,
        key_levels=KeyLevels(prior_low=326, prior_high=358, first_key_level=348, core_level=345, short_support=347),
    )
    profile = TargetProfile(
        name="腾讯", ticker="0700.HK",
        tags=["港股科技", "高流动性大盘"], asset_tier="顶级资产",
    )
    pf = PortfolioConstraint(current_position_pct=0.12, max_position_pct=0.15, holding_tactical=True)
    return md, profile, pf


DEMOS = {
    "valid_rebound": _demo_valid_rebound,
    "distribution": _demo_distribution,
}


def load_csv(path: str, ticker: str) -> MarketData:
    bars: list[Bar] = []
    index_bars: list[Bar] = []
    with open(path, newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        has_index = reader.fieldnames and "index_close" in reader.fieldnames
        for row in reader:
            bars.append(Bar(
                date=row["date"],
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
                volume=float(row["volume"]),
            ))
            if has_index:
                index_bars.append(Bar(
                    date=row["date"],
                    open=float(row["index_open"]), high=float(row["index_high"]),
                    low=float(row["index_low"]), close=float(row["index_close"]),
                    volume=float(row.get("index_volume", 0) or 0),
                ))
    return MarketData(ticker=ticker, bars=bars, index_bars=index_bars)


def main():
    ap = argparse.ArgumentParser(description="个股状态识别工具（量化状态机 v2.0）")
    ap.add_argument("--demo", choices=list(DEMOS), default="valid_rebound",
                    help="使用内置示例数据")
    ap.add_argument("--csv", help="从 CSV 读取行情（覆盖 --demo）")
    ap.add_argument("--ticker", default="0700.HK")
    ap.add_argument("--tags", nargs="*", default=["港股科技", "高流动性大盘"],
                    help="标的画像标签")
    ap.add_argument("--prev-state", help="上一周期状态（用于普通状态防抖）")
    ap.add_argument("--confirmations", type=int, default=2,
                    help="候选状态已连续出现周期数（≥2 视为确认）")
    ap.add_argument("--show-candidates", action="store_true", help="展示全部候选状态评分")
    args = ap.parse_args()

    if args.csv:
        md = load_csv(args.csv, args.ticker)
        profile = TargetProfile(name=args.ticker, ticker=args.ticker, tags=args.tags)
        pf = PortfolioConstraint()
    else:
        md, profile, pf = DEMOS[args.demo]()

    prev = State(args.prev_state) if args.prev_state else None
    inp = EngineInput(
        market_data=md, profile=profile, portfolio=pf,
        previous_state=prev, candidate_confirmations=args.confirmations,
    )

    result = StateEngine().evaluate(inp)
    # 替换占位日期
    if result.date.startswith("D-"):
        result.date = f"{date.today().isoformat()}（示例，{result.date}）"

    print(format_report(result))
    if args.show_candidates:
        print()
        print(format_candidates(result))


if __name__ == "__main__":
    main()
