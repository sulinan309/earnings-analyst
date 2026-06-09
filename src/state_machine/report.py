"""标准输出格式（文档第十节标准输出模板）"""

from .engine import StateResult

_LAYER_CN = {"price": "价位层", "volume": "成交层", "index": "指数层", "flow": "资金层"}


def format_report(r: StateResult) -> str:
    lines: list[str] = []
    sep = "─" * 44

    lines.append("=" * 44)
    lines.append(f"个股状态识别  {r.ticker}")
    lines.append("=" * 44)
    lines.append(f"日期：{r.date}")
    lines.append(f"当前状态：{r.state.value if r.state else '无有效状态'}")
    lines.append(f"状态分数：{r.score:.1f}")
    lines.append(f"状态等级：{r.score_level}")
    lines.append(f"置信度：{r.confidence_level}")
    lines.append(f"数据质量：{r.data_quality}（{r.data_quality_note}）")
    if r.state:
        lines.append(f"状态含义：{r.state_desc}")
    lines.append(sep)

    # 四层得分 / 权重
    if r.layer_scores:
        scores = "  ".join(
            f"{_LAYER_CN[k]} {r.layer_scores.get(k, 0):.0f}" for k in ("price", "volume", "index", "flow")
        )
        weights = "  ".join(
            f"{_LAYER_CN[k]} {r.weights.get(k, 0):.0f}%" for k in ("price", "volume", "index", "flow")
        )
        lines.append(f"四层得分：{scores}")
        lines.append(f"当前权重：{weights}")
        lines.append(sep)

    # 触发证据
    lines.append("主要触发证据：")
    if r.evidence:
        for k in ("price", "volume", "index", "flow"):
            names = r.evidence.get(k, [])
            text = "、".join(names) if names else "（无）"
            lines.append(f"  □ {_LAYER_CN[k]}：{text}")
    else:
        lines.append("  （无有效状态，无触发证据）")
    lines.append(sep)

    # 硬门槛
    lines.append(f"硬门槛：{'通过' if r.gate_passed else '未通过'}" +
                 (f"（{r.gate_reason}）" if r.gate_reason and not r.gate_passed else ""))
    # 防抖
    lines.append(f"防抖状态：{r.debounce_note}")
    if r.pending_state:
        lines.append(f"  待确认状态：{r.pending_state.value}")
    # 误判惩罚
    lines.append(f"误判惩罚：{r.penalty_note}")
    lines.append(sep)

    # 组合约束
    lines.append("组合约束：")
    lines.append(f"  □ 是否允许加仓：{'是' if r.allow_add else '否'}")
    lines.append(f"  □ 是否只能减仓：{'是' if r.only_reduce else '否'}")
    lines.append(f"  □ 说明：{r.portfolio_note}")
    lines.append(sep)

    # 建议动作
    lines.append(f"建议动作：{r.action}")
    lines.append(f"  □ 明细：{r.action_detail}")
    lines.append(sep)

    # Decision Log
    lines.append(f"Decision Log：{'必须记录' if r.log_required else '否'}（{r.log_reason}）")
    lines.append("=" * 44)

    return "\n".join(lines)


def format_candidates(r: StateResult, top: int = 8) -> str:
    """调试用：展示全部候选状态的评分与有效性"""
    lines = ["候选状态评分（防抖前）："]
    ranked = sorted(r.all_evaluations, key=lambda e: e.score, reverse=True)[:top]
    for e in ranked:
        flag = "✅有效" if e.valid else "❌无效"
        reason = "" if e.valid else f" [{e.gate_reason or '分数不足/无A类触发'}]"
        lines.append(f"  {e.state.value:<6} {e.score:5.1f} {flag}{reason}")
    return "\n".join(lines)
