import asyncio

import pytest

pytestmark = pytest.mark.integration


def test_mcp_server_lists_and_calls_read_only_tools():
    pytest.importorskip("mcp")
    from mcp import Client
    from agentic_qe.mcp_server import build_mcp_server

    async def run():
        server = build_mcp_server()
        async with Client(server) as client:
            tools = await client.list_tools()
            by_name = {tool.name: tool for tool in tools.tools}
            expected_names = {"scenario_context", "dataset_profile", "database_profile", "quality_capabilities"}
            assert expected_names.issubset(by_name)
            assert by_name["scenario_context"].output_schema is not None
            assert by_name["database_profile"].output_schema is not None

            result = await client.call_tool(
                "scenario_context",
                {"scenario_path": "examples/etl-decimal-precision/scenario.json"},
            )
            assert result.is_error is False
            assert result.structured_content is not None
            assert result.structured_content["risk"] == "HIGH"

    asyncio.run(run())
