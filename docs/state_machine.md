# 个股状态识别工具（量化状态机 v2.0）

基于《量化状态机设计 v2.0》业务文档的 Phase 1 实现。系统**不输出"买/卖"信号**，
而是稳定识别个股当前所处的 8 个状态之一，并给出置信度、触发证据、数据质量、
组合约束、建议动作与是否需要写 Decision Log。

> 量化负责"稳定识别状态"，人工保留价值锚、基本面判断、组合约束与最终决策。

## 快速使用

```bash
# 内置示例：有效反弹
python state_tool.py --demo valid_rebound --show-candidates

# 内置示例：放量派发（风险状态立即覆盖）
python state_tool.py --demo distribution

# 从 CSV 读取真实行情
python state_tool.py --csv data.csv --ticker 0700.HK --tags 港股科技 高流动性大盘
```

CSV 列：`date,open,high,low,close,volume`，可选附带指数列
`index_open,index_high,index_low,index_close,index_volume`（升序，末行为评估日）。

## 编程接口

```python
from src.state_machine import (
    Bar, MarketData, KeyLevels, FlowData,
    TargetProfile, StateEngine, EngineInput, PortfolioConstraint, format_report,
)

md = MarketData(
    ticker="0700.HK",
    bars=[Bar("2026-06-09", 312, 326, 311, 324, 165), ...],   # ≥5 根，升序
    index_bars=[...],                                          # 本地指数（恒科等）
    flow=FlowData(net_flow=8.0, prev_net_flow=-3.0, ...),     # B 类，可选
    key_levels=KeyLevels(prior_low=295, core_level=315),      # 价值锚，可选
)
profile = TargetProfile(name="腾讯", ticker="0700.HK",
                        tags=["港股科技", "高流动性大盘"], asset_tier="顶级资产")

result = StateEngine().evaluate(EngineInput(
    market_data=md, profile=profile,
    portfolio=PortfolioConstraint(current_position_pct=0.05, max_position_pct=0.15),
))
print(format_report(result))
```

## 架构

| 模块 | 职责 | 文档对应 |
|------|------|---------|
| `states.py` | 8 个状态定义、基础权重、风险/普通分类、动作映射 | 第二节 |
| `market_data.py` | 行情输入 + OHLCV/指数/资金特征计算（A/B 类数据） | 第六节 |
| `checkboxes.py` | 各状态四层 checkbox 判定 → 层得分 | 第二、三节 |
| `profile.py` | 标的画像 + 权重映射（基础权重+修正→裁剪→归一化） | 第七节 |
| `hard_gates.py` | 硬门槛（状态是否有资格成立） | 第四节 |
| `scoring.py` | 加权总分 + 分级 | 第三节 |
| `engine.py` | 编排（选状态/防抖/组合约束/Decision Log） | 第五、九节 |
| `report.py` | 标准输出模板 | 第十节 |

## 核心机制

- **四层加权评分**：状态分数 = Σ(层得分 × 层权重)，层得分 = checkbox 满足比例 × 100。
- **权重 = 状态类型 + 标的画像**：基础权重叠加画像修正项，裁剪到 10%–45% 并归一化。
- **硬门槛优先于总分**：核心层 < 60 或专属结构条件不满足时，再高总分也无效。
- **A/B/C 数据分级**：价位/成交/指数为 A 类（可主触发），资金为 B 类（仅加减分），
  C 类不进入评分；状态进入至少需 1 个 A 类触发。
- **防抖优先级**：风险覆盖 > 硬门槛 > 状态冷却 > 连续确认 > 普通评分。风险状态
  （下跌加速/放量派发/趋势破坏）立即覆盖，普通状态需连续 2 周期确认。
- **数据质量降级**：缺指数 → "低"，缺资金 → "中"；数据不足或政策/事件未落地时置信度降一级。

## 输出 7 项（文档第十节）

当前状态 / 状态置信度 / 触发证据 / 数据质量 / 组合约束 / 建议动作 / 是否需写 Decision Log。

## 与基础权重/归一化的实现说明

文档第七节小盘事件股示例先将贴边层钉在下限再压缩其他层；本实现遵循第九节伪代码
"裁剪→归一化"流程，并迭代收敛以确保最终四层仍满足 10%–45% 边界，数值与示例一致
（资金层 ≈10%）。

## 测试

```bash
python -m pytest tests/test_state_machine.py -q
```
