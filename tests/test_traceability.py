from agentic_qe.contracts import ValidationPlan
from agentic_qe.models import ReleaseSignal
from agentic_qe.traceability import apply_traceability_policy, build_plan_traceability


def make_plan(*, priority="HIGH", capability="critical-field-differential"):
    return ValidationPlan.model_validate({
        "objective": "Trace a planned scenario to deterministic execution.",
        "risk_coverage": ["functional", "data integrity"],
        "differential_testing": True,
        "human_release_approval": True,
        "evidence": ["structured result", "execution events"],
        "requested_tools": ["quality_capabilities"],
        "rationale": "Traceability fixture.",
        "generated_by": "test",
        "scenarios": [{
            "name": "traceable_check",
            "assertion": "the deterministic capability must execute the requested check",
            "expected": "the mapped capability returns a decision-grade result",
            "priority": priority,
            "evidence": ["structured result"],
            "required_capabilities": [capability],
        }],
    })


def go_signal():
    return ReleaseSignal(decision="GO", residual_risk="LOW", blocking_reasons=[], conditions=[])


def test_supported_executed_scenario_passes_traceability():
    trace = build_plan_traceability(
        plan=make_plan(),
        capability_results={
            "critical-field-differential": {
                "id": "critical-field-differential",
                "status": "PASS",
                "evidence_refs": ["evidence.json"],
            }
        },
    )
    assert trace["coverage_gate"]["status"] == "PASS"
    assert trace["summary"]["passed"] == 1
    assert trace["scenarios"][0]["mapping_status"] == "SUPPORTED"
    assert trace["scenarios"][0]["execution_status"] == "PASS"
    assert apply_traceability_policy(go_signal(), trace).decision == "GO"


def test_unsupported_high_scenario_blocks_release():
    trace = build_plan_traceability(plan=make_plan(capability="mutation-testing"), capability_results={})
    assert trace["coverage_gate"]["status"] == "BLOCKED"
    assert trace["scenarios"][0]["mapping_status"] == "UNSUPPORTED"
    assert trace["scenarios"][0]["execution_status"] == "NOT_EXECUTED"
    release = apply_traceability_policy(go_signal(), trace)
    assert release.decision == "NO_GO"
    assert release.residual_risk == "HIGH"


def test_unexecuted_low_scenario_degrades_go_to_conditional_go():
    trace = build_plan_traceability(
        plan=make_plan(priority="LOW"),
        capability_results={
            "critical-field-differential": {
                "id": "critical-field-differential",
                "status": "NOT_RUN",
                "evidence_refs": [],
            }
        },
    )
    assert trace["coverage_gate"]["status"] == "WARN"
    release = apply_traceability_policy(go_signal(), trace)
    assert release.decision == "CONDITIONAL_GO"
    assert release.residual_risk == "MEDIUM"
