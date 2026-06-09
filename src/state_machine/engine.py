"""状态机引擎（文档第九节工程实现 + 第五节防抖 + 第十节输出）

流程（对应伪代码 Step 1-13）：
  1-4  读取基础权重 → 叠加画像修正 → 裁剪 → 归一化
  5    计算四层得分
  6    检查数据质量（无 A 类触发则无效；数据质量低则置信度降级）
  7    计算状态总分
  8    检查硬门槛
  9    应用防抖（普通状态需连续确认，风险状态可直接覆盖）
  10   应用误判惩罚
  11   输出状态
  12   组合约束覆盖
  13   触发 Decision Log
"""

from dataclasses import dataclass, field

from .states import State, RISK_STATES, STATE_BASE_ACTION, STATE_DESCRIPTIONS
from .market_data import MarketData, Features, compute_features
from .profile import TargetProfile, resolve_weights
from .checkboxes import LayerEvidence, evaluate_layers
from .hard_gates import check_hard_gate, has_a_class_trigger
from .scoring import classify_score, weighted_total


@dataclass
class PortfolioConstraint:
    """组合约束（人工保留项，文档第一节"人工保留：组合约束"）"""

    current_position_pct: float = 0.0   # 当前仓位占组合比例 (0-1)
    max_position_pct: float = 1.0       # 该标的组合上限 (0-1)
    holding_tactical: bool = False      # 是否持有战术仓

    @property
    def limit_exceeded(self) -> bool:
        return self.current_position_pct >= self.max_position_pct


@dataclass
class EngineInput:
    """一次状态评估的完整输入"""

    market_data: MarketData
    profile: TargetProfile
    portfolio: PortfolioConstraint = field(default_factory=PortfolioConstraint)
    previous_state: State | None = None
    candidate_confirmations: int = 2    # 候选状态已连续出现周期数（≥2 视为确认）
    penalties: dict[State, int] = field(default_factory=dict)  # 误判惩罚：状态→阈值加分
    fundamental_redline: bool = False   # 基本面重度红线（风险覆盖）


@dataclass
class StateEvaluation:
    """单个候选状态的评估明细"""

    state: State
    score: float
    weights: dict[str, float]
    layers: dict[str, LayerEvidence]
    gate_passed: bool
    gate_reason: str | None
    valid: bool                          # 通过硬门槛 + A 类 + 达最低分（含惩罚）
    penalty_applied: int = 0


@dataclass
class StateResult:
    """状态机最终输出（文档第十节 7 项 + 透明化明细）"""

    ticker: str
    date: str

    # 1. 当前状态
    state: State | None
    state_desc: str
    # 2. 状态置信度
    score: float
    score_level: str
    confidence_level: str               # 高/中/低（受数据质量与画像待落地降级）
    # 3. 触发证据（四层）
    evidence: dict[str, list[str]]      # layer -> 触发的 checkbox 名称
    layer_scores: dict[str, float]
    weights: dict[str, float]
    # 4. 数据质量
    data_quality: str                   # 高/中/低
    data_quality_note: str
    # 5. 组合约束
    allow_add: bool
    only_reduce: bool
    portfolio_note: str
    # 6. 建议动作
    action: str                         # 短标签
    action_detail: str
    # 7. Decision Log
    log_required: bool
    log_reason: str

    # 透明化 / 防抖 / 惩罚
    raw_state: State | None             # 本周期评分最优的有效状态（防抖前）
    debounce_note: str
    pending_state: State | None
    penalty_note: str
    gate_passed: bool
    gate_reason: str | None
    all_evaluations: list[StateEvaluation] = field(default_factory=list)


class StateEngine:
    """状态机引擎"""

    MIN_VALID_SCORE = 40  # 低于此分视为"未触发"

    def evaluate(self, inp: EngineInput) -> StateResult:
        md = inp.market_data
        f = compute_features(md)

        # ── Step 1-8：逐状态评分 + 硬门槛 ──
        evaluations: list[StateEvaluation] = []
        for state in State:
            weights = resolve_weights(state, inp.profile.tags)
            layers = evaluate_layers(state, f)
            score = weighted_total(layers, weights)
            gate_passed, gate_reason = check_hard_gate(
                state, f, layers, md.intraday_confirmed
            )
            penalty = inp.penalties.get(state, 0)
            min_score = self.MIN_VALID_SCORE + penalty
            valid = gate_passed and has_a_class_trigger(layers) and score >= min_score
            evaluations.append(
                StateEvaluation(
                    state=state,
                    score=score,
                    weights=weights,
                    layers=layers,
                    gate_passed=gate_passed,
                    gate_reason=gate_reason,
                    valid=valid,
                    penalty_applied=penalty,
                )
            )

        # ── Step 9：选状态（风险覆盖 > 普通评分）+ 防抖 ──
        raw_eval = self._select_raw(evaluations, inp.fundamental_redline)
        committed_eval, debounce_note, pending_state = self._apply_debounce(
            raw_eval, inp
        )

        # ── Step 6：数据质量 + 置信度降级 ──
        data_quality, dq_note = self._data_quality(f, md)
        score_level = classify_score(committed_eval.score) if committed_eval else "未触发"
        confidence_level = self._confidence_level(
            committed_eval.score if committed_eval else 0.0,
            data_quality,
            inp.profile,
            pending_state is not None,
        )

        # ── Step 12：组合约束覆盖 + Step 11 输出 ──
        state = committed_eval.state if committed_eval else None
        allow_add, only_reduce, portfolio_note = self._portfolio(state, inp.portfolio)
        action, action_detail = self._map_action(
            state, committed_eval.score if committed_eval else 0.0,
            inp.portfolio, allow_add, only_reduce,
        )

        # ── Step 13：Decision Log ──
        log_required, log_reason = self._log_required(state, action)

        evidence = {}
        layer_scores = {}
        weights_out = {}
        if committed_eval:
            for layer, ev in committed_eval.layers.items():
                evidence[layer] = ev.triggered_names
                layer_scores[layer] = round(ev.score, 1)
            weights_out = {k: round(v, 1) for k, v in committed_eval.weights.items()}

        penalty_note = self._penalty_note(inp, state)

        return StateResult(
            ticker=md.ticker,
            date=f.date,
            state=state,
            state_desc=STATE_DESCRIPTIONS.get(state, "") if state else "无有效状态成立",
            score=round(committed_eval.score, 1) if committed_eval else 0.0,
            score_level=score_level,
            confidence_level=confidence_level,
            evidence=evidence,
            layer_scores=layer_scores,
            weights=weights_out,
            data_quality=data_quality,
            data_quality_note=dq_note,
            allow_add=allow_add,
            only_reduce=only_reduce,
            portfolio_note=portfolio_note,
            action=action,
            action_detail=action_detail,
            log_required=log_required,
            log_reason=log_reason,
            raw_state=raw_eval.state if raw_eval else None,
            debounce_note=debounce_note,
            pending_state=pending_state,
            penalty_note=penalty_note,
            gate_passed=committed_eval.gate_passed if committed_eval else False,
            gate_reason=committed_eval.gate_reason if committed_eval else "无有效状态",
            all_evaluations=evaluations,
        )

    # ── 选状态：风险覆盖优先 ──
    def _select_raw(
        self, evals: list[StateEvaluation], fundamental_redline: bool
    ) -> StateEvaluation | None:
        valid = [e for e in evals if e.valid]
        if not valid:
            return None
        # 风险覆盖：有效风险状态优先（文档第五节防抖优先级）
        risk_valid = [e for e in valid if e.state in RISK_STATES]
        if risk_valid:
            return max(risk_valid, key=lambda e: e.score)
        return max(valid, key=lambda e: e.score)

    # ── 防抖（文档第五节）──
    def _apply_debounce(
        self, raw_eval: StateEvaluation | None, inp: EngineInput
    ) -> tuple[StateEvaluation | None, str, State | None]:
        if raw_eval is None:
            return None, "无有效状态，维持观察", None

        state = raw_eval.state

        # 风险状态：立即覆盖，不等待
        if state in RISK_STATES or inp.fundamental_redline:
            return raw_eval, "风险状态/红线，立即覆盖，不受冷却限制", None

        # 普通状态：需连续 2 周期确认
        if inp.previous_state == state:
            return raw_eval, "与上一周期状态一致，已确认", None
        if inp.candidate_confirmations >= 2:
            return raw_eval, f"普通状态已连续确认 {inp.candidate_confirmations} 周期", None

        # 未达连续确认 → 维持上一状态（若有），标记 pending
        note = (
            f"普通状态需连续确认（当前 {inp.candidate_confirmations}/2），"
            f"暂不切换，{('维持 ' + inp.previous_state.value) if inp.previous_state else '维持观察'}"
        )
        # 维持上一状态时，输出仍以 raw_eval 透明展示，但 committed 状态降级处理：
        # 这里以"维持观察"语义返回 raw_eval 但通过 pending_state 提示待确认
        return raw_eval, note, state

    # ── 数据质量分级（文档第六节）──
    def _data_quality(self, f: Features, md: MarketData) -> tuple[str, str]:
        if f.has_index and f.has_flow:
            return "高", "OHLCV + 指数 + 资金(B类) 齐备"
        if f.has_index:
            return "中", "OHLCV + 指数齐备，缺 B 类资金数据，资金层不参与评分"
        return "低", "仅个股 OHLCV，缺指数/资金数据，置信度自动降一级"

    def _confidence_level(
        self, score: float, data_quality: str, profile: TargetProfile, pending: bool
    ) -> str:
        # 以分数为基线映射 高/中/低
        if score >= 75:
            base = "高"
        elif score >= 60:
            base = "中"
        else:
            base = "低"
        order = ["低", "中", "高"]
        idx = order.index(base)
        # 降级触发项
        if data_quality == "低":
            idx -= 1
        if profile.policy_pending or profile.event_pending:
            idx -= 1
        if pending:
            idx -= 1
        idx = max(0, idx)
        return order[idx]

    # ── 组合约束（Step 12）──
    def _portfolio(
        self, state: State | None, pf: PortfolioConstraint
    ) -> tuple[bool, bool, str]:
        if state in RISK_STATES:
            return False, True, "风险状态：禁止加仓，释放/减战术仓"
        if pf.limit_exceeded:
            return False, True, (
                f"仓位 {pf.current_position_pct:.0%} 已达上限 {pf.max_position_pct:.0%}："
                f"禁止加仓，只能减仓"
            )
        if state in (State.DOWN_ACCEL, State.DOWN_EXHAUST):
            return False, False, "下跌阶段：禁止加仓，观察为主"
        return True, False, f"仓位 {pf.current_position_pct:.0%} / 上限 {pf.max_position_pct:.0%}，允许在约束内加仓"

    # ── 状态 → 建议动作（短标签 + 明细）──
    def _map_action(
        self,
        state: State | None,
        score: float,
        pf: PortfolioConstraint,
        allow_add: bool,
        only_reduce: bool,
    ) -> tuple[str, str]:
        if state is None:
            return "观察", "无有效状态成立，仅观察，不交易"

        detail = STATE_BASE_ACTION[state]

        if state == State.DOWN_ACCEL:
            return ("减战术仓" if pf.holding_tactical else "观察"), detail
        if state == State.DOWN_EXHAUST:
            return "观察", detail
        if state == State.WEAK_REBOUND:
            return "小仓试探", detail + "（极小仓需写 Decision Log，不可升级核心买入）"
        if state == State.VALID_REBOUND:
            if not allow_add:
                return "观察", "有效反弹成立，但组合约束禁止加仓：" + detail
            return ("标准战术仓" if score >= 75 else "小加"), detail
        if state == State.TREND_REPAIR:
            if not allow_add:
                return "观察", "趋势修复成立，但组合约束禁止加仓：" + detail
            return ("标准战术仓" if score >= 75 else "正常加"), detail
        if state == State.UP_EXHAUST:
            return "启动利润保护", detail
        if state == State.DISTRIBUTION:
            return "减战术仓", detail
        if state == State.TREND_BREAK:
            return "清战术仓", detail
        return "观察", detail

    # ── Decision Log 判定（Step 13）──
    def _log_required(self, state: State | None, action: str) -> tuple[bool, str]:
        if state is None:
            return False, "无交易动作"
        if state in RISK_STATES:
            return True, "风险状态触发，必须记录"
        if action != "观察":
            return True, f"触发交易动作「{action}」，必须记录"
        return False, "无交易动作"

    def _penalty_note(self, inp: EngineInput, state: State | None) -> str:
        if state and state in inp.penalties:
            return f"该状态存在误判惩罚：触发阈值 +{inp.penalties[state]} 分，仓位权限降级"
        if inp.penalties:
            return "其他状态存在历史惩罚（不影响当前状态）"
        return "无"
