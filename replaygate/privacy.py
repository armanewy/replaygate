"""Privacy hooks for report generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ReportRedactor(Protocol):
    """Hook for future payload and message redaction strategies."""

    def redact(self, value: str) -> str:
        """Return a redacted representation of the provided string."""


@dataclass(slots=True)
class NoopReportRedactor:
    """Default placeholder redactor used by the MVP."""

    def redact(self, value: str) -> str:
        return value
