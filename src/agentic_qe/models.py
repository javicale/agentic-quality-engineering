from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Status = Literal["PASS", "FAIL", "WARN"]
ReleaseDecision = Literal["GO", "CONDITIONAL_GO", "NO_GO"]


@dataclass(frozen=True)
class EvalDimension:
    name: str
    score: int
    max_score: int
    rationale: str


@dataclass(frozen=True)
class EvalResult:
    status: Status
    score: int
    max_score: int
    threshold: int
    dimensions: list[EvalDimension]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Difference:
    row_key: str
    field: str
    expected: str | None
    observed: str | None
    severity: str
    message: str


@dataclass(frozen=True)
class DifferentialResult:
    status: Status
    compared_rows: int
    difference_count: int
    differences: list[Difference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReleaseSignal:
    decision: ReleaseDecision
    residual_risk: str
    blocking_reasons: list[str]
    conditions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
