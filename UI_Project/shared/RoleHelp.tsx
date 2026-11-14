import * as React from "react";
import { AccessibleDialog, Accordion, AccordionContent, AccordionHeader, AccordionItem, AccordionTrigger } from "./ui";

type PortalRole = "TEACHER" | "MANAGER" | "ADMIN";
type HelpEntry = { question: string; answer: string };

const HELP_CONTENT: Record<PortalRole, { title: string; intro: string; entries: HelpEntry[] }> = {
  TEACHER: {
    title: "Trợ giúp Giáo viên",
    intro: "Hướng dẫn nhanh cho các việc thường làm trong lớp.",
    entries: [
      { question: "Bắt đầu một buổi học ở đâu?", answer: "Chọn lớp và giáo án, kiểm tra hoạt động rồi mở màn chiếu. Có thể quay lại để đổi nội dung trước khi bắt đầu." },
      { question: "Tạo video mẫu cần những gì?", answer: "Chọn học sinh đại diện, hoạt động và bức vẽ; xem lại kịch bản trước khi tạo. Màn hình sẽ báo rõ khi cần thử lại hoặc khi đã hết lượt." },
      { question: "Không thấy lớp hoặc học sinh?", answer: "Kiểm tra lớp đang chọn. Nếu lớp vẫn chưa xuất hiện, nhờ Quản lý trường kiểm tra phân công." },
    ],
  },
  MANAGER: {
    title: "Trợ giúp Quản lý trường",
    intro: "Các bước nhanh để duyệt giáo án và quản lý lớp.",
    entries: [
      { question: "Duyệt giáo án công khai thế nào?", answer: "Mở hàng chờ, xem nội dung và đánh dấu đủ bốn tiêu chí. Chọn phạm vi công khai trước khi duyệt; khi yêu cầu chỉnh sửa, ghi rõ nội dung cần bổ sung." },
      { question: "Thêm hoặc kiểm tra lớp ở đâu?", answer: "Mở mục Lớp & chỗ học để xem danh sách hoặc tạo lớp. Giáo viên và nhóm phụ huynh nằm trong mục Giáo viên & nhóm." },
      { question: "Lượt tạo video được quản lý ở đâu?", answer: "Mở mục Lượt tạo để xem hạn mức và phần đã sử dụng." },
    ],
  },
  ADMIN: {
    title: "Trợ giúp Quản trị nền tảng",
    intro: "Lối tắt cho kiểm duyệt và theo dõi dịch vụ.",
    entries: [
      { question: "Ẩn hoặc hiện lại giáo án ở đâu?", answer: "Mở Thư viện bài học, chọn giáo án và kiểm tra nội dung. Khi ẩn, nhập lý do để người gửi biết cần sửa gì." },
      { question: "Kiểm tra trạng thái dịch vụ thế nào?", answer: "Mở Tổng quan rồi chọn Kiểm tra lại để cập nhật trạng thái các dịch vụ hệ thống." },
      { question: "Vì sao một số mục chưa có dữ liệu?", answer: "Dữ liệu chỉ hiển thị theo phạm vi phân quyền và trạng thái hoạt động của từng tổ chức." },
    ],
  },
};

export function RoleHelp({ role }: { role: PortalRole }) {
  const [open, setOpen] = React.useState(false);
  const content = HELP_CONTENT[role];

  return (
    <>
      <button
        type="button"
        className="s2l-help-open"
        aria-label={`Mở ${content.title.toLowerCase()}`}
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
          <circle cx="10" cy="10" r="7.2" fill="none" stroke="currentColor" strokeWidth="1.7" />
          <path d="M7.9 7.4a2.2 2.2 0 1 1 3.5 1.8c-.9.6-1.4 1-1.4 2.1M10 14.1h.01" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
        <span className="s2l-help-label">Trợ giúp</span>
      </button>
      <AccessibleDialog
        open={open}
        onOpenChange={setOpen}
        title={content.title}
        description={content.intro}
        className="s2l-help-dialog"
      >
        <header className="s2l-help-head">
          <h2>{content.title}</h2>
          <p>{content.intro}</p>
        </header>
        <Accordion type="single" collapsible className="s2l-help-list">
          {content.entries.map((entry, index) => (
            <AccordionItem key={entry.question} value={`help-${index}`} className="s2l-accordion-item">
              <AccordionHeader>
                <AccordionTrigger className="s2l-accordion-trigger">
                  <span>{entry.question}</span>
                  <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                    <path d="m5 7.5 5 5 5-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </AccordionTrigger>
              </AccordionHeader>
              <AccordionContent className="s2l-accordion-content"><div>{entry.answer}</div></AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </AccessibleDialog>
    </>
  );
}
