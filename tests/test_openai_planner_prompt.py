import pytest

from agentic_qe.data import load_scenario
from agentic_qe.openai_planner import build_planning_prompt


SCENARIO = "examples/sql-etl-reconciliation/scenario.json"


def test_sql_planning_prompt_uses_selected_candidate_query():
    scenario = load_scenario(SCENARIO)
    prompt = build_planning_prompt(
        scenario=scenario,
        relative_scenario=SCENARIO,
        candidate_query_name="regression",
    )
    assert "candidate_query_name='regression'" in prompt
    assert "candidate_query_name='good'" not in prompt
    assert "not currently executable" in prompt


def test_sql_planning_prompt_rejects_unknown_candidate_query():
    scenario = load_scenario(SCENARIO)
    with pytest.raises(ValueError, match="Unknown SQL candidate query"):
        build_planning_prompt(
            scenario=scenario,
            relative_scenario=SCENARIO,
            candidate_query_name="does-not-exist",
        )
