"""The API contract between backend and frontend.

Pydantic models for /api/v1/analyze. These are the OUTSIDE shape of the
system; detectors/base.py holds the INSIDE shape (Finding). Keep the two
separate: internal evidence can be refactored without breaking the frontend.

IMPORTANT: frontend/src/types/analysis.ts is a hand-written mirror of this
file. Change one, change the other in the same commit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Vocabulary -- closed sets, so the frontend can switch on them exhaustively
# ---------------------------------------------------------------------------

# The four verdicts. "Likely Safe" never means guaranteed safe, and
# "Unable to Verify" is a first-class answer, not an error.
Category = Literal["Likely Safe", "Suspicious", "High Risk", "Unable to Verify"]

Severity = Literal["info", "low", "medium", "high"]

DetectorName = Literal[
    "rules", "patterns_in", "url_heuristics", "url_reputation", "ml"
]

# Deliberately NO "clean" / "safe" value. A URL nobody has reported is an
# unreported URL, which is not the same as a verified-safe URL.
ReputationVerdict = Literal[
    "malicious",     # provider positively flags it
    "suspicious",    # provider flags it with lower confidence
    "not_listed",    # provider has no record -- NOT a clean bill of health
    "unavailable",   # lookup not configured, not consented, or failed
]

ReputationProvider = Literal["google_safe_browsing", "virustotal"]


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

MAX_MESSAGE_CHARS = 2000


class AnalyzeRequest(BaseModel):
    """What the browser sends.

    Validation here is the first security boundary: a size cap before any
    detector, any regex or any network call sees the text.
    """

    model_config = ConfigDict(extra="forbid")  # reject unknown keys outright

    message: str = Field(
        min_length=1,
        max_length=MAX_MESSAGE_CHARS,
        description="The raw SMS text. Treated as untrusted attacker input.",
    )
    # Reputation lookups transmit a URL to a third party, so they are OFF by
    # default and require an explicit, informed opt-in per request.
    allow_reputation_lookup: bool = Field(
        default=False,
        description=(
            "If true, URLs found in the message may be sent to third-party "
            "reputation providers. Requires informed user consent in the UI."
        ),
    )


# ---------------------------------------------------------------------------
# Response pieces
# ---------------------------------------------------------------------------


class EvidenceSpan(BaseModel):
    """Character offsets into the submitted message."""

    start: int = Field(ge=0)
    end: int = Field(ge=0)
    quote: str


class WarningSign(BaseModel):
    """A Finding, rendered for the user. One row in the results list."""

    code: str
    title: str
    description: str
    severity: Severity
    detector: DetectorName
    evidence: list[EvidenceSpan] = Field(default_factory=list)


class ReputationResult(BaseModel):
    """One provider's answer about one URL."""

    provider: ReputationProvider
    verdict: ReputationVerdict
    detail: str | None = None
    checked_at: datetime | None = None


class ExtractedUrl(BaseModel):
    """A URL found in the message, described WITHOUT ever visiting it.

    Every field here comes from parsing the string offline. The backend does
    not fetch the URL, does not follow its redirects and does not resolve
    shorteners by requesting them.
    """

    raw: str                        # exactly as it appeared in the SMS
    normalized: str | None = None   # lowercased host, defragmented, etc.
    scheme: str | None = None
    host: str | None = None
    registrable_domain: str | None = None  # "example.co.in" from a subdomain
    path: str | None = None

    is_ip_host: bool = False        # http://203.0.113.7/pay
    is_shortener: bool = False      # bit.ly, tinyurl, t.co ...
    is_punycode: bool = False       # xn-- lookalike domains
    uses_https: bool = False        # NOT evidence of legitimacy

    heuristic_flags: list[str] = Field(default_factory=list)
    reputation: list[ReputationResult] = Field(default_factory=list)

    # Per-URL verdict, same vocabulary as the message verdict.
    assessment: Category = "Unable to Verify"


class CheckRecord(BaseModel):
    """One entry in the audit trail of what the system actually did."""

    name: str
    detail: str | None = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

DISCLAIMER = (
    "Automated detection can make mistakes. This is an educational prototype "
    "and is not affiliated with any bank, company or government agency. "
    "Treat this as one input to your own judgement, not a final answer."
)


class AnalysisResponse(BaseModel):
    """The single response shape. Every field is always present.

    The frontend never has to guess whether a key exists; absence of
    information is expressed as an empty list or an explicit null, which is
    far easier to render honestly than a missing key.
    """

    schema_version: str = "1.0"
    request_id: str
    analyzed_at: datetime

    category: Category

    # Present ONLY when the active methods justify a number. Rule counts are
    # not probabilities; a null score is the honest answer until Milestone 9
    # fuses a calibrated model in. Never fabricate a number to fill the gap.
    score: int | None = Field(default=None, ge=0, le=100)
    score_basis: str | None = Field(
        default=None,
        description="Which methods produced the score, or why there is none.",
    )

    warning_signs: list[WarningSign] = Field(default_factory=list)
    extracted_urls: list[ExtractedUrl] = Field(default_factory=list)

    # Audit trail. checks_failed is what keeps the system honest: a check
    # that could not run is reported, never silently treated as a pass.
    checks_performed: list[CheckRecord] = Field(default_factory=list)
    checks_failed: list[CheckRecord] = Field(default_factory=list)

    # Why the scorer chose this category, in plain language.
    reasons: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)

    disclaimer: str = DISCLAIMER
