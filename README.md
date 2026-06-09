# earnings-analyst

港股财报深度分析工具，基于李录 Owner's Earnings 框架（v1.3），配套量化状态机（v2.0）。

## 两层能力

1. **财报基本面分析**（Owner's Earnings 框架）— 现金流质量、保守估值、8-Combo 信号、仓位建议。
   入口：`python main.py`
2. **个股状态识别**（量化状态机 v2.0）— 稳定识别个股 8 个状态，输出置信度/触发证据/
   数据质量/组合约束/建议动作/Decision Log。入口：`python state_tool.py`
   详见 [docs/state_machine.md](docs/state_machine.md)。

## 快速开始

```bash
# 财报分析
python main.py --ticker 1024.HK

# 个股状态识别（内置示例）
python state_tool.py --demo valid_rebound --show-candidates

# 测试
python -m pytest -q --ignore=tests/test_report_parser.py
```

详细分析框架见 [CLAUDE.md](CLAUDE.md)。
