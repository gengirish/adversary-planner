"""Custom exception hierarchy for adversary planner.

Follows the error-handling-patterns skill: typed exceptions with
error codes, context details, and a clean hierarchy.
"""

from __future__ import annotations

from datetime import datetime


class PlannerError(Exception):
    """Base exception for all adversary planner errors."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()


class CampaignNotFoundError(PlannerError):
    """Raised when a campaign ID doesn't exist on disk."""

    def __init__(self, campaign_id: str):
        super().__init__(
            f"Campaign not found: {campaign_id}",
            code="CAMPAIGN_NOT_FOUND",
            details={"campaign_id": campaign_id},
        )


class CampaignNotLoadedError(PlannerError):
    """Raised when an operation requires a loaded campaign but none is active."""

    def __init__(self):
        super().__init__(
            "No campaign is loaded. Call create() or load() first.",
            code="CAMPAIGN_NOT_LOADED",
        )


class TargetFileError(PlannerError):
    """Raised when the target YAML file is missing or malformed."""

    def __init__(self, path: str, reason: str = ""):
        detail = f": {reason}" if reason else ""
        super().__init__(
            f"Invalid target file '{path}'{detail}",
            code="TARGET_FILE_ERROR",
            details={"path": path, "reason": reason},
        )


class ReportParseError(PlannerError):
    """Raised when a scanner report file cannot be parsed."""

    def __init__(self, path: str, reason: str = ""):
        detail = f": {reason}" if reason else ""
        super().__init__(
            f"Failed to parse report '{path}'{detail}",
            code="REPORT_PARSE_ERROR",
            details={"path": path, "reason": reason},
        )


class TechniqueNotFoundError(PlannerError):
    """Raised when a technique ID doesn't exist in the catalog."""

    def __init__(self, technique_id: str):
        super().__init__(
            f"Technique not found: {technique_id}",
            code="TECHNIQUE_NOT_FOUND",
            details={"technique_id": technique_id},
        )


class ValidationError(PlannerError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str = "", value: object = None):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value is not None else ""},
        )
