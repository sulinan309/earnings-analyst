"""ReportParser 测试

使用 mock 模拟 Claude API 返回，验证：
1. PDF 字节流解析流程
2. JSON → ParsedReport 转换
3. 缺失字段标注
4. 文件不存在错误处理
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass

from src.parsers.report_parser import ReportParser, ParsedReport, ExtractedField


# ── 模拟快手 FY2024 的 Claude API 返回 ──

MOCK_KUAISHOU_RESPONSE = {
    "company_name": "快手科技",
    "ticker": "1024.HK",
    "period": "FY2024",
    "original_currency": "人民币",
    "exchange_rate_note": "按 1 CNY = 1.1 HKD 换算",
    "fields": {
        "cfo": {
            "value": 220.0,
            "unit": "亿港币",
            "source": "合并现金流量表 - 经营活动产生的现金流量净额",
            "reason": None,
        },
        "total_capex": {
            "value": 95.0,
            "unit": "亿港币",
            "source": "合并现金流量表 - 购建固定资产、无形资产支出",
            "reason": None,
        },
        "maintenance_capex": {
            "value": None,
            "unit": "亿港币",
            "source": "",
            "reason": "财报附注未单独披露维持性资本支出与扩张性资本支出的拆分",
        },
        "growth_capex": {
            "value": None,
            "unit": "亿港币",
            "source": "",
            "reason": "财报附注未单独披露维持性资本支出与扩张性资本支出的拆分",
        },
        "cash_and_equivalents": {
            "value": 400.0,
            "unit": "亿港币",
            "source": "合并资产负债表 - 现金及现金等价物",
            "reason": None,
        },
        "short_term_investments": {
            "value": 150.0,
            "unit": "亿港币",
            "source": "合并资产负债表 - 短期投资及定期存款",
            "reason": None,
        },
        "interest_bearing_debt": {
            "value": 50.0,
            "unit": "亿港币",
            "source": "合并资产负债表 - 短期借款+长期借款",
            "reason": None,
        },
        "revenue": {
            "value": 1100.0,
            "unit": "亿港币",
            "source": "合并利润表 - 营业收入",
            "reason": None,
        },
        "committed_investments": {
            "value": 25.0,
            "unit": "亿港币",
            "source": "附注 - 资本承诺",
            "reason": None,
        },
        "restricted_cash": {
            "value": 10.0,
            "unit": "亿港币",
            "source": "附注 - 受限制存款",
            "reason": None,
        },
        "overseas_cash": {
            "value": None,
            "unit": "亿港币",
            "source": "",
            "reason": "财报未按地区拆分现金持有情况",
        },
    },
}


def _make_mock_response(raw: dict):
    """构造模拟的 Claude API response 对象"""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = json.dumps(raw, ensure_ascii=False)

    response = MagicMock()
    response.content = [text_block]
    return response


class TestParsedReportStructure:
    """验证 _build_result 正确转换 JSON → ParsedReport"""

    def test_metadata(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.company_name == "快手科技"
        assert result.ticker == "1024.HK"
        assert result.period == "FY2024"
        assert result.original_currency == "人民币"

    def test_cfo_extracted(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.cfo.value == 220.0
        assert result.cfo.reason is None
        assert "现金流量表" in result.cfo.source

    def test_total_capex_extracted(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.total_capex.value == 95.0

    def test_maintenance_capex_null_with_reason(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.maintenance_capex.value is None
        assert "附注未单独披露" in result.maintenance_capex.reason

    def test_revenue_extracted(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.revenue.value == 1100.0

    def test_overseas_cash_null_with_reason(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        assert result.overseas_cash.value is None
        assert "未按地区拆分" in result.overseas_cash.reason


class TestMissingFields:
    """验证缺失字段检测"""

    def test_missing_fields_list(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        missing = result.missing_fields()
        names = [name for name, _ in missing]
        # 3 个字段缺失：maintenance_capex, growth_capex, overseas_cash
        assert "maintenance_capex" in names
        assert "growth_capex" in names
        assert "overseas_cash" in names
        assert len(missing) == 3

    def test_missing_fields_have_reasons(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        for name, reason in result.missing_fields():
            assert reason != "未说明原因"


class TestJsonOutput:
    """验证 JSON 序列化"""

    def test_to_json_parseable(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        text = result.to_json()
        parsed = json.loads(text)
        assert parsed["company_name"] == "快手科技"
        assert parsed["cfo"]["value"] == 220.0
        assert parsed["maintenance_capex"]["value"] is None

    def test_to_dict(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["ticker"] == "1024.HK"


class TestAPICalling:
    """验证 API 调用流程（mock）"""

    @patch("src.parsers.report_parser.anthropic.Anthropic")
    def test_parse_pdf_bytes(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response(MOCK_KUAISHOU_RESPONSE)

        parser = ReportParser(api_key="test-key")
        result = parser.parse_pdf_bytes(b"%PDF-1.4 fake pdf content")

        assert result.company_name == "快手科技"
        assert result.cfo.value == 220.0

        # 验证调用参数
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-6"
        assert call_kwargs["thinking"] == {"type": "adaptive"}
        assert "format" in call_kwargs["output_config"]

    @patch("src.parsers.report_parser.anthropic.Anthropic")
    def test_parse_pdf_file_not_found(self, mock_anthropic_cls):
        parser = ReportParser(api_key="test-key")
        with pytest.raises(FileNotFoundError):
            parser.parse_pdf("/nonexistent/path/report.pdf")

    @patch("src.parsers.report_parser.anthropic.Anthropic")
    def test_api_returns_no_text(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # 模拟只有 thinking block 没有 text block
        thinking_block = MagicMock()
        thinking_block.type = "thinking"
        response = MagicMock()
        response.content = [thinking_block]
        mock_client.messages.create.return_value = response

        parser = ReportParser(api_key="test-key")
        with pytest.raises(ValueError, match="未返回文本内容"):
            parser.parse_pdf_bytes(b"%PDF-1.4 fake")


class TestPrintReport:
    """打印完整的解析结果（用 -s 查看）"""

    def test_print_parsed_report(self):
        parser = ReportParser.__new__(ReportParser)
        result = parser._build_result(MOCK_KUAISHOU_RESPONSE)

        print(f"\n{'='*50}")
        print(f"  {result.company_name} ({result.ticker}) {result.period}")
        print(f"  原始币种: {result.original_currency} | {result.exchange_rate_note}")
        print(f"{'='*50}")
        print(result.to_json())

        missing = result.missing_fields()
        if missing:
            print(f"\n缺失字段 ({len(missing)} 项):")
            for name, reason in missing:
                print(f"  • {name}: {reason}")
