"""Settings for the backend-only live Lightning development adapter."""

from __future__ import annotations

import hmac
import secrets
from functools import lru_cache
from ipaddress import ip_address
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_PROFILE_RECEIPT_KEY_BYTES = 32


class Settings(BaseSettings):
    _BACKEND_ROOT = Path(__file__).resolve().parents[4]
    model_config = SettingsConfigDict(
        env_prefix="SKETCH2LIFE_",
        # One root .env is shared by local backend, Docker Compose and app clients.
        # Explicit process/container environment variables still take precedence.
        env_file=(_BACKEND_ROOT.parent / ".env",),
        # The shared file also contains Compose and Vite client keys owned elsewhere.
        extra="ignore",
        # A validation error must never echo the raw environment values (the probe credential).
        hide_input_in_errors=True,
    )

    env: Literal["local", "test", "staging", "production"] = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: SecretStr | None = None
    redis_url: SecretStr | None = None
    room_code_hmac_key: SecretStr | None = None
    s3_endpoint: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket: str = "sketch2life-private"
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None
    clamav_host: str | None = None
    clamav_port: int = Field(default=3310, ge=1, le=65535)
    # T-2z (TD-29): "local_test_allowlist" swaps ClamAV for a fixture-hash allowlist scanner and a
    # signature media validator. Refused outside local/test (see the policy validator below).
    scanner_adapter: Literal["clamav", "local_test_allowlist"] = "clamav"
    local_scanner_allowlist_file: Path | None = None
    # T-1a (OD-03): "local_test" composes the accept-all local/test pair of the Parent video
    # admission ports. Refused outside local/test (see the policy validator below). "unconfigured"
    # composes nothing: the video route answers 503 PROVIDER_UNAVAILABLE after its other checks.
    story_video_adapters: Literal["unconfigured", "local_test"] = "unconfigured"
    # FEAT-093: "modal_dev" makes the video worker render real videos through the Modal dev apps; "fixture" keeps the
    # synthetic stand-in. Only the worker process reads it (no Modal credential reaches the app or the API route).
    story_video_renderer: Literal["fixture", "modal_dev"] = "fixture"
    # Per-call timeout of the two admission ports (BR-38: no port call inside a transaction).
    story_video_port_timeout_seconds: float = Field(default=5.0, ge=0.1, le=30.0)
    # T-1c (SRS l.1676, l.1691, TD-07): signing secret of the Parent video playback token. Blank
    # means unset. Unset in staging/production the playback routes answer 503 (fail closed at the
    # route; the API still starts); local/test then use a per-process key. Never logged or echoed.
    story_playback_signing_secret: SecretStr | None = None
    story_playback_key_id: str = Field(default="k1", pattern=r"^[A-Za-z0-9_-]{1,16}$")
    # Rotation: the previous secret keeps verifying tokens that are still alive.
    story_playback_previous_secret: SecretStr | None = None
    story_playback_previous_key_id: str | None = Field(
        default=None, pattern=r"^[A-Za-z0-9_-]{1,16}$"
    )
    # "Short-lived" has no number in the SRS (Q4): 300 s by default, 900 s at most.
    story_playback_token_ttl_seconds: int = Field(default=300, ge=30, le=900)
    # An object over this size is refused before the first byte (the port has no range read).
    story_playback_max_object_bytes: int = Field(
        default=100 * 1024 * 1024, ge=1024, le=2 * 1024 * 1024 * 1024
    )
    # T-1d1-fix (SRS l.1799, l.2867 S12, FR-O-03 l.608): the periodic story sweep (lost-task reaper,
    # admission reconciler, adult-wait closeout). The SRS gives no interval and no batch size: the
    # defaults are safe, not licensed, and local/test shorten or disable them by environment. The
    # task lease is bounded by the 6 h AI job deadline, the only number the SRS licenses (l.615).
    story_sweep_enabled: bool = True
    story_sweep_interval_seconds: int = Field(default=300, ge=1, le=3600)
    story_sweep_batch_size: int = Field(default=50, ge=1, le=200)
    story_sweep_task_lease_seconds: int = Field(default=21_600, ge=60, le=21_600)
    platform_admin_bootstrap_email: str = ""
    smtp_host: str | None = None
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_from: str = "Sketch2Life <no-reply@sketch2life.local>"
    smtp_starttls: bool = False
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    billing_sandbox_enabled: bool = False
    billing_real_payments_enabled: bool = False
    momo_partner_code: str = ""
    momo_access_key: SecretStr | None = None
    momo_secret_key: SecretStr | None = None
    momo_partner_name: str = "Sketch2Life"
    momo_endpoint: str = "https://test-payment.momo.vn/v2/gateway/api/create"
    momo_return_url: str = ""
    momo_ipn_url: str = ""
    vnpay_tmn_code: str = ""
    vnpay_hash_secret: SecretStr | None = None
    vnpay_payment_url: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    vnpay_query_url: str = "https://sandbox.vnpayment.vn/merchant_webapi/api/transaction"
    vnpay_server_ip: str = ""
    vnpay_return_url: str = ""
    vnpay_ipn_url: str = ""
    billing_provider_timeout_seconds: int = Field(default=35, ge=30, le=60)
    storage_example_enabled: bool = False
    storage_example_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024, ge=1, le=50 * 1024 * 1024
    )
    be1_artifact_root: Path = Path(".runtime/be1-artifacts")
    session_idle_ttl_seconds: int = Field(default=1800, ge=60, le=86_400)
    # FEAT-064 dev pilot: synthetic eligibility is honored only when this is on in local/test.
    synthetic_pilot_enabled: bool = False
    # FEAT-066 T-4b1 (OPEN-3, owner-visible): the most draws (one draw, one stale reselect) a
    # lesson occurrence ever gets. A product deviation that goes beyond SRS l.346; 1 forbids the
    # reselect, 2 is the shipped default, and a higher cap needs a migration (draw_no is 1 or 2).
    teacher_sample_max_draws: int = Field(default=2, ge=1, le=2)
    # T-7c (OD-06, SRS l.832): the real child-data path is built but off. While off, a profile
    # create with a `consent_id` is refused; when on it is still refused until X-19 (no valid
    # consent state exists). It never makes a real profile writable by itself.
    real_profile_data_enabled: bool = False
    # T0.3 (SRS l.814): optional operator credential for /health/ready and /metrics. Empty or
    # whitespace-only counts as not set (Compose passes unset optionals as an empty string).
    ops_probe_token: SecretStr | None = None
    # T-7c-fix (O-1, BR-34 l.278, SRS l.1697): server-side secret of the profile-create receipt
    # fingerprint (HMAC-SHA-256). Blank means unset. local/test generate a per-process key when
    # it is unset; staging/production never do, and real-data profiles cannot be enabled there
    # without it. It is never the room-code key, never logged and never stored.
    profile_receipt_hmac_key: SecretStr | None = None
    # T-7c-fix (O-2, NFR-12 l.637): provisional limits of the real-data gate (X-18: a benchmark
    # sets the real FR-O-06 numbers). Attempts per window, per account and per client address.
    # The upper bounds also cap the limiter's memory: at most 1024 tracked keys per dimension
    # times the limit in timestamps (about 1 million floats at the address bound).
    profile_gate_account_limit: int = Field(default=5, ge=1, le=200)
    profile_gate_ip_limit: int = Field(default=20, ge=1, le=1000)
    profile_gate_window_seconds: int = Field(default=60, ge=1, le=3600)

    auth_provider: Literal["development", "firebase"] = "development"
    firebase_project_id: str = ""
    firebase_credentials_file: Path | None = None
    firebase_admin_json_base64: SecretStr | None = None
    firebase_check_revoked_tokens: bool = True

    # Provider calls stay backend-side; Modal is limited to local synthetic validation.
    ai_provider: Literal["disabled", "lightning_dev", "runpod", "modal_dev"] = "disabled"
    # Checking an adult's own topic with the model (see .env.example); off unless enabled locally.
    parent_topic_subject_ai_enabled: bool = False
    lightning_ai_base_url: str = ""
    lightning_ai_token_file: Path | None = None
    lightning_model_profile: str = "live-p2-understanding-v1"
    lightning_asr_profile: str = "WHISPER_TURBO_FP16_AUTO_V1"
    lightning_asr_path: str = "/v1/asr"
    lightning_vision_path: str = "/v1/vision"
    lightning_vision_v2_path: str = "/v2/vision"
    lightning_sam21_enabled: bool = False
    lightning_sam21_path: str = "/v2/rig/segment"
    pixi_show_planner_enabled: bool = False
    pixi_sprite_cycle_dev_preview_enabled: bool = False
    lightning_pixi_show_path: str = "/v4/pixi/show-plan"
    lightning_whiteboard_localization_path: str = "/v1/whiteboard/localize"
    lightning_whiteboard_segmentation_path: str = "/v1/whiteboard/segment"
    whiteboard_video_enabled: bool = False
    whiteboard_video_auto_run: bool = False
    whiteboard_video_artifact_root: Path = Path(".runtime/whiteboard")
    whiteboard_video_max_size_bytes: int = Field(default=12 * 1024 * 1024, ge=1)
    whiteboard_learning_thread_fixture: Path | None = None
    whiteboard_tts_executable: str = "espeak-ng"
    whiteboard_ffmpeg_executable: str = "ffmpeg"
    live_fixture_root: Path | None = None
    runpod_endpoint_id: str = ""
    runpod_api_key_file: Path | None = None
    ai_connect_timeout_seconds: float = 5.0
    ai_request_timeout_seconds: float = 120.0
    story_video_request_timeout_seconds: float = Field(default=2100.0, ge=1800.0)
    story_render_v2_enabled: bool = False  # prototype only; does not replace V1 video jobs

    @property
    def pixi_sprite_cycle_dev_preview_allowed(self) -> bool:
        """Keep the owner-authorized preview unavailable outside local/test deployments."""
        return self.pixi_sprite_cycle_dev_preview_enabled and self.env in {"local", "test"}

    @field_validator("ops_probe_token", mode="before")
    @classmethod
    def blank_ops_probe_token_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, SecretStr) and not value.get_secret_value().strip():
            return None
        return value

    @field_validator(
        "story_playback_signing_secret", "story_playback_previous_secret", mode="before"
    )
    @classmethod
    def blank_playback_secret_is_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, SecretStr) and not value.get_secret_value().strip():
            return None
        return value

    @field_validator("story_playback_previous_key_id", mode="before")
    @classmethod
    def blank_playback_previous_key_id_is_unset(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("profile_receipt_hmac_key", mode="before")
    @classmethod
    def blank_profile_receipt_key_is_unset(cls, value: object) -> object:
        # A blank `NAME=` line (the .env example, Compose forwarding an empty variable) is unset.
        if isinstance(value, str) and not value.strip():
            return None
        if isinstance(value, SecretStr) and not value.get_secret_value().strip():
            return None
        return value
    @property
    def momo_payment_configured(self) -> bool:
        momo_endpoint = urlsplit(self.momo_endpoint)
        return bool(
            self.momo_partner_code
            and self.momo_access_key
            and self.momo_access_key.get_secret_value()
            and self.momo_secret_key
            and self.momo_secret_key.get_secret_value()
            and self.momo_return_url
            and self.momo_ipn_url
            and self._payment_callback_url_configured(self.momo_return_url)
            and self._payment_callback_url_configured(self.momo_ipn_url)
            and momo_endpoint.scheme == "https"
            and momo_endpoint.hostname in {"test-payment.momo.vn", "payment.momo.vn"}
            and momo_endpoint.path == "/v2/gateway/api/create"
        )

    @property
    def momo_sandbox_enabled(self) -> bool:
        return urlsplit(self.momo_endpoint).hostname == "test-payment.momo.vn"

    @property
    def vnpay_payment_configured(self) -> bool:
        payment_endpoint = urlsplit(self.vnpay_payment_url)
        query_endpoint = urlsplit(self.vnpay_query_url)
        try:
            query_server_ip = ip_address(self.vnpay_server_ip)
            query_server_ip_configured = query_server_ip.version == 4 and query_server_ip.is_global
        except ValueError:
            query_server_ip_configured = False
        return bool(
            self.vnpay_tmn_code
            and self.vnpay_hash_secret
            and self.vnpay_hash_secret.get_secret_value()
            and self.vnpay_return_url
            and self.vnpay_ipn_url
            and self._payment_callback_url_configured(self.vnpay_return_url)
            and self._payment_callback_url_configured(self.vnpay_ipn_url)
            and payment_endpoint.scheme == "https"
            and payment_endpoint.hostname in {"sandbox.vnpayment.vn", "pay.vnpay.vn"}
            and payment_endpoint.path == "/paymentv2/vpcpay.html"
            and query_endpoint.scheme == "https"
            and query_endpoint.hostname in {"sandbox.vnpayment.vn", "merchant.vnpay.vn"}
            and query_endpoint.path == "/merchant_webapi/api/transaction"
            and query_server_ip_configured
        )

    @property
    def vnpay_sandbox_enabled(self) -> bool:
        return urlsplit(self.vnpay_payment_url).hostname == "sandbox.vnpayment.vn"

    def _payment_callback_url_configured(self, url: str) -> bool:
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.netloc:
            return True
        return (
            self.env in {"local", "test"}
            and parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        )

    @model_validator(mode="after")
    def enforce_deployment_provider_policy(self) -> Self:
        # Checked first so staging/production fail on this reason before any other policy reason.
        if self.scanner_adapter != "clamav" and self.env not in {"local", "test"}:
            raise ValueError("the local test scanner adapter is available only in local/test")
        if self.story_video_adapters != "unconfigured" and self.env not in {"local", "test"}:
            raise ValueError("the local test video adapters are available only in local/test")

        if self.ops_probe_token is not None:
            # Checked here, not in a field validator, so a validation error never echoes the value.
            probe_token = self.ops_probe_token.get_secret_value()
            if len(probe_token) < 32 or not all("!" <= char <= "~" for char in probe_token):
                raise ValueError(
                    "the operator probe credential must be 32 or more visible ASCII characters"
                )

        # T-1c: checked here, not in a field validator, so an error never echoes a secret.
        for playback_secret in (
            self.story_playback_signing_secret,
            self.story_playback_previous_secret,
        ):
            if playback_secret is not None:
                value = playback_secret.get_secret_value()
                if len(value) < 32 or not all("!" <= char <= "~" for char in value):
                    raise ValueError(
                        "a playback signing secret must be 32 or more visible ASCII characters"
                    )
        if self.story_playback_previous_secret is not None and (
            self.story_playback_signing_secret is None
            or self.story_playback_previous_key_id is None
            or self.story_playback_previous_key_id == self.story_playback_key_id
        ):
            raise ValueError(
                "a previous playback secret needs the active secret and its own key id"
            )

        # T-7c-fix (O-1): checked here, not in a field validator, so an error never echoes the key.
        if self.profile_receipt_hmac_key is not None:
            receipt_key = self.profile_receipt_hmac_key.get_secret_value()
            if len(receipt_key.encode("utf-8")) < MIN_PROFILE_RECEIPT_KEY_BYTES:
                raise ValueError("the profile receipt key must be 32 or more bytes")
            # Never the room-code key (F-01); the message does not echo either value.
            if self.room_code_hmac_key is not None and hmac.compare_digest(
                receipt_key.encode("utf-8"),
                self.room_code_hmac_key.get_secret_value().encode("utf-8"),
            ):
                raise ValueError("the profile receipt key must differ from the room-code key")
        elif self.env in {"local", "test"}:
            # Per-process key: a replay after a restart or on another worker is not recognised
            # (400 INVALID_IDEMPOTENCY_KEY); set the key explicitly to avoid it.
            self.profile_receipt_hmac_key = SecretStr(secrets.token_urlsafe(48))
        elif self.real_profile_data_enabled:
            raise ValueError(
                "real profile data in staging/production requires the profile receipt key"
            )

        if self.storage_example_enabled and self.env != "local":
            raise ValueError("the storage example is available only in local development")

        has_s3_access_key = bool(self.s3_access_key and self.s3_access_key.get_secret_value())
        has_s3_secret_key = bool(self.s3_secret_key and self.s3_secret_key.get_secret_value())
        if has_s3_access_key != has_s3_secret_key:
            raise ValueError("S3 access key and secret key must be configured together")

        if self.env in {"staging", "production"} and (
            self.auth_provider != "firebase" or not self.firebase_project_id
        ):
            raise ValueError("staging/production requires configured Firebase Authentication")

        if self.env == "production":
            if self.ai_provider != "runpod":
                raise ValueError("production requires the approved Runpod AI provider")
            if not self.runpod_endpoint_id or self.runpod_api_key_file is None:
                raise ValueError("production Runpod endpoint and key file are required")

        if self.ai_provider == "modal_dev" and self.env not in {"local", "test"}:
            raise ValueError("Modal dev inference is available only in local/test environments")

        return self


class CoreDatabaseSettings(BaseSettings):
    """Database-only configuration for adapters and Alembic, independent of providers."""

    _BACKEND_ROOT = Path(__file__).resolve().parents[4]
    model_config = SettingsConfigDict(
        env_prefix="SKETCH2LIFE_",
        env_file=(_BACKEND_ROOT.parent / ".env",),
        extra="ignore",
    )

    database_url: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_core_database_settings() -> CoreDatabaseSettings:
    return CoreDatabaseSettings()
