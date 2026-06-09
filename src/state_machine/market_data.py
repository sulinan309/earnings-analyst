"""行情数据输入与特征计算

对应文档第六节 A/B/C 数据分级：
- A 类（可主触发）：OHLC、成交额/量、换手率、指数、行业指数、汇率、美债等
- B 类（仅辅助）：南向/北向、大单净流入、主动买卖盘比例、资金净流入等
- C 类（仅入 Decision Log）：经纪席位、挂单墙、社媒情绪 —— 本引擎不接收

价位/成交/指数三层均由 A 类数据驱动；资金层为 B 类，缺失时数据质量下降。

关键价位（前低/前高/第一关键位/核心关键位/短线支撑）属"价值锚"，
人工可显式指定；未指定时由近端波段自动估算（代理值，可被人工覆盖）。
"""

from dataclasses import dataclass, field
from statistics import fmean


@dataclass
class Bar:
    """单根 K 线（A 类数据，单位与平台一致，成交额优先于成交量）"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float  # 成交额（亿）或成交量，全程口径需固定


@dataclass
class KeyLevels:
    """关键价位（价值锚）。任意字段留 None 则由历史波段自动估算。"""

    prior_low: float | None = None        # 前低
    prior_high: float | None = None       # 前高
    first_key_level: float | None = None  # 第一关键位（近端阻力/反弹首道关口）
    core_level: float | None = None       # 核心关键位（趋势分水岭）
    short_support: float | None = None     # 短线支撑


@dataclass
class FlowData:
    """资金层辅助数据（B 类）。全部可选，缺失即视为该层数据不可用。

    约定：正值=净流入/改善，负值=净流出/恶化。
    prev_* 为上一周期值，用于判断"扩大/收窄/由负转正"等边际变化。
    """

    net_flow: float | None = None          # 当日资金净流入
    prev_net_flow: float | None = None     # 上一周期资金净流入
    big_order_net: float | None = None     # 大单净流入
    prev_big_order_net: float | None = None
    active_buy_ratio: float | None = None  # 主动买盘占比 0-1
    southbound_net: float | None = None    # 南向/北向净流入
    prev_southbound_net: float | None = None

    @property
    def available(self) -> bool:
        return any(
            v is not None
            for v in (
                self.net_flow,
                self.big_order_net,
                self.active_buy_ratio,
                self.southbound_net,
            )
        )


@dataclass
class MarketData:
    """单个标的的一次状态评估所需的全部行情输入"""

    ticker: str
    bars: list[Bar]                              # 个股 K 线，按时间升序，最后一根为评估日
    index_bars: list[Bar] = field(default_factory=list)     # 本地指数（如恒科）
    industry_bars: list[Bar] = field(default_factory=list)  # 行业指数（可选）
    key_levels: KeyLevels = field(default_factory=KeyLevels)
    flow: FlowData = field(default_factory=FlowData)
    intraday_confirmed: bool = True              # 是否为收盘确认数据（普通买点需 True）

    def __post_init__(self):
        if len(self.bars) < 5:
            raise ValueError("至少需要 5 根 K 线才能计算特征")


# ── 特征计算辅助 ──

def _sma(values: list[float], n: int) -> float:
    window = values[-n:] if len(values) >= n else values
    return fmean(window) if window else 0.0


def _swing_low(bars: list[Bar], exclude_last: int = 1) -> float:
    pool = bars[:-exclude_last] if exclude_last and len(bars) > exclude_last else bars
    return min(b.low for b in pool)


def _swing_high(bars: list[Bar], exclude_last: int = 1) -> float:
    pool = bars[:-exclude_last] if exclude_last and len(bars) > exclude_last else bars
    return max(b.high for b in pool)


def _index_return(bars: list[Bar]) -> float | None:
    if len(bars) < 2:
        return None
    prev = bars[-2].close
    return (bars[-1].close - prev) / prev if prev else None


@dataclass
class Features:
    """从 MarketData 派生的标准化特征（全部布尔/数值，供 checkbox 判定）

    available_* 标记某类数据是否可评估，用于数据质量分级。
    """

    # 元数据
    ticker: str = ""
    date: str = ""
    has_index: bool = False
    has_industry: bool = False
    has_flow: bool = False

    # ── 价位层 ──
    making_new_low: bool = False
    consec_new_lows: int = 0
    breaks_prior_low: bool = False
    below_core_level: bool = False
    holds_core_level: bool = False
    consec_above_core: int = 0
    close_position: float = 0.5          # (close-low)/(high-low)，日内位置
    close_near_low: bool = False         # <=1/3
    close_upper_third: bool = False      # >=2/3
    lower_shadow: bool = False           # 下影线明显
    upper_shadow: bool = False           # 上影线明显（冲高回落）
    higher_low: bool = False             # 低点抬高
    reclaim_first_level: bool = False    # 收复第一关键位
    no_new_low: bool = False
    no_break_prior_low: bool = False
    breaks_prior_high: bool = False      # 突破前高
    fail_break_prior_high: bool = False  # 冲前高失败
    lower_high: bool = False             # 高点不再抬高
    break_short_support: bool = False

    # ── 成交层 ──
    vol_expansion: bool = False          # 放量 >1.3x
    vol_strong_expansion: bool = False   # 显著放量 >1.5x
    vol_contraction: bool = False        # 缩量 <0.8x
    mild_expansion: bool = False         # 温和放量 1.0-1.4x
    up_day: bool = False
    down_day: bool = False
    close_below_open: bool = False
    close_below_vwap: bool = False       # 收盘低于日内均价线（典型价代理）
    close_above_vwap: bool = False
    vol_price_divergence: bool = False   # 量价背离
    healthy_volume: bool = False         # 涨放量/跌缩量

    # ── 指数层 ──
    index_new_low: bool = False
    index_no_new_low: bool = False
    index_down: bool = False
    index_up: bool = False
    index_converging: bool = False       # 跌幅收敛（边际改善）
    index_stabilizing: bool = False      # 企稳
    index_repairing: bool = False        # 同步修复
    index_weakening: bool = False        # 转弱
    industry_weak: bool = False
    industry_repairing: bool = False

    # ── 资金层（B 类）──
    active_sell_up: bool = False         # 主动卖盘增加
    net_outflow_expanding: bool = False
    big_order_outflow: bool = False
    net_inflow_turning_positive: bool = False
    active_buy_recovering: bool = False
    active_buy_increasing: bool = False
    net_inflow_improving: bool = False
    flow_passive_only: bool = False      # 只剩低位被动承接


def compute_features(md: MarketData, vol_lookback: int = 20) -> Features:
    """从 MarketData 计算标准化特征"""

    bars = md.bars
    last = bars[-1]
    prev = bars[-2]
    rng = max(last.high - last.low, 1e-9)
    pos = (last.close - last.low) / rng

    vols = [b.volume for b in bars[:-1]]
    vol_ma = _sma(vols, vol_lookback) if vols else last.volume
    vol_ratio = last.volume / vol_ma if vol_ma else 1.0

    kl = md.key_levels
    prior_low = kl.prior_low if kl.prior_low is not None else _swing_low(bars)
    prior_high = kl.prior_high if kl.prior_high is not None else _swing_high(bars)
    # 代理：第一关键位≈5日均线，核心关键位≈20日均线，短线支撑≈近3日最低
    closes = [b.close for b in bars]
    first_level = kl.first_key_level if kl.first_key_level is not None else _sma(closes, 5)
    core_level = kl.core_level if kl.core_level is not None else _sma(closes, 20)
    short_support = (
        kl.short_support if kl.short_support is not None else min(b.low for b in bars[-3:])
    )

    # 创新低 / 连续创新低
    making_new_low = last.close <= _swing_low(bars, exclude_last=1)
    consec = 0
    for i in range(len(bars) - 1, 0, -1):
        prior = min(b.low for b in bars[:i]) if i > 0 else bars[i].low
        if bars[i].close <= prior:
            consec += 1
        else:
            break

    # 低点抬高：最近 3 根的最低 > 之前 3 根的最低
    higher_low = False
    if len(bars) >= 6:
        recent_low = min(b.low for b in bars[-3:])
        earlier_low = min(b.low for b in bars[-6:-3])
        higher_low = recent_low > earlier_low

    # 日内典型价（VWAP 代理）
    vwap = (last.high + last.low + last.close) / 3
    upper_shadow_ratio = (last.high - max(last.open, last.close)) / rng
    lower_shadow_ratio = (min(last.open, last.close) - last.low) / rng

    up_day = last.close > prev.close
    down_day = last.close < prev.close

    # 核心位连续站稳
    consec_above_core = 0
    for b in reversed(bars):
        if b.close >= core_level:
            consec_above_core += 1
        else:
            break

    f = Features(
        ticker=md.ticker,
        date=last.date,
        has_index=bool(md.index_bars),
        has_industry=bool(md.industry_bars),
        has_flow=md.flow.available,
    )

    # 价位层
    f.making_new_low = making_new_low
    f.consec_new_lows = consec
    f.breaks_prior_low = last.close < prior_low
    f.below_core_level = last.close < core_level
    f.holds_core_level = last.close >= core_level
    f.consec_above_core = consec_above_core
    f.close_position = pos
    f.close_near_low = pos <= 0.33
    f.close_upper_third = pos >= 0.67
    f.lower_shadow = lower_shadow_ratio >= 0.30
    f.upper_shadow = upper_shadow_ratio >= 0.30
    f.higher_low = higher_low
    f.reclaim_first_level = last.close >= first_level
    f.no_new_low = not making_new_low
    f.no_break_prior_low = last.close >= prior_low
    f.breaks_prior_high = last.close > prior_high
    f.fail_break_prior_high = last.high > prior_high and last.close < prior_high
    f.lower_high = last.high < _swing_high(bars, exclude_last=1)
    f.break_short_support = last.close < short_support

    # 成交层
    f.vol_expansion = vol_ratio > 1.30
    f.vol_strong_expansion = vol_ratio > 1.50
    f.vol_contraction = vol_ratio < 0.80
    f.mild_expansion = 1.0 <= vol_ratio <= 1.40
    f.up_day = up_day
    f.down_day = down_day
    f.close_below_open = last.close < last.open
    f.close_below_vwap = last.close < vwap
    f.close_above_vwap = last.close >= vwap
    f.vol_price_divergence = f.vol_expansion and (not up_day or f.upper_shadow)
    f.healthy_volume = (up_day and f.vol_expansion) or (down_day and f.vol_contraction)

    # 指数层
    if md.index_bars:
        idx = md.index_bars
        idx_new_low = idx[-1].close <= _swing_low(idx, exclude_last=1)
        idx_ret = _index_return(idx) or 0.0
        prev_idx_ret = _index_return(idx[:-1]) or 0.0
        idx_sma5 = _sma([b.close for b in idx], 5)
        f.index_new_low = idx_new_low
        f.index_no_new_low = not idx_new_low
        f.index_down = idx_ret < 0
        f.index_up = idx_ret > 0
        # 跌幅收敛：仍跌但跌幅小于上一根
        f.index_converging = idx_ret < 0 and idx_ret > prev_idx_ret
        f.index_stabilizing = idx_ret >= 0 and not idx_new_low
        f.index_repairing = idx_ret > 0 and idx[-1].close >= idx_sma5
        f.index_weakening = idx_ret < 0 and prev_idx_ret >= 0

    if md.industry_bars:
        ind = md.industry_bars
        ind_ret = _index_return(ind) or 0.0
        f.industry_weak = ind_ret < 0
        f.industry_repairing = ind_ret > 0

    # 资金层（B 类）
    fl = md.flow
    if fl.available:
        nf, pnf = fl.net_flow, fl.prev_net_flow
        bo = fl.big_order_net
        sb, psb = fl.southbound_net, fl.prev_southbound_net
        abr = fl.active_buy_ratio

        if nf is not None:
            f.active_sell_up = nf < 0
            f.net_inflow_turning_positive = nf > 0 and (pnf is not None and pnf <= 0)
            f.net_inflow_improving = pnf is not None and nf > pnf
            if pnf is not None:
                f.net_outflow_expanding = nf < 0 and nf < pnf
        if bo is not None:
            f.big_order_outflow = bo < 0
        if abr is not None:
            f.active_buy_increasing = abr > 0.55
            f.active_buy_recovering = abr >= 0.50
            f.flow_passive_only = abr < 0.45
        if sb is not None and psb is not None:
            # 南向改善并入净流入改善信号
            f.net_inflow_improving = f.net_inflow_improving or sb > psb

    return f
