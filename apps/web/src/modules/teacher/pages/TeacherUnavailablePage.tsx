import { FeatureAvailability, PageHeading } from "../../../shared/FeatureAvailability";

export type TeacherUnavailablePageProps = {
  title: string;
  summary: string;
  missing: string[];
  srsStep: string;
  nextTo?: string;
  nextLabel?: string;
};

export function TeacherUnavailablePage({ title, summary, missing, srsStep, nextTo = "/teacher/t02-lesson-authoring", nextLabel = "Mở học liệu" }: TeacherUnavailablePageProps) {
  return (
    <div className="s2l-page">
      <PageHeading eyebrow="Teacher · Theo yêu cầu sản phẩm" title={title} description={summary} />
      <FeatureAvailability
        title="Luồng này đang chờ API"
        summary={srsStep}
        requirement="Màn chỉ bật khi có contract versioned và quyền được backend xác minh."
        dependencies={missing}
        backTo={nextTo}
        backLabel={nextLabel}
      />
    </div>
  );
}
