from types import SimpleNamespace
from unittest.mock import Mock

from firebase_admin import auth
from pydantic import SecretStr

from sketch2life.infrastructure.local_demo import parent_seed, teacher_seed


def test_existing_parent_seed_identity_syncs_configured_password(monkeypatch):
    email = "parent.demo@sketch2life.local"
    user = SimpleNamespace(uid="seed-parent-uid", email=email)
    admin_app = object()
    update_user = Mock(return_value=user)
    monkeypatch.setattr(parent_seed, "get_firebase_admin_app", lambda _settings: admin_app)
    monkeypatch.setattr(auth, "get_user", Mock(return_value=user))
    monkeypatch.setattr(auth, "update_user", update_user)

    settings = SimpleNamespace(
        local_seed_parent_email=email,
        local_seed_parent_password=SecretStr("local-parent-password"),
        env="local",
        auth_provider="firebase",
        firebase_project_id="sketch2life-dev",
    )

    subject = parent_seed._seed_firebase_parent(settings)

    assert subject == user.uid
    update_user.assert_called_once_with(
        user.uid, password="local-parent-password", app=admin_app
    )


def test_existing_teacher_seed_identity_syncs_configured_password(monkeypatch):
    email = "teacher.demo@sketch2life.local"
    user = SimpleNamespace(uid="seed-teacher-uid", email=email)
    admin_app = object()
    update_user = Mock(return_value=user)
    monkeypatch.setattr(
        teacher_seed,
        "get_settings",
        lambda: SimpleNamespace(
            env="local",
            auth_provider="firebase",
            firebase_project_id="sketch2life-dev",
        ),
    )
    monkeypatch.setattr(teacher_seed, "get_firebase_admin_app", lambda _settings: admin_app)
    monkeypatch.setattr(auth, "get_user", Mock(return_value=user))
    monkeypatch.setattr(auth, "update_user", update_user)

    subject = teacher_seed._seed_auth_user(
        email=email,
        password="local-teacher-password",
        project_id="sketch2life-dev",
    )

    assert subject == user.uid
    update_user.assert_called_once_with(
        user.uid, password="local-teacher-password", app=admin_app
    )
