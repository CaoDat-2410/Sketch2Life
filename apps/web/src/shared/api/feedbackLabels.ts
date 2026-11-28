export type FeedbackAuthorRole = "parent" | "teacher" | "school_manager" | "platform_admin" | "other";

const FEEDBACK_ROLE_LABELS: Record<FeedbackAuthorRole, string> = {
  parent: "Phụ huynh",
  teacher: "Giáo viên",
  school_manager: "Quản lý trường",
  platform_admin: "Quản trị viên nền tảng",
  other: "Người tham gia",
};

export function feedbackAuthorRole(value: unknown): FeedbackAuthorRole {
  return value === "parent" || value === "teacher" || value === "school_manager" || value === "platform_admin"
    ? value
    : "other";
}

export function feedbackDisplayName(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const name = value.trim();
  return name && !name.includes("@") ? name : null;
}

export function feedbackAuthorLabel(
  role: unknown,
  displayName: unknown,
  fromYou: boolean,
): string {
  const roleLabel = FEEDBACK_ROLE_LABELS[feedbackAuthorRole(role)];
  if (fromYou) return `Bạn · ${roleLabel}`;
  const name = feedbackDisplayName(displayName);
  return name ? `${name} · ${roleLabel}` : roleLabel;
}
