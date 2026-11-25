import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";
import { teacherProfileApi } from "../../../shared/api/teacherProfileApi";
import type {
  Be1ProfileRevisionV1,
  ProfileEditRequestV1,
  SupportNeedsPutRequestV1,
} from "../../../shared/api/teacherProfileApi";
import {
  CLASS_READ_ONLY,
  NOT_FOUND_OR_NO_ACCESS,
  PROFILE_AGE_MONTHS,
  PROFILE_NAME_MAX,
  SYNTHETIC_NAME_PREFIX,
} from "../../../shared/api/teacherRosterApi";
import { FormField } from "../../../shared/ui";

const SUPPORT_UNAVAILABLE = "Mục này chưa khả dụng.";
const RETRY_LATER = "Chưa thể hoàn tất thao tác lúc này. Hãy thử lại sau.";
const PROFILE_EDIT_UNAVAILABLE = "Hồ sơ hiện chưa khả dụng để chỉnh sửa.";
const PROFILE_HISTORY_ERROR = "Không thể tải lịch sử hồ sơ lúc này.";
const SUPPORT_GENERIC_ERROR = "Không thể hoàn tất thao tác với mục này lúc này.";
const STALE_REVIEW = "Thông tin đã thay đổi. Đã tải bản mới nhất; hãy kiểm tra lại trước khi lưu.";
const DIAGNOSIS_INTEREST = "Sở thích không nên nêu chẩn đoán.";
const DIAGNOSIS_SUPPORT = "Thông tin hỗ trợ không nên nêu chẩn đoán.";
function hasControlCharacters(value: string, allowNewlineAndTab = false): boolean {
  return Array.from(value).some((character) => {
    const codePoint = character.codePointAt(0)!;
    if (allowNewlineAndTab && (codePoint === 0x09 || codePoint === 0x0a)) return false;
    return codePoint <= 0x1f || (codePoint >= 0x7f && codePoint <= 0x9f);
  });
}

type ApiFieldIssue = { field: string; code: string };
type ApiFailure = BackendApiError & { fieldErrors?: ApiFieldIssue[]; currentVersion?: number };

function apiFailure(cause: unknown): ApiFailure | null {
  return cause instanceof BackendApiError ? cause as ApiFailure : null;
}

function issueFor(cause: unknown, fields: string[]): ApiFieldIssue | undefined {
  return apiFailure(cause)?.fieldErrors?.find((issue) => fields.some((field) => (
    issue.field === field
    || issue.field.startsWith(`${field}.`)
    || issue.field.startsWith(`${field}[`)
  )));
}

function isRetryableOutcome(cause: unknown): boolean {
  const failure = apiFailure(cause);
  return Boolean(failure && (failure.status === 0 || failure.status === 408 || failure.status >= 500));
}

function profileFailureMessage(cause: unknown, editing = false): string {
  const failure = apiFailure(cause);
  if (!failure) return editing ? RETRY_LATER : PROFILE_HISTORY_ERROR;
  if (failure.status === 404 || failure.code === "RESOURCE_NOT_FOUND") return NOT_FOUND_OR_NO_ACCESS;
  if (failure.code === "CONSENT_NOT_EFFECTIVE") return PROFILE_EDIT_UNAVAILABLE;
  if (failure.code === "INVALID_STATE_TRANSITION") return CLASS_READ_ONLY;
  if (failure.status === 503 || failure.status === 0 || failure.status === 408) return RETRY_LATER;
  if (failure.status === 403) return "Tài khoản chưa được cấp quyền cho dữ liệu này.";
  if (failure.status === 400) return "Hãy kiểm tra các trường rồi thử lại.";
  return editing ? RETRY_LATER : PROFILE_HISTORY_ERROR;
}

function supportFailure(cause: unknown): { unavailable: boolean; retry: boolean; clear: boolean } {
  const failure = apiFailure(cause);
  const unavailable = Boolean(failure && (
    failure.status === 404
    || failure.status === 503
    || failure.code === "SUPPORT_NEEDS_UNAVAILABLE"
    || failure.code === "CONSENT_NOT_EFFECTIVE"
  ));
  return {
    unavailable,
    retry: unavailable,
    clear: Boolean(failure && (failure.status === 404 || failure.code === "CONSENT_NOT_EFFECTIVE")),
  };
}

function supportErrorMessage(cause: unknown): string {
  const failure = apiFailure(cause);
  if (!failure) return SUPPORT_GENERIC_ERROR;
  if (failure.code === "STALE_REVISION") return STALE_REVIEW;
  if (failure.code === "INVALID_STATE_TRANSITION") return CLASS_READ_ONLY;
  if (failure.status === 400) return "Hãy kiểm tra nội dung rồi thử lại.";
  if (failure.status === 403) return "Không thể truy cập mục này.";
  return SUPPORT_GENERIC_ERROR;
}

function utf8Length(value: string): number {
  return new TextEncoder().encode(value).length;
}

function characterLength(value: string): number {
  return Array.from(value).length;
}

function ageBandLabel(revision: Be1ProfileRevisionV1): string {
  if (!revision.age_band) return "Không có nhóm tuổi";
  const labels: Record<string, string> = {
    AGE_36_71: "36–71 tháng",
    AGE_72_107: "72–107 tháng",
    AGE_108_120: "108–120 tháng",
  };
  return labels[revision.age_band.band_code] ?? "Không có nhóm tuổi";
}

function createdAtLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Thời điểm không khả dụng";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function profileDraftProblem(
  name: string,
  ageText: string,
  interests: string[],
): { name?: string; age?: string; interests?: string } {
  const issues: { name?: string; age?: string; interests?: string } = {};
  if (
    !name.startsWith(SYNTHETIC_NAME_PREFIX)
    || characterLength(name) < 11
    || characterLength(name) > PROFILE_NAME_MAX
    || hasControlCharacters(name)
  ) issues.name = `Tên phải bắt đầu bằng “${SYNTHETIC_NAME_PREFIX}” và có từ 11 đến ${PROFILE_NAME_MAX} ký tự.`;
  const age = Number(ageText);
  if (!Number.isInteger(age) || age < PROFILE_AGE_MONTHS.min || age > PROFILE_AGE_MONTHS.max) {
    issues.age = `Tuổi phải từ ${PROFILE_AGE_MONTHS.min} đến ${PROFILE_AGE_MONTHS.max} tháng.`;
  }
  if (interests.length > 20) issues.interests = "Có thể thêm tối đa 20 sở thích.";
  else if (new Set(interests).size !== interests.length) issues.interests = "Mỗi sở thích chỉ được thêm một lần.";
  else if (interests.some((interest) => (
    characterLength(interest) < 1
    || characterLength(interest) > 80
    || utf8Length(interest) > 320
    || interest !== interest.trim()
    || interest !== interest.normalize("NFC")
    || hasControlCharacters(interest)
  ))) issues.interests = "Mỗi sở thích cần từ 1 đến 80 ký tự hợp lệ.";
  return issues;
}

function profileEditBody(
  head: Be1ProfileRevisionV1,
  name: string,
  ageText: string,
  interests: string[],
): ProfileEditRequestV1 | null {
  const body: ProfileEditRequestV1 = { expected_revision: head.revision_no };
  if (name !== head.display_name) body.display_name = name;
  const age = Number(ageText);
  if (age !== head.age_months) body.age_months = age;
  if (JSON.stringify(interests) !== JSON.stringify(head.structured_interests)) body.structured_interests = interests;
  return Object.keys(body).length > 1 ? body : null;
}

type PanelProps = {
  organizationId: string;
  classId: string;
  childId: string;
  canEdit: boolean;
  onProfileSaved: () => void;
  onClose: () => void;
};

function ProfileRevisionsPanel({ organizationId, classId, childId, canEdit, onProfileSaved, onClose }: PanelProps) {
  const [items, setItems] = useState<Be1ProfileRevisionV1[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [readError, setReadError] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [name, setName] = useState("");
  const [ageText, setAgeText] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [interestInput, setInterestInput] = useState("");
  const [nameIssue, setNameIssue] = useState<string | undefined>();
  const [ageIssue, setAgeIssue] = useState<string | undefined>();
  const [interestIssue, setInterestIssue] = useState<string | undefined>();
  const [editMessage, setEditMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [retryAvailable, setRetryAvailable] = useState(false);
  const pendingEdit = useRef<{ signature: string; key: string } | null>(null);
  const alive = useRef(true);

  const applyFirstPage = useCallback((page: { items: Be1ProfileRevisionV1[]; next_cursor: string | null }) => {
    setItems(page.items);
    setNextCursor(page.next_cursor);
    setReadError(null);
    const head = page.items[0];
    if (head) {
      setName(head.display_name);
      setAgeText(String(head.age_months));
      setInterests(head.structured_interests);
    }
  }, []);

  const loadFirstPage = useCallback(async () => {
    try {
      const page = await teacherProfileApi.listProfileRevisions(organizationId, classId, childId);
      if (alive.current) applyFirstPage(page);
      return page;
    } catch (cause) {
      if (alive.current) {
        setItems([]);
        setNextCursor(null);
        setReadError(profileFailureMessage(cause));
      }
      return null;
    } finally {
      if (alive.current) setLoading(false);
    }
  }, [applyFirstPage, childId, classId, organizationId]);

  useEffect(() => {
    alive.current = true;
    void loadFirstPage();
    return () => { alive.current = false; };
  }, [loadFirstPage]);

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return;
    const cursor = nextCursor;
    setLoadingMore(true);
    setReadError(null);
    try {
      const page = await teacherProfileApi.listProfileRevisions(organizationId, classId, childId, cursor);
      if (!alive.current) return;
      setItems((current) => {
        const seen = new Set(current.map((item) => item.profile_revision_id));
        return [...current, ...page.items.filter((item) => !seen.has(item.profile_revision_id))];
      });
      setNextCursor(page.next_cursor);
    } catch (cause) {
      if (alive.current) setReadError(profileFailureMessage(cause));
    } finally {
      if (alive.current) setLoadingMore(false);
    }
  };

  const head = items[0];
  const validation = profileDraftProblem(name, ageText, interests);
  const body = head ? profileEditBody(head, name, ageText, interests) : null;
  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!head || !canEdit || saving || !body) return;
    setNameIssue(validation.name);
    setAgeIssue(validation.age);
    setInterestIssue(validation.interests);
    setEditMessage(null);
    if (validation.name || validation.age || validation.interests) return;

    const signature = JSON.stringify(body);
    const key = pendingEdit.current?.signature === signature ? pendingEdit.current.key : createIdempotencyKey();
    pendingEdit.current = { signature, key };
    setSaving(true);
    try {
      await teacherProfileApi.editProfile(organizationId, classId, childId, body, key);
      if (!alive.current) {
        onProfileSaved();
        return;
      }
      pendingEdit.current = null;
      setRetryAvailable(false);
      setEditOpen(false);
      setEditMessage("Đã lưu phiên bản hồ sơ mới.");
      await loadFirstPage();
      if (alive.current) onProfileSaved();
    } catch (cause) {
      if (!alive.current) return;
      const failure = apiFailure(cause);
      if (failure?.code === "STALE_REVISION") {
        pendingEdit.current = null;
        setRetryAvailable(false);
        setLoading(true);
        const page = await loadFirstPage();
        if (!alive.current) return;
        if (page?.items[0]) {
          setEditOpen(true);
          setName(page.items[0].display_name);
          setAgeText(String(page.items[0].age_months));
          setInterests(page.items[0].structured_interests);
          setEditMessage(STALE_REVIEW);
        } else {
          setEditMessage(profileFailureMessage(cause, true));
        }
      } else if (failure?.status === 404 || failure?.code === "CONSENT_NOT_EFFECTIVE") {
        pendingEdit.current = null;
        setRetryAvailable(false);
        setItems([]);
        setNextCursor(null);
        setReadError(profileFailureMessage(cause, true));
        setEditOpen(false);
        setEditMessage(null);
      } else {
        const diagnosis = issueFor(cause, ["structured_interests"]);
        if (diagnosis?.code === "DIAGNOSIS_LIKE") setInterestIssue(DIAGNOSIS_INTEREST);
        if (!isRetryableOutcome(cause)) pendingEdit.current = null;
        setRetryAvailable(isRetryableOutcome(cause));
        setEditMessage(profileFailureMessage(cause, true));
        if (failure?.code === "INVALID_STATE_TRANSITION") onProfileSaved();
      }
    } finally {
      if (alive.current) setSaving(false);
    }
  };

  const setDraftChanged = (update: () => void) => {
    pendingEdit.current = null;
    setRetryAvailable(false);
    setEditMessage(null);
    update();
  };

  const addInterest = () => {
    const value = interestInput.trim().normalize("NFC");
    if (!value || characterLength(value) > 80 || utf8Length(value) > 320 || hasControlCharacters(value)) {
      setInterestIssue("Mỗi sở thích cần từ 1 đến 80 ký tự hợp lệ.");
      return;
    }
    if (interests.length >= 20) {
      setInterestIssue("Có thể thêm tối đa 20 sở thích.");
      return;
    }
    if (interests.includes(value)) {
      setInterestIssue("Mỗi sở thích chỉ được thêm một lần.");
      return;
    }
    setDraftChanged(() => {
      setInterests((current) => [...current, value]);
      setInterestInput("");
      setInterestIssue(undefined);
    });
  };

  return (
    <section className="s2l-data-card teacher-profile-panel" aria-label="Lịch sử hồ sơ">
      <div className="s2l-section-heading">
        <div><h3>Lịch sử hồ sơ</h3><p>Các phiên bản mới nhất hiển thị trước.</p></div>
        <button type="button" className="s2l-button" onClick={onClose}>Đóng</button>
      </div>
      {loading && <p role="status">Đang tải lịch sử hồ sơ…</p>}
      {readError && <p role="alert">{readError}</p>}
      {!loading && !readError && items.length === 0 && <p>Chưa có phiên bản hồ sơ.</p>}
      {!loading && !readError && items.map((revision) => (
        <article className="teacher-profile-revision" key={revision.profile_revision_id}>
          <h4>Phiên bản {revision.revision_no}</h4>
          <p><strong>{revision.display_name}</strong> · {revision.age_months} tháng · {ageBandLabel(revision)}</p>
          <p>Sở thích: {revision.structured_interests.length ? revision.structured_interests.join(", ") : "Chưa có"}</p>
          <p>Thời điểm: {createdAtLabel(revision.created_at)}</p>
        </article>
      ))}
      {nextCursor && !readError && <button type="button" className="s2l-button" disabled={loadingMore} onClick={() => void loadMore()}>
        {loadingMore ? "Đang tải…" : "Tải thêm"}
      </button>}
      {head && !editOpen && <button type="button" className="s2l-button" disabled={!canEdit || loading} onClick={() => {
        setName(head.display_name);
        setAgeText(String(head.age_months));
        setInterests(head.structured_interests);
        setEditMessage(null);
        setRetryAvailable(false);
        setEditOpen(true);
      }}>Sửa hồ sơ</button>}
      {editOpen && head && <form className="teacher-profile-edit" autoComplete="off" onSubmit={(event) => void saveProfile(event)}>
        <h4>Sửa hồ sơ</h4>
        <FormField label="Tên hiển thị" htmlFor={`profile-name-${childId}`} error={nameIssue}>
          <input
            id={`profile-name-${childId}`}
            className="cozy-input"
            value={name}
            disabled={saving}
            autoComplete="off"
            onChange={(event) => setDraftChanged(() => { setName(event.target.value); setNameIssue(undefined); })}
          />
        </FormField>
        <FormField label="Tuổi (tháng)" htmlFor={`profile-age-${childId}`} error={ageIssue}>
          <input
            id={`profile-age-${childId}`}
            className="cozy-input"
            type="number"
            min={PROFILE_AGE_MONTHS.min}
            max={PROFILE_AGE_MONTHS.max}
            step={1}
            value={ageText}
            disabled={saving}
            onChange={(event) => setDraftChanged(() => { setAgeText(event.target.value); setAgeIssue(undefined); })}
          />
        </FormField>
        <FormField label="Sở thích" htmlFor={`profile-interest-${childId}`} error={interestIssue}>
          <div className="teacher-profile-interest-entry">
            <input
              id={`profile-interest-${childId}`}
              className="cozy-input"
              value={interestInput}
              disabled={saving}
              autoComplete="off"
            onChange={(event) => setDraftChanged(() => { setInterestInput(event.target.value); setInterestIssue(undefined); })}
            onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); addInterest(); } }}
            />
            <button type="button" className="s2l-button" disabled={saving} onClick={addInterest}>Thêm sở thích</button>
          </div>
          <ul className="teacher-profile-interest-list">
            {interests.map((interest, index) => <li key={`${index}-${interest}`}>
              <span>{interest}</span>
              <button type="button" className="s2l-button" disabled={saving} aria-label={`Xóa sở thích: ${interest}`} onClick={() => setDraftChanged(() => setInterests((current) => current.filter((_, itemIndex) => itemIndex !== index)))}>Xóa</button>
            </li>)}
          </ul>
        </FormField>
        {editMessage && <p role="alert">{editMessage}</p>}
        <div className="cozy-form-actions">
          <button type="button" className="s2l-button" disabled={saving} onClick={() => { pendingEdit.current = null; setEditOpen(false); }}>Hủy</button>
          <button type="submit" className="s2l-button" disabled={saving || !canEdit || Boolean(validation.name || validation.age || validation.interests) || !body}>
            {saving ? "Đang lưu…" : retryAvailable ? "Thử lại cùng yêu cầu" : "Lưu thay đổi"}
          </button>
        </div>
      </form>}
    </section>
  );
}

type SupportView = "loading" | "value" | "empty" | "unavailable" | "error";

function supportNeedsProblem(category: string, note: string): { category?: string; note?: string; form?: string } {
  const issues: { category?: string; note?: string; form?: string } = {};
  if (characterLength(category) > 80 || utf8Length(category) > 320) issues.category = "Danh mục không được vượt quá giới hạn cho phép.";
  else if (hasControlCharacters(category, true)) issues.category = "Danh mục có ký tự không được hỗ trợ.";
  if (characterLength(note) > 2000 || utf8Length(note) > 8000) issues.note = "Ghi chú không được vượt quá giới hạn cho phép.";
  else if (hasControlCharacters(note, true)) issues.note = "Ghi chú có ký tự không được hỗ trợ.";
  if (!category.trim() && !note.trim()) issues.form = "Hãy nhập danh mục hoặc ghi chú trước khi lưu.";
  return issues;
}

function SupportNeedsPanel({ organizationId, classId, childId, canEdit, onClose }: PanelProps) {
  const [view, setView] = useState<SupportView>("loading");
  const [revision, setRevision] = useState(0);
  const [savedCategory, setSavedCategory] = useState<string | null>(null);
  const [savedNote, setSavedNote] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [note, setNote] = useState("");
  const [editOpen, setEditOpen] = useState(false);
  const [categoryIssue, setCategoryIssue] = useState<string | undefined>();
  const [noteIssue, setNoteIssue] = useState<string | undefined>();
  const [formIssue, setFormIssue] = useState<string | undefined>();
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retryAvailable, setRetryAvailable] = useState(false);
  const pendingPut = useRef<{ signature: string; key: string; body: SupportNeedsPutRequestV1 } | null>(null);
  const alive = useRef(true);

  const applySupportNeeds = useCallback((value: { revision: number; category: string | null; note: string | null }) => {
    setRevision(value.revision);
    setSavedCategory(value.category);
    setSavedNote(value.note);
    setCategory(value.category ?? "");
    setNote(value.note ?? "");
    setView(value.revision === 0 ? "empty" : "value");
    setMessage(null);
    setRetryAvailable(false);
  }, []);

  const loadSupportNeeds = useCallback(async () => {
    try {
      const value = await teacherProfileApi.getSupportNeeds(organizationId, classId, childId);
      if (alive.current) applySupportNeeds(value);
      return value;
    } catch (cause) {
      if (!alive.current) return null;
      const failure = supportFailure(cause);
      if (failure.unavailable) {
        setView("unavailable");
        setSavedCategory(null);
        setSavedNote(null);
        setRevision(0);
        if (failure.clear || !pendingPut.current) {
          setCategory("");
          setNote("");
          setEditOpen(false);
          if (failure.clear) pendingPut.current = null;
        }
        setRetryAvailable(failure.retry);
        setMessage(null);
      } else {
        setView("error");
        setMessage(supportErrorMessage(cause));
        setRetryAvailable(false);
      }
      return null;
    }
  }, [applySupportNeeds, childId, classId, organizationId]);

  useEffect(() => {
    alive.current = true;
    void loadSupportNeeds();
    return () => { alive.current = false; };
  }, [loadSupportNeeds]);

  const sendPendingPut = async () => {
    const pending = pendingPut.current;
    if (!pending || busy) return;
    setBusy(true);
    setMessage(null);
    try {
      await teacherProfileApi.putSupportNeeds(organizationId, classId, childId, pending.body, pending.key);
      if (!alive.current) return;
      pendingPut.current = null;
      setRetryAvailable(false);
      setEditOpen(false);
      setView("loading");
      const updated = await loadSupportNeeds();
      if (updated && alive.current) setMessage("Đã lưu nhu cầu hỗ trợ.");
    } catch (cause) {
      if (!alive.current) return;
      const failure = supportFailure(cause);
      if (failure.unavailable) {
        setView("unavailable");
        setSavedCategory(null);
        setSavedNote(null);
        setRevision(0);
        if (failure.clear) {
          pendingPut.current = null;
          setCategory("");
          setNote("");
          setEditOpen(false);
        }
        setRetryAvailable(failure.retry);
        setMessage(null);
      } else if (apiFailure(cause)?.code === "STALE_REVISION") {
        pendingPut.current = null;
        setView("loading");
        const latest = await loadSupportNeeds();
        if (latest && alive.current) {
          setEditOpen(true);
          setMessage(STALE_REVIEW);
        }
      } else {
        const categoryDiagnosis = issueFor(cause, ["category"])?.code === "DIAGNOSIS_LIKE";
        const noteDiagnosis = issueFor(cause, ["note"])?.code === "DIAGNOSIS_LIKE";
        if (categoryDiagnosis) setCategoryIssue(DIAGNOSIS_SUPPORT);
        if (noteDiagnosis) setNoteIssue(DIAGNOSIS_SUPPORT);
        if (!isRetryableOutcome(cause)) pendingPut.current = null;
        setRetryAvailable(isRetryableOutcome(cause));
        setMessage(supportErrorMessage(cause));
      }
    } finally {
      if (alive.current) setBusy(false);
    }
  };

  const saveSupportNeeds = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canEdit || busy || (view !== "value" && view !== "empty")) return;
    const issues = supportNeedsProblem(category, note);
    setCategoryIssue(issues.category);
    setNoteIssue(issues.note);
    setFormIssue(issues.form);
    setMessage(null);
    if (issues.category || issues.note || issues.form) return;
    const body: SupportNeedsPutRequestV1 = {
      expected_revision: revision,
      category,
      note,
    };
    const signature = JSON.stringify(body);
    const pending = pendingPut.current;
    const key = pending?.signature === signature ? pending.key : createIdempotencyKey();
    pendingPut.current = { signature, key, body };
    await sendPendingPut();
  };

  const onDraftChange = (update: () => void) => {
    pendingPut.current = null;
    setRetryAvailable(false);
    setMessage(null);
    update();
  };

  const openEditor = () => {
    setCategory(savedCategory ?? "");
    setNote(savedNote ?? "");
    setCategoryIssue(undefined);
    setNoteIssue(undefined);
    setFormIssue(undefined);
    setMessage(null);
    setEditOpen(true);
  };

  return (
    <section className="s2l-data-card teacher-support-needs-panel" aria-label="Nhu cầu hỗ trợ">
      <div className="s2l-section-heading">
        <div><h3>Nhu cầu hỗ trợ</h3><p>Thông tin chỉ hiển thị trong khi mục này đang mở.</p></div>
        <button type="button" className="s2l-button" onClick={onClose}>Đóng</button>
      </div>
      {view === "loading" && <p role="status">Đang tải mục này…</p>}
      {view === "unavailable" && <p role="status">{SUPPORT_UNAVAILABLE}</p>}
      {view === "error" && <p role="alert">{message ?? SUPPORT_GENERIC_ERROR}</p>}
      {(view === "empty" || view === "value") && <>
        <p>Phiên bản {revision}</p>
        {view === "empty"
          ? <p>Chưa có thông tin nhu cầu hỗ trợ.</p>
          : <div className="teacher-support-needs-value">
            <p><strong>Danh mục:</strong> {savedCategory ?? "—"}</p>
            <p><strong>Ghi chú:</strong> {savedNote ?? "—"}</p>
          </div>}
      </>}
      {message && view !== "error" && !editOpen && <p role="status">{message}</p>}
      {view === "unavailable" && retryAvailable && <button type="button" className="s2l-button" disabled={busy} onClick={() => {
        if (pendingPut.current) void sendPendingPut();
        else { setView("loading"); void loadSupportNeeds(); }
      }}>{busy ? "Đang thử lại…" : "Thử lại"}</button>}
      {(view === "empty" || view === "value") && !editOpen && <button type="button" className="s2l-button" disabled={!canEdit} onClick={openEditor}>Sửa nhu cầu hỗ trợ</button>}
      {editOpen && (view === "empty" || view === "value") && <form className="teacher-support-needs-edit" autoComplete="off" onSubmit={(event) => void saveSupportNeeds(event)}>
        <FormField label="Danh mục" htmlFor={`support-category-${childId}`} error={categoryIssue}>
          <input
            id={`support-category-${childId}`}
            className="cozy-input"
            value={category}
            disabled={busy}
            autoComplete="off"
            onChange={(event) => onDraftChange(() => { setCategory(event.target.value); setCategoryIssue(undefined); setFormIssue(undefined); })}
          />
        </FormField>
        <FormField label="Ghi chú" htmlFor={`support-note-${childId}`} error={noteIssue}>
          <textarea
            id={`support-note-${childId}`}
            className="cozy-input"
            value={note}
            disabled={busy}
            autoComplete="off"
            onChange={(event) => onDraftChange(() => { setNote(event.target.value); setNoteIssue(undefined); setFormIssue(undefined); })}
          />
        </FormField>
        {formIssue && <p role="alert">{formIssue}</p>}
        {message && <p role="alert">{message}</p>}
        <div className="cozy-form-actions">
          <button type="button" className="s2l-button" disabled={busy} onClick={() => { pendingPut.current = null; setEditOpen(false); setCategory(savedCategory ?? ""); setNote(savedNote ?? ""); }}>Hủy</button>
          <button type="submit" className="s2l-button" disabled={busy || !canEdit}>
            {busy ? "Đang lưu…" : retryAvailable ? "Thử lại cùng yêu cầu" : "Lưu nhu cầu hỗ trợ"}
          </button>
        </div>
      </form>}
    </section>
  );
}

export function TeacherProfilePanels({ organizationId, classId, childId, canEdit, onProfileSaved }: Omit<PanelProps, "onClose">) {
  const [open, setOpen] = useState<"revisions" | "support" | null>(null);
  return (
    <div className="teacher-profile-panels">
      <div className="teacher-profile-panel-actions">
        <button type="button" className="s2l-button" aria-expanded={open === "revisions"} onClick={() => setOpen((current) => current === "revisions" ? null : "revisions")}>Lịch sử hồ sơ</button>
        <button type="button" className="s2l-button" aria-expanded={open === "support"} onClick={() => setOpen((current) => current === "support" ? null : "support")}>Nhu cầu hỗ trợ</button>
      </div>
      {open === "revisions" && <ProfileRevisionsPanel
        key={`${childId}-revisions`}
        organizationId={organizationId}
        classId={classId}
        childId={childId}
        canEdit={canEdit}
        onProfileSaved={onProfileSaved}
        onClose={() => setOpen(null)}
      />}
      {open === "support" && <SupportNeedsPanel
        key={`${childId}-support`}
        organizationId={organizationId}
        classId={classId}
        childId={childId}
        canEdit={canEdit}
        onProfileSaved={onProfileSaved}
        onClose={() => setOpen(null)}
      />}
    </div>
  );
}
