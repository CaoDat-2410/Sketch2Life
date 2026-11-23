"""Shared §9.8 error envelope for the CONV-1 route families (FEAT-066 D-066-68, D-066-71).

The envelope carries the six SRS §9.8 fields, always present, plus ``request_id`` (equal to
``correlation_id``) and, with ``STALE_REVISION`` only, ``current_version``. Messages come from
one Vietnamese table; route-supplied message text is never copied into a response.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

# Route families that use this envelope (CONV-1 §3.1). `/api/parent/v1/ai`, the frozen M2
# Parent-profile and StoryRun families and the legacy demo families are deliberately absent.
CONV1_PREFIXES: tuple[str, ...] = (
    "/api/be1/v1",
    "/api/lesson-library/v1",
    "/api/platform-admin/v1",
    "/api/auth/v1",
    "/api/teacher/v1/",
    # FEAT-066 T0.4: trailing slash so a sibling such as ``/v1/jobsfoo`` is not captured.
    "/v1/jobs/",
)

# FEAT-066 T-2a: the generic upload sessions (SRS l.1654-1658) use the same envelope, but only while
# they are mounted: the StoryRun-lite demo owns the literal path with its own bodies, so a caller
# that serves the demo asks ``is_conv1_path(..., include_upload_sessions=False)``. The base is
# matched on a whole segment, so ``/v1/upload-sessionsfoo`` is not captured.
UPLOAD_SESSIONS_BASE = "/v1/upload-sessions"

# FEAT-066 T-3a: the Teacher lesson occurrences (SRS l.1652-1660). No demo owns this path, so the
# base is always part of the family; it is matched on a whole segment like the upload base.
LESSON_OCCURRENCES_BASE = "/v1/lesson-occurrences"

# FEAT-066 T-8a: the notification inbox (SRS l.1681). Matched on a whole segment, so
# ``/v1/notificationsfoo`` is not captured; the T-8b push-endpoint paths are not registered.
NOTIFICATIONS_BASE = "/v1/notifications"

FIELD_ERROR_CODES = frozenset(
    {
        "REQUIRED",
        "TOO_LONG",
        "OUT_OF_RANGE",
        "EMPTY",
        "INVALID_TYPE",
        "INVALID_FORMAT",
        "UNKNOWN_FIELD",
        # FEAT-066 T-3d: a value the API deliberately refuses for now (a Teacher-written activity
        # while no safety checklist exists, an activity-catalog reference before TD-16). Without
        # this member ``safe_field_errors`` would drop the explicit signal.
        "NOT_SUPPORTED",
    }
)

_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MAX_FIELD_LENGTH = 120

# Legacy generic codes and their §9.8 replacements (CONV-1 §3.2 item 2b, owner CV-2 = A).
GENERIC_CODE_MAP: Mapping[str, str] = {
    "AUTHENTICATION_REQUIRED": "AUTH_REQUIRED",
    "UNAUTHENTICATED": "AUTH_REQUIRED",
    "INVALID_IDENTITY_TOKEN": "INVALID_TOKEN",
    "FORBIDDEN": "ACTION_NOT_ALLOWED",
    "NOT_FOUND": "RESOURCE_NOT_FOUND",
    "CONFLICT": "INVALID_STATE_TRANSITION",
    "INVALID_TRANSITION": "INVALID_STATE_TRANSITION",
    "REQUEST_VALIDATION_FAILED": "INVALID_REQUEST",
    "SERVICE_UNAVAILABLE": "PROVIDER_UNAVAILABLE",
    "DEPENDENCY_UNAVAILABLE": "PROVIDER_UNAVAILABLE",
}

# 404 codes that keep their own name (anti-enumeration or deferred to a slice).
KEPT_404_CODES = frozenset({"JOIN_UNAVAILABLE", "CANVAS_SOURCE_UNAVAILABLE"})

STATUS_DEFAULT_CODES: Mapping[int, str] = {
    400: "INVALID_REQUEST",
    401: "AUTH_REQUIRED",
    403: "ACTION_NOT_ALLOWED",
    404: "RESOURCE_NOT_FOUND",
    405: "ACTION_NOT_ALLOWED",
    409: "INVALID_STATE_TRANSITION",
    413: "MEDIA_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    429: "RATE_LIMITED",
    500: "INTERNAL_SERVER_ERROR",
    502: "PROVIDER_BAD_RESPONSE",
    503: "PROVIDER_UNAVAILABLE",
    504: "PROVIDER_UNAVAILABLE",
}

MESSAGES: Mapping[str, str] = {
    "AUTH_REQUIRED": "Vui lòng đăng nhập để tiếp tục.",
    "INVALID_TOKEN": "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
    "TOKEN_EXPIRED": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
    "ACTION_NOT_ALLOWED": "Tài khoản không được phép thực hiện thao tác này.",
    "RESOURCE_NOT_FOUND": "Không tìm thấy tài nguyên được yêu cầu.",
    "INVALID_STATE_TRANSITION": "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này.",
    "INVALID_REQUEST": "Yêu cầu không hợp lệ.",
    "INVALID_IDEMPOTENCY_KEY": "Khóa yêu cầu trùng với một yêu cầu có nội dung khác.",
    "STALE_REVISION": "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.",
    "PROVIDER_UNAVAILABLE": "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.",
    "PROVIDER_BAD_RESPONSE": "Không thể hoàn tất yêu cầu lúc này.",
    "RATE_LIMITED": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
    "MEDIA_TOO_LARGE": "Dữ liệu gửi lên vượt quá giới hạn cho phép.",
    "UNSUPPORTED_MEDIA_TYPE": "Định dạng nội dung không được hỗ trợ.",
    "INTERNAL_SERVER_ERROR": "Máy chủ chưa thể hoàn tất yêu cầu.",
    # FEAT-066 C4: SRS §9.8 upload codes for the Lesson Library (SRS 867-871, 1725).
    "LESSON_FILE_TOO_LARGE": (
        "Tệp giáo án vượt quá 25 MB. Chỉ nhận PDF, DOCX hoặc PPTX; hãy chọn tệp khác."
    ),
    "UPLOAD_PART_CONFLICT": "Phần tệp này đã được gửi với nội dung khác.",
    "UPLOAD_SESSION_STATE_CONFLICT": "Phiên tải lên không còn ở trạng thái cho phép thao tác này.",
    "UPLOAD_SESSION_EXPIRED": "Phiên tải lên đã hết hạn. Vui lòng tải tệp lại từ đầu.",
    "UPLOAD_INCOMPLETE": "Tệp chưa được tải lên đủ các phần.",
    # FEAT-066 T-2a: SRS §9.8 upload codes of the generic upload sessions (l.867-873).
    "UNSUPPORTED_LESSON_TYPE": "Chỉ nhận tệp giáo án PDF, DOCX hoặc PPTX.",
    "UPLOAD_CHECKSUM_MISMATCH": "Nội dung tải lên không khớp với mã kiểm tra đã khai báo.",
    "UPLOAD_CONTENT_MISMATCH": "Nội dung tệp không khớp với định dạng đã khai báo.",
    "STORAGE_UNAVAILABLE": "Kho lưu trữ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.",
    # FEAT-066 T-2c: SRS l.982, a run audio over 20,000,000 bytes or two minutes.
    "AUDIO_TOO_LARGE": "Bản ghi âm vượt quá 2 phút hoặc 20 MB. Vui lòng ghi âm ngắn hơn.",
    # FEAT-066 T-3a: SRS §9.8 l.866, a Teacher who is not assigned to the class.
    "TEACHER_ASSIGNMENT_REQUIRED": "Giáo viên chưa được phân công phụ trách lớp học này.",
    # FEAT-066 T-4b1: SRS §9.8 l.866 and l.871, the sample-video gates of the child selection.
    "SAMPLE_VIDEO_ALREADY_EXISTS": (
        "Buổi học này đã có video mẫu. Không thể chọn bé cho một video mẫu khác."
    ),
    "LESSON_PLAN_NOT_APPROVED": (
        "Giáo án của buổi học chưa được duyệt. Vui lòng duyệt giáo án rồi thử lại."
    ),
    # FEAT-066 T-3b: refusals of an attached occurrence document (SRS §9.8 l.862-873; the last
    # three are the parser's own stable codes, not named by §9.8, see T-3b-DEC-5).
    "INVALID_FILE_CONTENT": (
        "Nội dung tệp không hợp lệ hoặc không đọc được. Vui lòng chọn tệp khác."
    ),
    "OCR_NOT_SUPPORTED": (
        "Tệp chỉ gồm trang quét ảnh nên chưa thể đọc văn bản. Vui lòng dùng tệp có văn bản."
    ),
    "ENCRYPTED_DOCUMENT_UNSUPPORTED": (
        "Tệp được mã hóa hoặc đặt mật khẩu. Vui lòng gỡ mật khẩu rồi tải lại."
    ),
    "DOCUMENT_PAGE_LIMIT_EXCEEDED": (
        "Tệp vượt quá 100 trang hoặc slide. Vui lòng chia nhỏ tệp rồi tải lại."
    ),
    "DOCUMENT_TEXT_LIMIT_EXCEEDED": (
        "Văn bản trong tệp quá dài (tối đa 2 MB). Vui lòng rút gọn tệp rồi tải lại."
    ),
}

STATUS_MESSAGES: Mapping[int, str] = {
    400: MESSAGES["INVALID_REQUEST"],
    401: MESSAGES["AUTH_REQUIRED"],
    403: MESSAGES["ACTION_NOT_ALLOWED"],
    404: MESSAGES["RESOURCE_NOT_FOUND"],
    405: MESSAGES["ACTION_NOT_ALLOWED"],
    409: "Yêu cầu xung đột với trạng thái hiện tại.",
    410: "Tài nguyên không còn khả dụng.",
    413: MESSAGES["MEDIA_TOO_LARGE"],
    415: MESSAGES["UNSUPPORTED_MEDIA_TYPE"],
    422: "Yêu cầu chưa đáp ứng điều kiện nghiệp vụ.",
    429: MESSAGES["RATE_LIMITED"],
    500: MESSAGES["INTERNAL_SERVER_ERROR"],
    502: MESSAGES["PROVIDER_BAD_RESPONSE"],
    503: MESSAGES["PROVIDER_UNAVAILABLE"],
    504: MESSAGES["PROVIDER_UNAVAILABLE"],
}
_GENERIC_4XX_MESSAGE = "Không thể hoàn tất yêu cầu."
_GENERIC_5XX_MESSAGE = MESSAGES["INTERNAL_SERVER_ERROR"]

# Domain codes that are kept by name and answered with the status message (CONV-1 §3.2 item 2c).
# The coverage test fails when a code literal in a scanned module is in neither set.
STATUS_MESSAGE_ONLY = frozenset(
    {
        "ACCOUNT_SCOPE_UNAVAILABLE", "ACCOUNT_SETUP_UNAVAILABLE", "ACCOUNT_UPDATE_UNAVAILABLE",
        "ACTIVE_TURN_REQUIRED", "ADMITTED_MEMBER_REQUIRED", "AGGREGATE_SCOPE_CONFLICT",
        "ARTIFACT_INTEGRITY_FAILED", "ARTIFACT_PROVIDER_UNCONFIGURED",
        "ASSISTANCE_DISPOSITION_REQUIRED", "ASSISTANCE_REVIEW_PENDING", "BE1_RUNTIME_UNAVAILABLE",
        "CANVAS_CAPACITY_REACHED", "CANVAS_IMAGE_NOT_ADMITTED", "CANVAS_PROFILE_INVALID",
        "CANVAS_RENDER_BUSY", "CANVAS_RENDER_DEADLINE_EXCEEDED", "CANVAS_RENDER_INTEGRITY_FAILED",
        "CANVAS_RENDER_PILOT_DISABLED", "CANVAS_SOURCE_TOO_LARGE", "CANVAS_SOURCE_UNAVAILABLE",
        "CANVAS_UNAVAILABLE", "CHECKPOINT_INVALID", "CHECKPOINT_OPERATION_REQUIRED",
        "CHECKPOINT_STORAGE_INTEGRITY", "CHECKPOINT_UNAVAILABLE", "CLASS_SCOPE_MISMATCH",
        "CLASS_TEACHER_EXISTS", "COMPLETION_STAGE_REQUIRED", "CONSENT_NOT_EFFECTIVE",
        "CONTRIBUTORS_REQUIRED", "DATABASE_NOT_CONFIGURED", "DATABASE_UNAVAILABLE",
        "DEVICE_AUTHENTICATION_REQUIRED", "DEVICE_GRANT_INACTIVE", "DEVICE_MEMBERSHIP_INACTIVE",
        "DEVICE_SCOPE_INACTIVE", "DRAWING_RECEIPT_REQUIRED", "EMAIL_VERIFICATION_REQUIRED",
        "GALLERY_NOT_PUBLISHED",
        "GROUP_DRAFT_REQUIRED", "GROUP_NOT_WRITABLE", "IDEMPOTENCY_KEY_REUSED",
        "IDENTITY_ISSUER_MISMATCH", "IDENTITY_PROVIDER_UNAVAILABLE", "IMAGE_DIMENSIONS_EXCEEDED",
        "IMAGE_INVALID", "INVALID_DEVICE_CREDENTIAL", "INVALID_GALLERY_TRANSITION",
        "INVALID_GROUP_TRANSITION", "INVALID_SOURCE_DOCUMENT", "INVALID_STAGE_TRANSITION",
        "INVITATION_EXISTS", "INVITATION_EXPIRED", "JOIN_UNAVAILABLE", "JOIN_WINDOW_CLOSED",
        "LAST_PLATFORM_ADMIN", "LEARNING_STAGE_CONFLICT", "LEARNING_STAGE_UNAVAILABLE",
        "MALWARE_DETECTED", "MEDIA_TYPE_MISMATCH", "MEMBER_ALREADY_ADMITTED",
        "MODAL_AI_NOT_ENABLED", "MODAL_MODEL_REVISION_MISMATCH", "MODAL_OUTCOME_UNKNOWN",
        "MODAL_OUTPUT_CONTRACT_INVALID", "OBSERVATION_TOO_LARGE", "ORGANIZATION_REQUIRED",
        "ORGANIZATION_UNAVAILABLE", "PART_CONFLICT", "PILOT_ASSISTANCE_DISABLED",
        "PILOT_LEDGER_UNAVAILABLE", "PILOT_PROFILE_LOOKUP_UNAVAILABLE", "PUBLICATION_REQUIRED",
        "PUBLISHED_GALLERY_REQUIRED", "REQUEST_TOO_LARGE", "RESERVED_CONFIGURATION_KEY",
        "RESOURCE_CONFLICT", "ROOM_CODE_CLOSED", "ROOM_CODE_RATE_LIMITED", "ROOM_CODE_UNAVAILABLE",
        "SCOPE_DENIED", "SELF_DISABLE_DENIED", "SELF_ROLE_CHANGE_DENIED", "SESSION_NOT_ACTIVE",
        "SESSION_NOT_IN_LOBBY",
        "SESSION_NOT_OPEN", "SESSION_NOT_RUNNING", "SESSION_OUTCOME_ALREADY_RECORDED",
        "SRS_STAGE_CONTRACT_UNAVAILABLE", "STALE_AGGREGATE", "STALE_CANVAS_REVISION",
        "STALE_SESSION_REVISION", "STALE_STAGE_REVISION", "SYNTHETIC_PROFILE_CREATION_UNAVAILABLE",
        "TEACHER_ORGANIZATION_ACCESS_REQUIRED", "TEACHER_PLAN_FIELD_LIMIT_EXCEEDED",
        "UNFINISHED_GROUP_SET_MISMATCH", "UPLOAD_EXPIRED", "UPLOAD_TOO_LARGE",
    }
)

# 422 codes sent through HTTPException that become 400 INVALID_REQUEST (§3.2 item 2a).
_VALIDATION_422_CODES = frozenset({"INVALID_REQUEST", "IDEMPOTENCY_KEY_REQUIRED"})


def is_conv1_path(path: str, *, include_upload_sessions: bool = True) -> bool:
    """Return whether a request path belongs to a CONV-1 envelope family."""
    if path.startswith(CONV1_PREFIXES):
        return True
    if path == LESSON_OCCURRENCES_BASE or path.startswith(LESSON_OCCURRENCES_BASE + "/"):
        return True
    if path == NOTIFICATIONS_BASE or path.startswith(NOTIFICATIONS_BASE + "/"):
        return True
    return include_upload_sessions and (
        path == UPLOAD_SESSIONS_BASE or path.startswith(UPLOAD_SESSIONS_BASE + "/")
    )


def _valid_code(value: object) -> str | None:
    return value if isinstance(value, str) and _CODE_PATTERN.fullmatch(value) else None


def map_code(status: int, code: str | None) -> str:
    """Map a route code to its public code: generic map, uniform 404, else the status default."""
    if code is None:
        return STATUS_DEFAULT_CODES.get(
            status, "INVALID_REQUEST" if 400 <= status < 500 else "INTERNAL_SERVER_ERROR"
        )
    if code in GENERIC_CODE_MAP:
        return GENERIC_CODE_MAP[code]
    if status == 404 and code.endswith("_NOT_FOUND"):
        return "RESOURCE_NOT_FOUND"
    return code


def message_for(status: int, code: str) -> str:
    """Return the safe Vietnamese message for a code, falling back to the status message."""
    if code in MESSAGES:
        return MESSAGES[code]
    if status in STATUS_MESSAGES:
        return STATUS_MESSAGES[status]
    return _GENERIC_5XX_MESSAGE if status >= 500 else _GENERIC_4XX_MESSAGE


def safe_field_errors(value: object) -> list[dict[str, str]] | None:
    """Keep only well-formed {field, code} items from a route detail (§3.2 item 2d)."""
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    kept: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        field, code = item.get("field"), item.get("code")
        if (
            isinstance(field, str)
            and 0 < len(field) <= _MAX_FIELD_LENGTH
            and isinstance(code, str)
            and code in FIELD_ERROR_CODES
        ):
            kept.append({"field": field, "code": code})
    return sorted(kept, key=lambda e: (e["field"], e["code"])) or None


def retry_after_seconds(headers: Mapping[str, str] | None) -> int | None:
    """Return the integer Retry-After value when the header is all digits."""
    if not headers:
        return None
    for key, value in headers.items():
        if key.lower() == "retry-after" and isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def build_error_body(
    *,
    status: int,
    code: str,
    request_id: str,
    field_errors: list[dict[str, str]] | None = None,
    current_version: int | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    """Build the CONV-1 envelope; all six §9.8 fields are always present."""
    body: dict[str, Any] = {
        "code": code,
        "message": message_for(status, code),
        "correlation_id": request_id,
        "retryable": status in {429, 502, 503, 504},
        "retry_after_seconds": retry_after,
        "field_errors": field_errors or None,
        "request_id": request_id,
    }
    if code == "STALE_REVISION" and type(current_version) is int:
        body["current_version"] = current_version
    return body


def normalize_http_error(
    status: int, detail: object, *, idempotency_header_present: bool
) -> tuple[int, str, list[dict[str, str]] | None, int | None]:
    """Normalize an HTTPException into (status, code, field_errors, current_version)."""
    detail_map: Mapping[str, Any] = detail if isinstance(detail, Mapping) else {}
    raw_code = _valid_code(detail_map.get("code"))
    field_errors = safe_field_errors(detail_map.get("field_errors"))
    current_version = detail_map.get("current_version")
    if status == 422 and (raw_code is None or raw_code in _VALIDATION_422_CODES):
        if raw_code == "IDEMPOTENCY_KEY_REQUIRED":
            field_errors = [
                {
                    "field": "Idempotency-Key",
                    "code": "INVALID_FORMAT" if idempotency_header_present else "REQUIRED",
                }
            ]
        return 400, "INVALID_REQUEST", field_errors, None
    code = map_code(status, raw_code)
    return status, code, field_errors, current_version if type(current_version) is int else None


__all__ = [
    "CONV1_PREFIXES",
    "FIELD_ERROR_CODES",
    "GENERIC_CODE_MAP",
    "KEPT_404_CODES",
    "LESSON_OCCURRENCES_BASE",
    "MESSAGES",
    "NOTIFICATIONS_BASE",
    "STATUS_DEFAULT_CODES",
    "STATUS_MESSAGES",
    "STATUS_MESSAGE_ONLY",
    "UPLOAD_SESSIONS_BASE",
    "build_error_body",
    "is_conv1_path",
    "map_code",
    "message_for",
    "normalize_http_error",
    "retry_after_seconds",
    "safe_field_errors",
]
