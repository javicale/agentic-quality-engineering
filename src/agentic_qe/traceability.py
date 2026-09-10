from __future__ import annotations

from typing import Any

from .contracts import ValidationPlan
from .models import DifferentialResult, ReleaseSignal


CAPABILITY_REGISTRY: dict[str, dict[str, Any]] = {
    "csv-record-differential": {"domains": ["csv"], "description": "Compare expected and candidate CSV records deterministically."},
    "projected-schema-differential": {"domains": ["sql"], "description": "Compare projected baseline/candidate SQL result columns."},
    "business-key-reconciliation": {"domains": ["csv", "sql"], "description": "Detect missing and unexpected business keys."},
    "duplicate-key-detection": {"domains": ["sql"], "description": "Detect duplicate business-key cardinality."},
    "critical-field-differential": {"domains": ["csv", "sql"], "description": "Compare critical field values exactly."},
    "database-metadata-profile": {"domains": ["sql"], "description": "Produce sanitized row/null/key-cardinality database metadata."},
    "validation-plan-eval": {"domains": ["governance"], "description": "Evaluate the structured validation plan deterministically."},
    "execution-gating": {"domains": ["governance"], "description": "Block weak or unsafe validation plans before execution."},
    "structured-evidence": {"domains": ["governance"], "description": "Persist machine-readable validation evidence."},
    "execution-observability": {"domains": ["governance"], "description": "Persist append-only execution events."},
    "human-release-approval": {"domains": ["governance"], "description": "Preserve mandatory human release accountability."},
}


def capability_catalog() -> list[dict[str, Any]]:
    return [
        {"id": capability_id, "domains": details["domains"], "description": details["description"]}
        for capability_id, details in sorted(CAPABILITY_REGISTRY.items())
    ]


def _result(capability_id: str, status: str, *evidence_refs: str) -> dict[str, Any]:
    return {"id": capability_id, "status": status, "evidence_refs": list(evidence_refs)}


def _common_results(*, eval_passed: bool, gate_allowed: bool, human_release_approval: bool, execution_started: bool) -> dict[str, dict[str, Any]]:
    return {
        "validation-plan-eval": _result("validation-plan-eval", "PASS" if eval_passed else "FAIL", "eval-result.json"),
        "execution-gating": _result("execution-gating", "PASS" if gate_allowed else "FAIL", "execution-gate.json"),
        "structured-evidence": _result("structured-evidence", "PASS", "evidence.json"),
        "execution-observability": _result("execution-observability", "PASS" if execution_started else "NOT_RUN", "events.jsonl"),
        "human-release-approval": _result("human-release-approval", "PASS" if human_release_approval else "FAIL", "execution-gate.json"),
    }


def build_csv_capability_results(*, differential: DifferentialResult | None, critical_fields: list[str], eval_passed: bool, gate_allowed: bool, human_release_approval: bool) -> dict[str, dict[str, Any]]:
    results = _common_results(eval_passed=eval_passed, gate_allowed=gate_allowed, human_release_approval=human_release_approval, execution_started=differential is not None)
    if differential is None:
        results.update({
            "csv-record-differential": _result("csv-record-differential", "NOT_RUN"),
            "business-key-reconciliation": _result("business-key-reconciliation", "NOT_RUN"),
            "critical-field-differential": _result("critical-field-differential", "NOT_RUN"),
        })
        return results
    findings = differential.differences
    key_failed = any(item.field in {"__key__", "__row__"} for item in findings)
    critical_failed = any(item.field in set(critical_fields) for item in findings)
    results.update({
        "csv-record-differential": _result("csv-record-differential", differential.status, "evidence.json"),
        "business-key-reconciliation": _result("business-key-reconciliation", "FAIL" if key_failed else "PASS", "evidence.json"),
        "critical-field-differential": _result("critical-field-differential", "FAIL" if critical_failed else "PASS", "evidence.json"),
    })
    return results


def build_sql_capability_results(*, differential: DifferentialResult | None, profiles: dict[str, Any] | None, critical_fields: list[str], eval_passed: bool, gate_allowed: bool, human_release_approval: bool) -> dict[str, dict[str, Any]]:
    results = _common_results(eval_passed=eval_passed, gate_allowed=gate_allowed, human_release_approval=human_release_approval, execution_started=differential is not None)
    if differential is None:
        results.update({
            "projected-schema-differential": _result("projected-schema-differential", "NOT_RUN"),
            "business-key-reconciliation": _result("business-key-reconciliation", "NOT_RUN"),
            "duplicate-key-detection": _result("duplicate-key-detection", "NOT_RUN"),
            "critical-field-differential": _result("critical-field-differential", "NOT_RUN"),
            "database-metadata-profile": _result("database-metadata-profile", "NOT_RUN"),
        })
        return results
    findings = differential.differences
    schema_failed = any(item.row_key == "__schema__" for item in findings)
    key_failed = any(item.field in {"__key__", "__row__"} for item in findings)
    duplicate_failed = any(item.field == "__key__" and item.observed == "duplicate key" for item in findings)
    critical_failed = any(item.field in set(critical_fields) for item in findings)
    results.update({
        "projected-schema-differential": _result("projected-schema-differential", "FAIL" if schema_failed else "PASS", "database-differential.json"),
        "business-key-reconciliation": _result("business-key-reconciliation", "FAIL" if key_failed else "PASS", "database-differential.json"),
        "duplicate-key-detection": _result("duplicate-key-detection", "FAIL" if duplicate_failed else "PASS", "database-differential.json"),
        "critical-field-differential": _result("critical-field-differential", "FAIL" if critical_failed else "PASS", "database-differential.json"),
        "database-metadata-profile": _result("database-metadata-profile", "PASS" if profiles is not None else "NOT_RUN", "database-profile.json"),
    })
    return results


def build_plan_traceability(*, plan: ValidationPlan, capability_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scenario_rows: list[dict[str, Any]] = []
    high_priority_gaps: list[str] = []
    lower_priority_gaps: list[str] = []
    for scenario in plan.scenarios:
        declared = scenario.required_capabilities
        unsupported = [cap for cap in declared if cap not in CAPABILITY_REGISTRY]
        deferred = [cap for cap in declared if cap in CAPABILITY_REGISTRY and (cap not in capability_results or capability_results[cap]["status"] == "NOT_RUN")]
        mapped = [
            {
                "capability": cap,
                "registry_status": "SUPPORTED" if cap in CAPABILITY_REGISTRY else "UNSUPPORTED",
                "execution_status": capability_results[cap]["status"] if cap in capability_results else "NOT_RUN",
            }
            for cap in declared
        ]
        if unsupported:
            mapping_status = "UNSUPPORTED"
        elif not declared or deferred:
            mapping_status = "DEFERRED"
        else:
            mapping_status = "SUPPORTED"
        executed_statuses = [capability_results[cap]["status"] for cap in declared if cap in capability_results]
        if "FAIL" in executed_statuses:
            execution_status = "FAIL"
        elif mapping_status != "SUPPORTED" or "NOT_RUN" in executed_statuses:
            execution_status = "NOT_EXECUTED"
        elif declared and all(status == "PASS" for status in executed_statuses):
            execution_status = "PASS"
        else:
            execution_status = "NOT_EXECUTED"
        evidence_refs: list[str] = []
        for cap in declared:
            for ref in capability_results.get(cap, {}).get("evidence_refs", []):
                if ref not in evidence_refs:
                    evidence_refs.append(ref)
        row = {
            "scenario": scenario.name,
            "priority": scenario.priority,
            "required_capabilities": declared,
            "mapping_status": mapping_status,
            "execution_status": execution_status,
            "unsupported_capabilities": unsupported,
            "deferred_capabilities": deferred,
            "capability_results": mapped,
            "evidence_refs": evidence_refs,
        }
        scenario_rows.append(row)
        if execution_status != "PASS":
            label = f"{scenario.name}: {mapping_status}/{execution_status}"
            if scenario.priority in {"HIGH", "CRITICAL"}:
                high_priority_gaps.append(label)
            else:
                lower_priority_gaps.append(label)
    if high_priority_gaps:
        gate_status = "BLOCKED"
        gate_reasons = ["HIGH/CRITICAL validation scenarios lack complete executable coverage.", *high_priority_gaps]
    elif lower_priority_gaps:
        gate_status = "WARN"
        gate_reasons = ["LOW/MEDIUM validation scenarios have incomplete executable coverage.", *lower_priority_gaps]
    else:
        gate_status = "PASS"
        gate_reasons = []
    return {
        "schema_version": "1.0",
        "capability_registry": capability_catalog(),
        "coverage_gate": {"status": gate_status, "reasons": gate_reasons},
        "summary": {
            "planned_scenarios": len(scenario_rows),
            "passed": sum(row["execution_status"] == "PASS" for row in scenario_rows),
            "failed": sum(row["execution_status"] == "FAIL" for row in scenario_rows),
            "not_executed": sum(row["execution_status"] == "NOT_EXECUTED" for row in scenario_rows),
            "supported": sum(row["mapping_status"] == "SUPPORTED" for row in scenario_rows),
            "deferred": sum(row["mapping_status"] == "DEFERRED" for row in scenario_rows),
            "unsupported": sum(row["mapping_status"] == "UNSUPPORTED" for row in scenario_rows),
        },
        "scenarios": scenario_rows,
    }


def apply_traceability_policy(signal: ReleaseSignal, traceability: dict[str, Any]) -> ReleaseSignal:
    gate = traceability["coverage_gate"]
    if gate["status"] == "BLOCKED":
        reasons = list(signal.blocking_reasons)
        for reason in ["Plan-to-execution traceability blocked release because required HIGH/CRITICAL coverage is incomplete.", *gate["reasons"]]:
            if reason not in reasons:
                reasons.append(reason)
        return ReleaseSignal(decision="NO_GO", residual_risk="HIGH", blocking_reasons=reasons, conditions=[])
    if gate["status"] == "WARN":
        conditions = list(signal.conditions)
        condition = "Review incomplete LOW/MEDIUM plan-to-execution coverage before release."
        if condition not in conditions:
            conditions.append(condition)
        if signal.decision == "GO":
            return ReleaseSignal(decision="CONDITIONAL_GO", residual_risk="MEDIUM", blocking_reasons=[], conditions=conditions)
        return ReleaseSignal(decision=signal.decision, residual_risk=signal.residual_risk, blocking_reasons=signal.blocking_reasons, conditions=conditions)
    return signal
