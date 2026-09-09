import pytest

pytestmark = pytest.mark.integration


def test_openai_agent_adapter_builds_without_model_call():
    pytest.importorskip("agents")
    from agents.mcp import MCPServerStdio
    from agentic_qe.contracts import ValidationPlan
    from agentic_qe.openai_planner import build_validation_agent

    server = MCPServerStdio(
        name="contract-only",
        params={"command": "python", "args": ["-m", "agentic_qe.mcp_server"]},
    )
    agent = build_validation_agent(model="gpt-5.6-luna", mcp_server=server)
    assert agent.name == "Quality Validation Planner"
    assert agent.output_type is ValidationPlan
    assert agent.mcp_servers == [server]
