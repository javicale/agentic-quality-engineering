from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Priority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _normalize_capability_id(value: str) -> str:
    return "-".join(str(value).strip().lower().replace("_", "-").split())


class ValidationScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    assertion: str = Field(min_length=1)
    expected: str = Field(min_length=1)
    priority: Priority = "HIGH"
    evidence: list[str] = Field(default_factory=list)
    required_capabilities: list[str] = Field(default_factory=list)

    @field_validator("required_capabilities")
    @classmethod
    def normalize_capabilities(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            capability = _normalize_capability_id(value)
            if capability and capability not in seen:
                cleaned.append(capability)
                seen.add(capability)
        return cleaned


class ValidationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = "Validate the requested change against defined quality risks."
    risk_coverage: list[str]
    differential_testing: bool
    human_release_approval: bool
    evidence: list[str]
    scenarios: list[ValidationScenario]
    requested_tools: list[str] = Field(default_factory=list)
    rationale: str = ""
    generated_by: str = "embedded"

    @field_validator("risk_coverage", "evidence", "requested_tools")
    @classmethod
    def normalize_tokens(cls, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            token = str(value).strip().lower()
            if token and token not in seen:
                cleaned.append(token)
                seen.add(token)
        return cleaned


class PlannerMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str | None = None
    transport: str | None = None
    tool_server: str | None = None
    live_model_call: bool = False
    notes: list[str] = Field(default_factory=list)


class PlannedValidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: ValidationPlan
    metadata: PlannerMetadata


class ExecutionGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed: bool
    status: Literal["PASS", "BLOCKED"]
    reasons: list[str] = Field(default_factory=list)
    required_human_approval: bool = True
