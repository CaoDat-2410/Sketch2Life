from __future__ import annotations

import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

from sketch2life.infrastructure.persistence import be1_bootstrap
from sketch2life.infrastructure.persistence.be1_models import (
    AdultIdentityModel,
    OrganizationAssignmentModel,
    OrganizationModel,
)


def test_bootstrap_flushes_parent_rows_before_organization_assignment(monkeypatch) -> None:
    events: list[tuple[str, type[object]]] = []

    class FakeSession:
        def get(self, model: type[object], subject: str) -> None:
            assert model is AdultIdentityModel
            assert subject == "firebase-subject"
            return None

        def add(self, value: object) -> None:
            events.append(("add", type(value)))

        def flush(self) -> None:
            events.append(("flush", type(None)))

    class FakeFactory:
        @contextmanager
        def begin(self):
            yield FakeSession()

    class FakeVerifier:
        def __init__(self, settings: object) -> None:
            assert getattr(settings, "firebase_project_id") == "sketch2life-dev"

        async def verify(self, token: str) -> SimpleNamespace:
            assert token == "verified-token"
            return SimpleNamespace(
                subject="firebase-subject",
                issuer="https://securetoken.google.com/sketch2life-dev",
            )

    engine = SimpleNamespace(dispose=lambda: None)
    monkeypatch.setattr(
        be1_bootstrap,
        "get_settings",
        lambda: SimpleNamespace(auth_provider="firebase", firebase_project_id="sketch2life-dev"),
    )
    monkeypatch.setattr(be1_bootstrap, "FirebaseTokenVerifier", FakeVerifier)
    monkeypatch.setattr(be1_bootstrap, "create_core_engine", lambda: engine)
    monkeypatch.setattr(be1_bootstrap, "create_core_session_factory", lambda _engine: FakeFactory())

    organization_id, subject = asyncio.run(
        be1_bootstrap._provision("QA school", "verified-token")
    )

    assert organization_id
    assert subject == "firebase-subject"
    assert events == [
        ("add", OrganizationModel),
        ("add", AdultIdentityModel),
        ("flush", type(None)),
        ("add", OrganizationAssignmentModel),
    ]
