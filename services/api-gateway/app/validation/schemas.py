"""Shared types for the per-file data-quality report."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Finding:
    rule: str
    severity: Severity
    message: str
    path: str = ""  # dotted path to the offending element, for UI click-to-jump
    details: dict = field(default_factory=dict)


@dataclass
class ValidationReport:
    source_path: str
    findings: list[Finding] = field(default_factory=list)

    def add(self, rule: str, severity: Severity, message: str, path: str = "", **details) -> None:
        self.findings.append(Finding(rule=rule, severity=severity, message=message, path=path, details=details))

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.WARNING)

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "findings": [
                {
                    "rule": f.rule,
                    "severity": f.severity.value,
                    "message": f.message,
                    "path": f.path,
                    "details": f.details,
                }
                for f in self.findings
            ],
        }
