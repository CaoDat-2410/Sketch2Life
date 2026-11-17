"""Lightweight V2 prototype errors; safe to import without optional media packages."""


class StoryWorldError(ValueError):
    def __init__(self, code: str, reason: str) -> None:
        super().__init__(f"{code}: {reason}")
        self.code = code
        self.reason = reason
