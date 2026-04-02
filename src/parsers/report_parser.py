"""财报 PDF 解析器 — 使用 Claude API 提取 OE 计算所需字段

将财报 PDF 发送给 Claude，通过结构化输出提取：
- 经营性现金流 (CFO)
- 资本支出（总 CapEx，拆分维持性 vs 扩张性）
- 现金及等价物、短期理财、有息负债
- 营业收入（用于计算月均运营储备）
- 已承诺投资款、受限资金
- 海外现金

字段缺失时标注 null 并说明原因。
"""

import base64
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

import anthropic


EXTRACTION_PROMPT = """\
你是一位专业的港股财报分析师。请从这份财报中提取以下财务数据，所有金额统一换算为**亿港币**。

需要提取的字段：

1. **经营性现金流 (CFO)**: 经营活动产生的现金流量净额
2. **总资本支出 (total_capex)**: 购建固定资产、无形资产等支出（取正数）
3. **维持性资本支出 (maintenance_capex)**: 如果附注中有拆分（如折旧替换、维护性支出），请提取；否则设为 null
4. **扩张性资本支出 (growth_capex)**: 如果附注中有拆分（如新业务投资、产能扩张），请提取；否则设为 null
5. **现金及等价物 (cash_and_equivalents)**: 资产负债表中的现金及现金等价物
6. **短期理财 (short_term_investments)**: 短期投资、定期存款、理财产品等
7. **有息负债 (interest_bearing_debt)**: 短期借款 + 长期借款 + 应付债券等有息负债合计
8. **营业收入 (revenue)**: 全年/半年营业收入总额
9. **已承诺投资款 (committed_investments)**: 附注中披露的已承诺但未支付的资本承诺
10. **受限资金 (restricted_cash)**: 受限制的现金或存款
11. **海外现金 (overseas_cash)**: 如有披露海外子公司持有的现金，请提取

**重要规则**：
- 如果某个字段在财报中找不到，设为 null 并在 reason 中说明原因
- 维持性 vs 扩张性资本支出的拆分通常需要查看附注，如果附注未拆分，total_capex 必须填写，maintenance_capex 设为 null 并说明
- 所有金额必须换算为亿港币（如果原始单位是人民币，请按约 1.1 的汇率换算并注明）
- 注明财报期间（如 FY2024、2024H1）
- 注明原始币种"""


@dataclass
class ExtractedField:
    """单个提取字段"""
    value: float | None
    unit: str = "亿港币"
    source: str = ""       # 数据在财报中的位置（如"合并现金流量表"）
    reason: str | None = None  # value 为 null 时的原因


@dataclass
class ParsedReport:
    """财报解析结果"""
    company_name: str = ""
    ticker: str = ""
    period: str = ""
    original_currency: str = ""
    exchange_rate_note: str = ""

    # OE 相关
    cfo: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    total_capex: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    maintenance_capex: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    growth_capex: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))

    # 净现金相关
    cash_and_equivalents: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    short_term_investments: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    interest_bearing_debt: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))

    # 营收
    revenue: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))

    # 扣除项
    committed_investments: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    restricted_cash: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))
    overseas_cash: ExtractedField = field(default_factory=lambda: ExtractedField(value=None))

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def missing_fields(self) -> list[tuple[str, str]]:
        """返回所有缺失字段及原因"""
        missing = []
        for name in [
            "cfo", "total_capex", "maintenance_capex", "growth_capex",
            "cash_and_equivalents", "short_term_investments",
            "interest_bearing_debt", "revenue",
            "committed_investments", "restricted_cash", "overseas_cash",
        ]:
            f: ExtractedField = getattr(self, name)
            if f.value is None:
                missing.append((name, f.reason or "未说明原因"))
        return missing


# Claude API 返回的 JSON Schema
OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "ticker": {"type": "string"},
            "period": {"type": "string"},
            "original_currency": {"type": "string"},
            "exchange_rate_note": {"type": "string"},
            "fields": {
                "type": "object",
                "properties": {
                    name: {
                        "type": "object",
                        "properties": {
                            "value": {"type": ["number", "null"]},
                            "unit": {"type": "string"},
                            "source": {"type": "string"},
                            "reason": {"type": ["string", "null"]},
                        },
                        "required": ["value", "unit", "source", "reason"],
                        "additionalProperties": False,
                    }
                    for name in [
                        "cfo", "total_capex", "maintenance_capex", "growth_capex",
                        "cash_and_equivalents", "short_term_investments",
                        "interest_bearing_debt", "revenue",
                        "committed_investments", "restricted_cash", "overseas_cash",
                    ]
                },
                "required": [
                    "cfo", "total_capex", "maintenance_capex", "growth_capex",
                    "cash_and_equivalents", "short_term_investments",
                    "interest_bearing_debt", "revenue",
                    "committed_investments", "restricted_cash", "overseas_cash",
                ],
                "additionalProperties": False,
            },
        },
        "required": [
            "company_name", "ticker", "period",
            "original_currency", "exchange_rate_note", "fields",
        ],
        "additionalProperties": False,
    },
}


class ReportParser:
    """使用 Claude API 解析财报 PDF，提取 OE 计算所需字段"""

    def __init__(
        self,
        model: str = "claude-opus-4-6",
        api_key: str | None = None,
    ):
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def parse_pdf(self, pdf_path: str | Path) -> ParsedReport:
        """解析本地 PDF 文件

        Args:
            pdf_path: PDF 文件路径

        Returns:
            ParsedReport 结构化解析结果
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

        pdf_data = base64.standard_b64encode(pdf_path.read_bytes()).decode("utf-8")

        return self._call_api(
            document_content={
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data,
                },
            }
        )

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> ParsedReport:
        """解析内存中的 PDF 字节流"""
        pdf_data = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        return self._call_api(
            document_content={
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data,
                },
            }
        )

    def _call_api(self, document_content: dict) -> ParsedReport:
        """调用 Claude API 提取财务数据"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"format": OUTPUT_SCHEMA},
            messages=[
                {
                    "role": "user",
                    "content": [
                        document_content,
                        {"type": "text", "text": EXTRACTION_PROMPT},
                    ],
                }
            ],
        )

        # 提取 JSON 文本
        text = next(
            (b.text for b in response.content if b.type == "text"), None
        )
        if text is None:
            raise ValueError("Claude API 未返回文本内容")

        raw = json.loads(text)
        return self._build_result(raw)

    def _build_result(self, raw: dict) -> ParsedReport:
        """将 API 返回的 JSON 转为 ParsedReport"""
        fields = raw.get("fields", {})

        result = ParsedReport(
            company_name=raw.get("company_name", ""),
            ticker=raw.get("ticker", ""),
            period=raw.get("period", ""),
            original_currency=raw.get("original_currency", ""),
            exchange_rate_note=raw.get("exchange_rate_note", ""),
        )

        for name in [
            "cfo", "total_capex", "maintenance_capex", "growth_capex",
            "cash_and_equivalents", "short_term_investments",
            "interest_bearing_debt", "revenue",
            "committed_investments", "restricted_cash", "overseas_cash",
        ]:
            f = fields.get(name, {})
            setattr(result, name, ExtractedField(
                value=f.get("value"),
                unit=f.get("unit", "亿港币"),
                source=f.get("source", ""),
                reason=f.get("reason"),
            ))

        return result
