import {
  backendRequest,
  createIdempotencyKey,
} from "../../../shared/api/backendApi";

export const ADMIN = "/api/platform-admin/v1";
export type Page<T> = {
  items: T[];
  total?: number;
  unread_count?: number;
  limit?: number;
  next_cursor?: string | null;
};
export type Organization = {
  organization_id: string;
  display_name: string;
  state: string;
  revision: number;
};
export type OrganizationSummary = {
  total: number;
  active: number;
  paused: number;
  disabled: number;
  other: number;
};
export type Grant = {
  permission: string;
  active: boolean;
  effective?: boolean;
  revision: number;
};
export type AdminSession = { account_id: string; items: Grant[] };
export type Preferences = {
  locale: "vi-VN" | "en-US";
  email_notifications: boolean;
  revision: number;
};
export type Settings = {
  environment: string;
  real_payments_enabled: boolean;
  billing_sandbox_enabled: boolean;
  smtp_configured: boolean;
  preferences: Preferences;
};
export type Operation = { state: string; count: number; job_type?: string };
export type DependencyHealth = { status: "healthy" | "unavailable" | "not_configured"; response_ms: number | null };
export type Operations = {
  database: DependencyHealth;
  broker: DependencyHealth & {
    queue_count: number | null;
    transport_pending_count: number | null;
    active_workers: number | null;
  };
  queue: {
    queued_jobs: number;
    running_jobs: number;
    failed_jobs: number;
    oldest_queued_at: string | null;
    last_dispatched_at: string | null;
    last_started_at: string | null;
    last_finished_at: string | null;
  };
  jobs: Operation[];
  core_outbox: Operation[];
  email: Operation[];
  lifecycle: Operation[];
};
export type AuditRetention = {
  retention_days: number | null;
  revision: number;
  updated_by: string;
  updated_at: string;
  total_entries: number;
  eligible_count: number;
  oldest_entry_at: string | null;
  newest_entry_at: string | null;
  last_purged_at: string | null;
  last_purged_count: number;
};
export type AuditRetentionPreview = {
  retention_days: number | null;
  policy_revision: number;
  cutoff: string | null;
  candidate_count: number;
  batch_count: number;
  batch_limit: number;
  oldest_candidate_at: string | null;
};
export type Audit = {
  audit_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  actor_ref?: string | null;
  organization_id: string;
  created_at: string;
  decision: string;
};
export type Lifecycle = {
  request_id: string;
  request_type: string;
  organization_id: string;
  state: string;
  unresolved_items: number;
  created_at: string;
  completed_at: string | null;
};
export type Inbox = {
  item_id: string;
  kind: string;
  is_read: boolean;
  created_at: string;
};
export type Delivery = {
  delivery_id: string;
  template: string;
  state: string;
  attempts: number;
  failure_code?: string | null;
  created_at: string;
};
export type Activity = {
  title: string;
  objective: string;
  instructions_text: string;
  materials_text?: string;
  preparation_text?: string;
  observation_notes?: string;
  safety_notes?: string;
  activity_kind?: "outdoor" | "indoor" | "mixed";
};
export type LessonContent = {
  locale: "vi-VN";
  title: string;
  topic: string;
  target_age_band_ref: string;
  target_age_band_version: number;
  objectives: string[];
  drawing_subject: string;
  drawing_steps_text: string;
  subject_learning_notes: string;
  activities: Activity[];
};
export type Lesson = {
  lesson_id: string;
  revision: number;
  version_id: string;
  version_no: number;
  content_hash: string;
  review_state: string;
  visibility: string;
  moderation_state: string;
  is_published_version: boolean;
  is_author: boolean;
  content: LessonContent;
  reviews: { review_id: string; decision: string; reason: string | null }[];
};
export type Catalog = {
  record_id: string;
  revision: number;
  version: number;
  content_hash: string;
  state: string;
  is_author: boolean;
  content: {
    activity: Activity;
    age_band: string;
    age_band_version: number;
    provenance: string;
  };
  reviews: { review_id: string; dimension: string; decision: string }[];
};
export type Invoice = {
  invoice_id: string;
  owner_kind: string;
  owner_ref: string;
  offer_id: string;
  units: number;
  amount_vnd: number;
  state: string;
  revision: number;
};
export type Offer = {
  offer_id: string;
  owner_kind: string;
  units: number;
  amount_vnd: number;
};
export type Quota = {
  available_units: number;
  owner_kind: string;
  owner_ref: string;
  grants: {
    grant_id: string;
    kind: string;
    units: number;
    used: number;
    expires_at: string | null;
  }[];
};
export type Subscription = {
  subscription_id: string;
  organization_ref: string;
  capacity: number;
  addon_slots: number;
  revision: number;
  state: string;
  period_end: string;
  scheduled_addon_slots: number | null;
  suspended_class_refs: string[];
};
export type Feedback = {
  thread_id: string;
  lesson_id: string;
  revision: number;
  created_at: string;
};
export type Thread = {
  thread_id: string;
  revision: number;
  limit?: number;
  next_cursor?: string | null;
  lesson_id: string;
  items: {
    message_id: string;
    body: string;
    from_you: boolean;
    created_at: string;
  }[];
};

export function read<T>(path: string) {
  return backendRequest<T>(ADMIN + path);
}
export async function readAllPages<T>(path: string, pageSize = 100): Promise<Page<T>> {
  const items: T[] = [];
  const seen = new Set<string>();
  let cursor: string | undefined;
  let total = 0;
  do {
    const page = await read<Page<T>>(path + query({ limit: pageSize, cursor }));
    items.push(...page.items);
    total = page.total ?? items.length;
    cursor = page.next_cursor ?? undefined;
    if (cursor && seen.has(cursor)) throw new Error("Danh sách trả về cursor phân trang bị lặp.");
    if (cursor) seen.add(cursor);
  } while (cursor);
  return { items, total };
}
export function query(values: Record<string, string | number | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  return "?" + params.toString();
}
// A retry of the same command retains its key, including after a network timeout.
export function commandClient() {
  const keys = new Map<string, string>();
  return async <T>(
    path: string,
    body: unknown = {},
    revision?: number,
    method = "POST",
  ) => {
    const signature = JSON.stringify([path, body, revision, method]);
    const key = keys.get(signature) ?? createIdempotencyKey();
    keys.set(signature, key);
    const result = await backendRequest<T>(ADMIN + path, {
      method,
      body: JSON.stringify(body),
      headers: {
        "Idempotency-Key": key,
        ...(revision === undefined ? {} : { "If-Match": `"${revision}"` }),
      },
    });
    // A confirmed success completes this intent; another click is a new command.
    keys.delete(signature);
    return result;
  };
}
