"""Runtime wiring of the encrypted support needs (T-12c).

The production composition sets nothing: no key source is approved yet (gate O-SEED-KEY) and the
Teacher narrow permission has no store (SRS §31.10), so both families answer 503
``SUPPORT_NEEDS_UNAVAILABLE`` and the Teacher family denies every caller. A composition (a test,
later the approved production wiring) sets ``app.state.support_needs_runtime`` to a
`SupportNeedsRuntime` holding the crypto port and, for the Teacher family, the two guard ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import Request
from sqlalchemy.orm import Session

from sketch2life.application.ports.identity import VerifiedPrincipal
from sketch2life.application.ports.support_needs import SupportNeedsCrypto
from sketch2life.infrastructure.persistence.be1_models import ManagedProfileModel


class TeacherSupportNeedsGuard(Protocol):
    """The two proofs a Teacher needs besides the class assignment (owner default C5).

    Both are asked for every profile, synthetic ones included, and both default to deny.
    """

    def consent_effective(self, db: Session, profile: ManagedProfileModel) -> bool: ...

    def permission_granted(
        self, db: Session, principal: VerifiedPrincipal, profile: ManagedProfileModel
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class SupportNeedsRuntime:
    crypto: SupportNeedsCrypto | None = None
    teacher_guard: TeacherSupportNeedsGuard | None = None


def get_support_needs_runtime(request: Request) -> SupportNeedsRuntime:
    runtime = getattr(request.app.state, "support_needs_runtime", None)
    return runtime if isinstance(runtime, SupportNeedsRuntime) else SupportNeedsRuntime()


__all__ = ["SupportNeedsRuntime", "TeacherSupportNeedsGuard", "get_support_needs_runtime"]
