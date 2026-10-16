"""Tests for KALI Sentinel security tools."""

from kali_sentinel.decider.contracts import SecurityTool
from kali_sentinel.tools.security_tools import (
    ReconTool,
    PortScanTool,
    WebScanTool,
    DnsCheckTool,
    ToolRegistry,
)


def test_recon_tool():
    tool = ReconTool()
    assert tool.tool_type == SecurityTool.RECON
    res = tool.execute("test.local")
    assert res["status"] == "COMPLETED"
    assert "test.local" in res["summary"]
    assert len(res["findings"]) > 0


def test_port_scan_tool():
    tool = PortScanTool()
    assert tool.tool_type == SecurityTool.PORT_SCAN
    res = tool.execute("127.0.0.1", {"ports": [80, 443, 8080]})
    assert res["status"] == "COMPLETED"
    assert "ports_audited" in res["data"]
    assert len(res["data"]["ports_audited"]) == 3
    assert len(res["findings"]) > 0


def test_web_scan_tool():
    tool = WebScanTool()
    assert tool.tool_type == SecurityTool.WEB_SCAN
    res = tool.execute("localhost:8080")
    assert res["status"] == "COMPLETED"
    assert "headers" in res["data"]
    assert "missing_headers" in res["data"]
    assert len(res["findings"]) > 0


def test_dns_check_tool():
    tool = DnsCheckTool()
    assert tool.tool_type == SecurityTool.DNS_CHECK
    res = tool.execute("test.local")
    assert res["status"] == "COMPLETED"
    assert "records" in res["data"]
    assert "SPF" in res["data"]["records"]
    assert len(res["findings"]) > 0


def test_tool_registry():
    reg = ToolRegistry()
    assert reg.get_tool(SecurityTool.PORT_SCAN) is not None
    assert reg.get_tool(SecurityTool.DNS_CHECK) is not None
    assert reg.get_tool(SecurityTool.NO_TOOL) is None

    # Execute valid tool
    out = reg.execute_tool(SecurityTool.DNS_CHECK, "test.local")
    assert out["status"] == "COMPLETED"

    # Execute NO_TOOL
    noop_out = reg.execute_tool(SecurityTool.NO_TOOL, "test.local")
    assert noop_out["status"] == "NO_OP"

    # List tools
    tools = reg.list_tools()
    assert len(tools) == 4
    tool_ids = [t["id"] for t in tools]
    assert "port_scan" in tool_ids
    assert "dns_check" in tool_ids
