from __future__ import annotations

import base64
import json
import time
from types import SimpleNamespace

import pytest
from firebase_admin import auth

from sketch2life.application.ports.identity import IdentityAccountProvisioningUnavailable
from sketch2life.infrastructure.identity import (
    firebase_admin_account_provisioner as provisioner_module,
)
from sketch2life.infrastructure.identity import (
    firebase_token_verifier as verifier_module,
)
from sketch2life.infrastructure.identity.firebase_admin_account_provisioner import (
    FirebaseAdminAccountProvisioner,
)
from sketch2life.infrastructure.identity.firebase_token_verifier import (
    FirebaseTokenVerifier,
    IdentityVerificationUnavailable,
)


def _encoded_token(payload: dict[str, object]) -> str:
    payload_segment = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        .rstrip(b"=")
        .decode("ascii")
    )
    return f"header.{payload_segment}.signature"


def test_firebase_token_verifier_logs_only_typed_claim_diagnostics(caplog, monkeypatch) -> None:
    project_id = "synthetic-project"
    email = "private-parent@example.invalid"
    uid = "private-firebase-uid"
    subject = "private-token-subject"
    claim = "private-token-claim-value"
    child_data = "private-child-name"
    authorization = "Bearer private-authorization-value"
    encoded_token = _encoded_token(
        {
            "uid": uid,
            "sub": subject,
            "iss": f"https://securetoken.google.com/{project_id}",
            "aud": project_id,
            "exp": int(time.time()) + 300,
            "email": email,
            "jti": claim,
            "name": child_data,
        }
    )
    provider_message = (
        f"private provider detail {encoded_token} {authorization} {email} {uid} "
        f"{subject} {claim} {child_data}"
    )

    def reject_token(_encoded_token: str, **_kwargs: object) -> None:
        raise RuntimeError(provider_message)

    monkeypatch.setattr(verifier_module, "get_firebase_admin_app", lambda _settings: object())
    monkeypatch.setattr(auth, "verify_id_token", reject_token)
    verifier = FirebaseTokenVerifier(
        SimpleNamespace(
            firebase_project_id=project_id,
            firebase_check_revoked_tokens=True,
        )
    )

    with pytest.raises(IdentityVerificationUnavailable):
        verifier._verify_sync(encoded_token)

    assert "firebase_token_verification_failed stage=verify" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "error_module=builtins" in caplog.text
    assert "token_payload_decodable=True" in caplog.text
    assert "token_audience_matches_project=True" in caplog.text
    assert "token_issuer_matches_project=True" in caplog.text
    assert "token_subject_present=True" in caplog.text
    assert "token_expiration_in_future=True" in caplog.text
    for sensitive_value in (
        provider_message,
        encoded_token,
        authorization,
        email,
        uid,
        subject,
        claim,
        child_data,
    ):
        assert sensitive_value not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)


def test_firebase_provisioner_logs_exception_types_without_provider_message(
    caplog, monkeypatch
) -> None:
    email = "private-parent@example.invalid"
    password = "private-password-value"
    uid = "private-firebase-uid"
    claim = "private-token-claim-value"
    child_data = "private-child-name"
    authorization = "Bearer private-authorization-value"
    create_message = f"private create provider detail {email} {password} {uid} {claim} {child_data}"
    delete_message = f"private delete provider detail {uid} {claim} {child_data} {authorization}"

    def fail_create(**_kwargs: object) -> None:
        try:
            raise OSError("private cause detail")
        except OSError as cause:
            raise RuntimeError(create_message) from cause

    def fail_delete(_subject: str, **_kwargs: object) -> None:
        raise ValueError(delete_message)

    monkeypatch.setattr(provisioner_module, "get_firebase_admin_app", lambda _settings: object())
    monkeypatch.setattr(auth, "create_user", fail_create)
    monkeypatch.setattr(auth, "delete_user", fail_delete)
    provisioner = FirebaseAdminAccountProvisioner(SimpleNamespace())

    with pytest.raises(IdentityAccountProvisioningUnavailable):
        provisioner.create_password_account(email=email, password=password)
    with pytest.raises(IdentityAccountProvisioningUnavailable):
        provisioner.delete_account(uid)

    assert "firebase_account_provisioning_failed stage=create" in caplog.text
    assert "firebase_account_provisioning_failed stage=delete" in caplog.text
    assert "error_type=RuntimeError" in caplog.text
    assert "error_type=ValueError" in caplog.text
    assert "cause_type=OSError" in caplog.text
    for sensitive_value in (
        create_message,
        delete_message,
        "private cause detail",
        email,
        password,
        uid,
        claim,
        child_data,
        authorization,
    ):
        assert sensitive_value not in caplog.text
    assert all(record.exc_info is None for record in caplog.records)
