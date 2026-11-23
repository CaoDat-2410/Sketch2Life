from types import SimpleNamespace

from firebase_admin import auth

from sketch2life.infrastructure.identity import firebase_token_verifier as verifier_module


def test_verifier_allows_bounded_clock_skew_for_fresh_identity_toolkit_tokens(monkeypatch):
    captured = {}
    project_id = "synthetic-project"
    app = object()

    def verify_id_token(token, **kwargs):
        captured.update(kwargs)
        return {
            "uid": "synthetic-parent",
            "iss": f"https://securetoken.google.com/{project_id}",
            "aud": project_id,
        }

    monkeypatch.setattr(verifier_module, "get_firebase_admin_app", lambda settings: app)
    monkeypatch.setattr(auth, "verify_id_token", verify_id_token)

    verifier = verifier_module.FirebaseTokenVerifier(
        SimpleNamespace(
            firebase_project_id=project_id,
            firebase_check_revoked_tokens=True,
        )
    )
    principal = verifier._verify_sync("synthetic.jwt.token")

    assert captured == {
        "app": app,
        "check_revoked": True,
        "clock_skew_seconds": 30,
    }
    assert principal.subject == "synthetic-parent"
    assert principal.issuer == f"https://securetoken.google.com/{project_id}"
