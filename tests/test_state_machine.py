"""状态机引擎测试

覆盖：
- 权重映射（文档第七节腾讯/小盘事件股示例）
- 分数分级
- 有效反弹 / 放量派发 端到端识别
- 硬门槛拦截（高总分不能绕过硬门槛）
- 风险状态立即覆盖（防抖优先级）
- 数据质量分级与置信度降级
- A 类触发硬门槛
"""

import pytest

from src.state_machine import (
    Bar, MarketData, KeyLevels, FlowData,
    TargetProfile, StateEngine, EngineInput, PortfolioConstraint,
    State, resolve_weights,
)
from src.state_machine.scoring import classify_score
from src.state_machine.profile import LAYER_MIN, LAYER_MAX


# ── 权重映射 ──

class TestWeights:
    def test_tencent_valid_rebound(self):
        """文档第七节示例：腾讯有效反弹 → 价35/指35/成15/资15"""
        w = resolve_weights(State.VALID_REBOUND, ["港股科技", "高流动性大盘"])
        assert round(w["price"]) == 35
        assert round(w["index"]) == 35
        assert round(w["volume"]) == 15
        assert round(w["flow"]) == 15
        assert abs(sum(w.values()) - 100) < 1e-6

    def test_smallcap_event_floor_respected(self):
        """文档第七节示例：小盘事件股，资金层贴近 10% 下限且不破"""
        w = resolve_weights(State.VALID_REBOUND, ["小盘高波动", "强事件驱动"])
        assert w["flow"] >= LAYER_MIN - 0.1
        assert w["price"] > w["index"] > w["volume"] > w["flow"]
        assert abs(sum(w.values()) - 100) < 1e-6

    def test_bounds_always_respected(self):
        for state in State:
            for tags in ([], ["港股科技"], ["小盘高波动", "强事件驱动"], ["周期商品"]):
                w = resolve_weights(state, tags)
                for layer in ("price", "volume", "index", "flow"):
                    assert LAYER_MIN - 0.1 <= w[layer] <= LAYER_MAX + 0.1
                assert abs(sum(w.values()) - 100) < 1e-3

    def test_unknown_tag_rejected(self):
        with pytest.raises(ValueError):
            TargetProfile(name="x", ticker="x", tags=["不存在的画像"])


# ── 分数分级 ──

class TestClassify:
    @pytest.mark.parametrize("score,level", [
        (10, "未触发"), (45, "观察"), (68, "弱确认"), (80, "有效确认"), (90, "强确认"),
    ])
    def test_levels(self, score, level):
        assert classify_score(score) == level


# ── 端到端场景 ──

def _valid_rebound_md():
    bars = [
        Bar("D-09", 320, 322, 312, 314, 95),
        Bar("D-08", 314, 316, 305, 307, 130),
        Bar("D-07", 307, 309, 298, 300, 145),
        Bar("D-06", 300, 303, 295, 297, 120),
        Bar("D-05", 297, 301, 296, 299, 70),
        Bar("D-04", 299, 304, 297, 302, 75),
        Bar("D-03", 302, 308, 301, 307, 80),
        Bar("D-02", 307, 312, 305, 310, 95),
        Bar("D-01", 310, 314, 308, 312, 105),
        Bar("D-00", 312, 326, 311, 324, 165),
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
        Bar("D-00", 4130, 4200, 4125, 4190, 0),
    ]
    flow = FlowData(net_flow=8.0, prev_net_flow=-3.0, big_order_net=5.0,
                    prev_big_order_net=-2.0, active_buy_ratio=0.58,
                    southbound_net=12.0, prev_southbound_net=4.0)
    return MarketData(
        ticker="0700.HK", bars=bars, index_bars=index, flow=flow,
        key_levels=KeyLevels(prior_low=295, prior_high=322, first_key_level=308, core_level=315),
    )


def _distribution_md():
    bars = [
        Bar("D-09", 300, 305, 298, 304, 80),
        Bar("D-08", 304, 312, 303, 310, 95),
        Bar("D-07", 310, 320, 309, 318, 110),
        Bar("D-06", 318, 330, 316, 328, 125),
        Bar("D-05", 328, 340, 326, 338, 140),
        Bar("D-04", 338, 348, 336, 346, 150),
        Bar("D-03", 346, 352, 344, 350, 130),
        Bar("D-02", 350, 356, 347, 352, 120),
        Bar("D-01", 352, 358, 349, 351, 135),
        Bar("D-00", 351, 360, 340, 343, 240),
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
        Bar("D-00", 4195, 4200, 4150, 4160, 0),
    ]
    flow = FlowData(net_flow=-15.0, prev_net_flow=5.0, big_order_net=-12.0,
                    prev_big_order_net=3.0, active_buy_ratio=0.40)
    return MarketData(
        ticker="0700.HK", bars=bars, index_bars=index, flow=flow,
        key_levels=KeyLevels(prior_low=326, prior_high=358, first_key_level=348,
                             core_level=345, short_support=347),
    )


@pytest.fixture
def engine():
    return StateEngine()


@pytest.fixture
def tencent_profile():
    return TargetProfile(name="腾讯", ticker="0700.HK",
                         tags=["港股科技", "高流动性大盘"], asset_tier="顶级资产")


class TestValidRebound:
    def test_identifies_valid_rebound(self, engine, tencent_profile):
        inp = EngineInput(market_data=_valid_rebound_md(), profile=tencent_profile,
                          portfolio=PortfolioConstraint(0.05, 0.15))
        r = engine.evaluate(inp)
        assert r.state == State.VALID_REBOUND
        assert r.score >= 75
        assert r.gate_passed
        assert r.action in ("标准战术仓", "小加")
        assert r.log_required

    def test_trend_repair_blocked_by_hard_gate(self, engine, tencent_profile):
        """趋势修复总分不低，但未连续站稳核心位 → 硬门槛拦截，不应被选中"""
        inp = EngineInput(market_data=_valid_rebound_md(), profile=tencent_profile)
        r = engine.evaluate(inp)
        repair = next(e for e in r.all_evaluations if e.state == State.TREND_REPAIR)
        assert not repair.valid
        assert "核心" in (repair.gate_reason or "") or "趋势修复" in (repair.gate_reason or "")

    def test_portfolio_limit_blocks_add(self, engine, tencent_profile):
        """仓位已达上限 → 禁止加仓，动作降级为观察"""
        inp = EngineInput(market_data=_valid_rebound_md(), profile=tencent_profile,
                          portfolio=PortfolioConstraint(0.15, 0.15))
        r = engine.evaluate(inp)
        assert r.state == State.VALID_REBOUND
        assert not r.allow_add
        assert r.only_reduce
        assert r.action == "观察"


class TestDistribution:
    def test_identifies_distribution(self, engine, tencent_profile):
        inp = EngineInput(market_data=_distribution_md(), profile=tencent_profile,
                          portfolio=PortfolioConstraint(0.12, 0.15, holding_tactical=True))
        r = engine.evaluate(inp)
        assert r.state == State.DISTRIBUTION
        assert r.action == "减战术仓"
        assert not r.allow_add and r.only_reduce
        assert r.log_required

    def test_risk_override_immediate(self, engine, tencent_profile):
        """放量派发为风险状态，立即覆盖，不等待防抖"""
        inp = EngineInput(market_data=_distribution_md(), profile=tencent_profile,
                          previous_state=State.TREND_REPAIR, candidate_confirmations=0)
        r = engine.evaluate(inp)
        assert r.state == State.DISTRIBUTION
        assert "立即覆盖" in r.debounce_note
        assert r.pending_state is None


class TestDataQuality:
    def test_no_index_downgrades(self, engine, tencent_profile):
        """缺指数数据 → 数据质量为低，置信度降级"""
        md = _valid_rebound_md()
        md.index_bars = []
        md.flow = FlowData()
        inp = EngineInput(market_data=md, profile=tencent_profile)
        r = engine.evaluate(inp)
        assert r.data_quality == "低"

    def test_no_flow_is_mid(self, engine, tencent_profile):
        md = _valid_rebound_md()
        md.flow = FlowData()
        inp = EngineInput(market_data=md, profile=tencent_profile)
        r = engine.evaluate(inp)
        assert r.data_quality == "中"


class TestDebounce:
    def test_normal_state_needs_confirmation(self, engine, tencent_profile):
        """普通状态首次出现且未连续确认 → 标记 pending，置信度降级"""
        inp = EngineInput(market_data=_valid_rebound_md(), profile=tencent_profile,
                          previous_state=None, candidate_confirmations=1)
        r = engine.evaluate(inp)
        assert r.pending_state == State.VALID_REBOUND
        assert "需连续确认" in r.debounce_note


class TestHardGate:
    def test_min_bars_enforced(self):
        with pytest.raises(ValueError):
            MarketData(ticker="x", bars=[Bar("d", 1, 1, 1, 1, 1)])
