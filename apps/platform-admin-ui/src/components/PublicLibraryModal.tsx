import React, { useEffect, useState } from "react";
import { TeacherLessonCard } from "../data/mockTeacherData";
import { Icon, IconName } from "./Icon";

export function topicIconName(topic: string): IconName {
  const lower = topic.toLowerCase();
  if (lower.includes("cây") || lower.includes("lá") || lower.includes("thực vật")) return "leaf";
  if (lower.includes("mưa") || lower.includes("mây") || lower.includes("nắng") || lower.includes("mặt trời")) return "sun";
  if (lower.includes("hoa")) return "star";
  if (lower.includes("đại dương") || lower.includes("cá") || lower.includes("biển")) return "sparkle";
  if (lower.includes("bướm") || lower.includes("động vật")) return "palette";
  return "book";
}

export function topicTone(topic: string): "" | "is-mint" | "is-amber" | "is-rose" {
  const lower = topic.toLowerCase();
  if (lower.includes("cây") || lower.includes("lá")) return "is-mint";
  if (lower.includes("hoa") || lower.includes("nắng")) return "is-amber";
  if (lower.includes("bướm")) return "is-rose";
  return "";
}

interface PublicLibraryModalProps {
  open: boolean;
  onClose: () => void;
  templates: TeacherLessonCard[];
  onSelectTemplate: (template: TeacherLessonCard) => void;
  primaryActionLabel?: string;
}

export function PublicLibraryModal({
  open,
  onClose,
  templates,
  onSelectTemplate,
  primaryActionLabel = "Nạp mẫu vào Giáo án",
}: PublicLibraryModalProps) {
  const [search, setSearch] = useState("");
  const [topicFilter, setTopicFilter] = useState("Tất cả");
  const [detailItem, setDetailItem] = useState<TeacherLessonCard | null>(null);

  useEffect(() => {
    if (!open) {
      setDetailItem(null);
      return;
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (detailItem) setDetailItem(null);
        else onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, detailItem, onClose]);

  if (!open) return null;

  const topics = ["Tất cả", ...Array.from(new Set(templates.map((t) => t.topic)))];
  const q = search.trim().toLowerCase();
  const filtered = templates.filter((t) => {
    const matchTopic = topicFilter === "Tất cả" || t.topic === topicFilter;
    const matchSearch =
      !q ||
      t.title.toLowerCase().includes(q) ||
      t.topic.toLowerCase().includes(q) ||
      t.description.toLowerCase().includes(q) ||
      t.objectives.toLowerCase().includes(q);
    return matchTopic && matchSearch;
  });

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="pub-lib-modal-title"
      className="tw-modal-backdrop"
      onClick={onClose}
    >
      <div className="tw-modal is-xl" onClick={(e) => e.stopPropagation()}>
        <div className="tw-row tw-between tw-wrap">
          <div className="tw-row">
            <span className="tw-ico is-amber" aria-hidden="true">
              <Icon name="star" size={22} />
            </span>
            <div>
              <h2 id="pub-lib-modal-title" style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>
                {detailItem ? detailItem.title : "Thư viện giáo án công khai"}
              </h2>
              <p className="tw-meta" style={{ marginTop: 2 }}>
                {detailItem
                  ? "Xem chi tiết mục tiêu sư phạm và danh sách hoạt động trước khi nạp mẫu."
                  : "Chọn một giáo án mẫu đã kiểm duyệt an toàn để nạp toàn bộ nội dung vào trình soạn thảo."}
              </p>
            </div>
          </div>
          <button
            type="button"
            className="tw-btn is-ghost is-sm"
            aria-label="Đóng thư viện công khai"
            onClick={onClose}
          >
            <Icon name="close" size={16} /> Đóng
          </button>
        </div>

        {detailItem ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="tw-row tw-wrap">
              <span className="tw-chip">{detailItem.topic}</span>
              <span className="tw-chip is-mint">{detailItem.ageBand}</span>
              <span className="tw-chip is-gray">{detailItem.version}</span>
              <span className="tw-chip is-amber">{detailItem.activities.length} hoạt động</span>
            </div>

            <div className="tw-item is-sky" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Mô tả tổng quan bài học</h3>
              <p style={{ fontSize: 15, lineHeight: 1.55 }}>{detailItem.description}</p>
            </div>

            <div className="tw-item is-mint" style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Mục tiêu sư phạm</h3>
              <p style={{ fontSize: 15, lineHeight: 1.55 }}>{detailItem.objectives}</p>
            </div>

            <div className="tw-item" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
                Danh sách hoạt động trên lớp ({detailItem.activities.length})
              </h3>
              {detailItem.activities.map((act, idx) => (
                <div key={act + idx} className="tw-row" style={{ alignItems: "flex-start", gap: 10 }}>
                  <span className="tw-chip is-mint">Bước {idx + 1}</span>
                  <span style={{ fontSize: 15, lineHeight: 1.5 }}>{act}</span>
                </div>
              ))}
            </div>

            <div className="tw-row tw-between tw-wrap" style={{ marginTop: 4 }}>
              <button
                type="button"
                className="tw-btn is-ghost"
                onClick={() => setDetailItem(null)}
              >
                <Icon name="arrow-left" size={16} /> Quay lại danh sách mẫu
              </button>
              <button
                type="button"
                className="tw-btn"
                onClick={() => {
                  onSelectTemplate(detailItem);
                }}
              >
                <Icon name="plus" size={18} /> {primaryActionLabel}
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="tw-row tw-wrap" style={{ gap: 10 }}>
              <div style={{ flex: 1, minWidth: 220, position: "relative" }}>
                <input
                  className="tw-input"
                  placeholder="Tìm mẫu giáo án theo tên, chủ đề, mục tiêu..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  aria-label="Tìm kiếm giáo án mẫu"
                />
              </div>
              <div className="tw-row tw-wrap" style={{ gap: 6 }}>
                {topics.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={"tw-chip " + (topicFilter === t ? "" : "is-gray")}
                    style={{ cursor: "pointer", fontFamily: "inherit" }}
                    onClick={() => setTopicFilter(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="tw-grid-2" style={{ gap: 14 }}>
              {filtered.map((tpl) => (
                <div
                  key={tpl.id}
                  className="tw-item"
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                    padding: 18,
                    borderRadius: 20,
                  }}
                >
                  <div className="tw-row tw-between">
                    <div className="tw-row" style={{ gap: 12 }}>
                      <span className={`tw-ico ${topicTone(tpl.topic)}`} aria-hidden="true">
                        <Icon name={topicIconName(tpl.topic)} size={22} />
                      </span>
                      <div>
                        <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>{tpl.title}</h3>
                        <div className="tw-meta" style={{ fontSize: 13 }}>
                          {tpl.authorName ?? "Thư viện Sketch2Life"} · {tpl.version}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="tw-row tw-wrap" style={{ gap: 6 }}>
                    <span className="tw-chip">{tpl.topic}</span>
                    <span className="tw-chip is-mint">{tpl.ageBand}</span>
                    <span className="tw-chip is-amber">{tpl.activities.length} hoạt động</span>
                  </div>

                  <p style={{ fontSize: 14.5, lineHeight: 1.5 }}>{tpl.description}</p>

                  <div className="tw-meta" style={{ fontSize: 13.5 }}>
                    <strong className="tw-strong">Mục tiêu:</strong> {tpl.objectives}
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{ fontSize: 13, fontWeight: 700 }}>Hoạt động tiêu biểu:</div>
                    {tpl.activities.slice(0, 3).map((a, idx) => (
                      <div key={a + idx} className="tw-meta" style={{ fontSize: 13 }}>
                        • {a}
                      </div>
                    ))}
                    {tpl.activities.length > 3 && (
                      <div className="tw-meta" style={{ fontSize: 12.5 }}>
                        + {tpl.activities.length - 3} hoạt động khác...
                      </div>
                    )}
                  </div>

                  <div className="tw-row tw-between tw-wrap" style={{ marginTop: "auto", paddingTop: 6, gap: 8 }}>
                    <button
                      type="button"
                      className="tw-btn is-ghost is-sm"
                      onClick={() => setDetailItem(tpl)}
                    >
                      <Icon name="eye" size={16} /> Xem chi tiết
                    </button>
                    <button
                      type="button"
                      className="tw-btn is-sm"
                      onClick={() => onSelectTemplate(tpl)}
                    >
                      <Icon name="plus" size={16} /> {primaryActionLabel}
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {filtered.length === 0 && (
              <p className="tw-sub" style={{ textAlign: "center", padding: 20 }}>
                Không tìm thấy giáo án mẫu khớp từ khóa tìm kiếm.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
