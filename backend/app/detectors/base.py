"""The evidence-producer contract.

Every detector in this project is an EVIDENCE PRODUCER. It observes the
message and emits Findings. It never assigns a score and never chooses a
category -- that is scoring.py's job, and only scoring.py's job.

A Finding is a statement of fact ("this phrase is present at these
characters"), not a judgement ("this message is a scam").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

# How alarming the observation is ON ITS OWN. This is NOT a score and not a
# verdict: scoring.py decides what a combination of severities adds up to.
Severity = Literal["info", "low", "medium", "high"]

# Which producer emitted the Finding. Kept as a closed set so the response is
# auditable: the user can see exactly which subsystem said what.
DetectorName = Literal[
    "rules",            # generic scam-language rules          (Milestone 5)
    "patterns_in",      # India-specific patterns              (Milestone 5)
    "url_heuristics",   # offline URL inspection               (Milestone 6)
    "url_reputation",   # third-party lookup, opt-in only      (Milestone 7)
    "ml",               # TF-IDF + logistic regression         (Milestone 8)
]


@dataclass(frozen=True)
class Evidence:
    """Where in the message the observation was made.

    Character offsets, not the extracted substring alone, so the UI can
    highlight the span in the original text without re-searching it (and
    without ever building HTML out of attacker-controlled text).
    """

    start: int
    end: int
    quote: str  # message[start:end], carried for convenience and for tests


@dataclass(frozen=True)
class Finding:
    """One factual observation about the message.

    Frozen (immutable) on purpose: once a detector has reported something,
    nothing downstream may quietly edit it. The scorer reads findings; it
    does not rewrite them.
    """

    detector: DetectorName
    code: str                 # stable machine id, e.g. "URGENCY_DEADLINE"
    title: str                # short human label, e.g. "Artificial urgency"
    description: str          # plain-language explanation for the end user
    severity: Severity
    evidence: list[Evidence] = field(default_factory=list)
    # How sure the detector is THAT IT OBSERVED THIS (0.0-1.0) -- not how
    # likely the message is a scam. A regex match is 1.0; an ML signal is not.
    confidence: float = 1.0


@dataclass(frozen=True)
class CheckOutcome:
    """Did this check actually run?

    Recorded separately from findings, because "ran and found nothing" and
    "could not run at all" mean completely different things to the user.
    An absent check must never be presented as a clean result.
    """

    name: str                 # e.g. "url_reputation:google_safe_browsing"
    ok: bool
    detail: str | None = None  # why it failed, or what it covered


@dataclass(frozen=True)
class DetectorResult:
    """What every detector hands back."""

    findings: list[Finding] = field(default_factory=list)
    checks: list[CheckOutcome] = field(default_factory=list)


@runtime_checkable
class Detector(Protocol):
    """The interface. Implemented in Milestones 5-8.

    A Protocol (structural typing) rather than a base class to inherit from:
    a detector only has to *have* these members, it does not have to know
    this file exists. That keeps detectors independently testable.
    """

    name: DetectorName

    def analyze(self, message: str) -> DetectorResult:
        """Pure function: same message in, same findings out.

        Implementations must not mutate the message, must not log it, and
        (except url_reputation, which is opt-in) must not touch the network.
        """
        ...
