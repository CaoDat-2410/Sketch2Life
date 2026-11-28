"""Vietnamese Parent and billing fixtures for the S13 whole-system seed stage."""

from __future__ import annotations

from typing import Final

from tools.seed import data, s12_story_v4a_data

CONSENT_POLICY_VERSION: Final[str] = "2026-11-parent-story-v1"
CONSENT_POLICY_TEXT: Final[str] = (
    "Thông tin hồ sơ do gia đình cung cấp được dùng để gợi ý hoạt động kể chuyện phù hợp với "
    "độ tuổi và mối quan tâm của trẻ. Phụ huynh có thể xem lại nội dung, lựa chọn thông tin "
    "chia sẻ với nhà trường và yêu cầu hỗ trợ về hồ sơ. Chính sách này cần được rà soát và "
    "phê duyệt trước khi áp dụng; hiện chưa ghi nhận sự đồng ý của phụ huynh."
)

PARENT_PROFILE_KEY: Final[str] = "k1"
PARENT_KEY: Final[str] = "p1"
PARENT_CONTEXT_ENTRY_TEXT: Final[str] = (
    "Mít thích kể tên những chiếc lá có màu sắc khác nhau sau giờ dạo sân trường."
)
PARENT_CONTEXT_ENTRY_SOURCE_KIND: Final[str] = "PARENT_NOTE"
PARENT_CONTEXT_ENTRY_IDEMPOTENCY_KEY: Final[str] = "seed:s13:parent-context-p1-k1"
PARENT_CONTEXT_REQUEST_ID: Final[str] = data.seed_uuid_text("s13:parent-context-request:p1-k1")

PARENT_SHARE_GRANTED_FIELDS: Final[tuple[str, ...]] = ("AGE_BAND", "DISPLAY_NAME")
PARENT_SHARE_IDEMPOTENCY_KEY: Final[str] = "seed:s13:parent-profile-share-p1-k1"

PARENT_FEEDBACK_LESSON_ID: Final[str] = s12_story_v4a_data.LESSON_ID
PARENT_FEEDBACK_SUBJECT: Final[str] = s12_story_v4a_data.PARENTS_BY_KEY["p6"].subject
PARENT_FEEDBACK_IDEMPOTENCY_KEY: Final[str] = "seed:s13:parent-feedback-p6-outdoor"
PARENT_FEEDBACK_TEXT: Final[str] = (
    "Bé thích quan sát tán lá xanh và kể lại màu sắc của từng chiếc lá. Gia đình mong bài học "
    "có thêm một câu hỏi gợi mở để bé chia sẻ điều mình phát hiện."
)

PARENT_QUOTA_UNITS: Final[int] = 2
# The demo Teacher gets enough video units to record a demo more than once.
ORGANIZATION_QUOTA_UNITS: Final[int] = 8
TEACHER_QUOTA_UNITS: Final[int] = 5
TEACHER_ALLOCATION_KEY: Final[str] = "seed:s13:teacher-quota-allocation-a1"

QUOTA_PRODUCTS: Final[tuple[dict[str, object], ...]] = (
    {
        "owner_kind": "PARENT_ACCOUNT",
        "display_name": "Gói 5 lượt tạo phim kể chuyện cho gia đình",
        "offer_kind": "TOP_UP",
        "cycle_months": None,
        "units": 5,
        "amount_vnd": 49_000,
    },
    {
        "owner_kind": "ORGANIZATION",
        "display_name": "Gói 20 lượt tạo phim kể chuyện cho nhà trường",
        "offer_kind": "TOP_UP",
        "cycle_months": None,
        "units": 20,
        "amount_vnd": 1_490_000,
    },
)

CAPACITY_PRICE: Final[dict[str, int]] = {
    "cycle_months": 12,
    "base_amount_vnd": 4_800_000,
    "slot_amount_vnd": 300_000,
}
CAPACITY_PRICE_KEY: Final[str] = "seed:s13:capacity-price-a"
CAPACITY_QUOTE_KEY: Final[str] = "seed:s13:capacity-quote-a"
CAPACITY_SETTLE_KEY: Final[str] = "seed:s13:capacity-settle-a"
CAPACITY_PAYMENT_EVENT_ID: Final[str] = data.seed_uuid_text("s13:capacity-payment-event-a")

BILLING_COMMAND_KEYS: Final[tuple[tuple[str, str], ...]] = (
    ("quota-product.save", "seed:s13:quota-product-parent"),
    ("quota-product.save", "seed:s13:quota-product-organization"),
    ("capacity.price", CAPACITY_PRICE_KEY),
    ("capacity.quote:new", CAPACITY_QUOTE_KEY),
    ("quota.allocate", TEACHER_ALLOCATION_KEY),
)

EXPECTED: Final[dict[str, int]] = {
    "parent_consent_policies": 1,
    "parent_profile_context_entries": 1,
    "parent_context_command_receipts": 1,
    "parent_profile_share_grants": 1,
    "parent_share_command_receipts": 1,
    "lesson_feedback_threads_s13": 1,
    "lesson_feedback_messages_s13": 1,
    "lesson_feedback_receipts_s13": 1,
    "notification_inbox_items_s13": 1,
    "core_audit_entries_s13": 3,
    "billing_video_quota_products": 2,
    "billing_offer_versions": 2,
    "billing_video_quota_product_events": 2,
    "billing_video_quota_grants_current_period": 2,
    "billing_video_quota_allocations": 1,
    "billing_video_quota_allocation_events": 1,
    "billing_capacity_price_versions": 1,
    "billing_invoices": 1,
    "billing_payment_events_sandbox": 1,
    "billing_organization_subscriptions": 1,
    "billing_subscription_events": 2,
    "billing_command_receipts_s13": 6,
    "billing_payment_attempts": 0,
    "billing_video_quota_usage": 0,
}


__all__ = [
    "BILLING_COMMAND_KEYS",
    "CAPACITY_PAYMENT_EVENT_ID",
    "CAPACITY_PRICE",
    "CAPACITY_PRICE_KEY",
    "CAPACITY_QUOTE_KEY",
    "CAPACITY_SETTLE_KEY",
    "CONSENT_POLICY_TEXT",
    "CONSENT_POLICY_VERSION",
    "EXPECTED",
    "ORGANIZATION_QUOTA_UNITS",
    "PARENT_CONTEXT_ENTRY_IDEMPOTENCY_KEY",
    "PARENT_CONTEXT_ENTRY_SOURCE_KIND",
    "PARENT_CONTEXT_ENTRY_TEXT",
    "PARENT_FEEDBACK_IDEMPOTENCY_KEY",
    "PARENT_FEEDBACK_LESSON_ID",
    "PARENT_FEEDBACK_SUBJECT",
    "PARENT_FEEDBACK_TEXT",
    "PARENT_CONTEXT_REQUEST_ID",
    "PARENT_KEY",
    "PARENT_PROFILE_KEY",
    "PARENT_QUOTA_UNITS",
    "PARENT_SHARE_GRANTED_FIELDS",
    "PARENT_SHARE_IDEMPOTENCY_KEY",
    "QUOTA_PRODUCTS",
    "TEACHER_ALLOCATION_KEY",
    "TEACHER_QUOTA_UNITS",
]
