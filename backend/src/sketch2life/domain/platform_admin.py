"""Provider-independent Admin command failures and publication invariants."""


class AdminError(ValueError):
    def __init__(self, code: str, status: int = 409):
        self.code, self.status = code, status
        super().__init__(code)


def require_revision(actual: int, expected: int) -> None:
    if actual != expected:
        raise AdminError("STALE_REVISION")


def independent_reviewer(author: str, reviewer: str) -> None:
    if author == reviewer:
        raise AdminError("INDEPENDENT_REVIEW_REQUIRED", 403)
