import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SketchStrokeGuideV3, SvgDocumentV1 } from "../../../../shared/api/teacherSvgCatalogApi";
import { revealedGuidePathIds, SvgGuidePlayer } from "../SvgGuidePlayer";

afterEach(cleanup);

const guide: SketchStrokeGuideV3 = {
  schema_version: "SketchStrokeGuideV3",
  guide_id: "cat",
  title_vi: "Vẽ con mèo",
  source_asset_ref: "catalog/cat",
  source_asset_version: 1,
  source_sha256: "a".repeat(64),
  parts: [{ part_id: "body", label_vi: "Thân", path_ids: ["p1", "p2", "p3", "p4"], depends_on: [] }],
  stages: [
    { step_index: 1, instruction_vi: "Vẽ đầu.", part_ids: ["body"], new_path_ids: ["p2", "p1"], animation_order: ["p1", "p2"] },
    { step_index: 2, instruction_vi: "Thêm thân.", part_ids: ["body"], new_path_ids: ["p3"], animation_order: ["p3"] },
    { step_index: 3, instruction_vi: "Thêm chân.", part_ids: ["body"], new_path_ids: ["p4"], animation_order: ["p4"] },
    { step_index: 4, instruction_vi: "Hoàn tất.", part_ids: ["body"], new_path_ids: ["p4"], animation_order: ["p4"] },
  ],
};

const document: SvgDocumentV1 = {
  schema_version: "SvgDocumentV1",
  view_box: "0 0 100 100",
  paths: ["p1", "p2", "p3", "p4"].map((path_id) => ({
    path_id, d: "M 0 0 L 10 10", fill: "none", stroke: "#345", stroke_width: 2,
  })),
};

describe("SvgGuidePlayer", () => {
  it("reveals paths cumulatively in each stage's animation order", () => {
    expect(revealedGuidePathIds(guide, 0)).toEqual(["p1", "p2"]);
    expect(revealedGuidePathIds(guide, 1)).toEqual(["p1", "p2", "p3"]);

    render(<SvgGuidePlayer guide={guide} document={document} onClose={vi.fn()} />);
    const svg = screen.getByTestId("svg-guide-svg");
    expect(svg.querySelectorAll("path")).toHaveLength(2);
    expect(svg.querySelector('path[data-path-id="p1"]')).toBeTruthy();
    expect(svg.querySelector('path[data-path-id="p2"]')).toBeTruthy();
    expect(screen.getByText("Vẽ đầu.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Tiếp →" }));
    expect(screen.getByText("Thêm thân.")).toBeTruthy();
    expect(svg.querySelectorAll("path")).toHaveLength(3);
  });

  it("supports keyboard step changes, previous, and skip", () => {
    const onClose = vi.fn();
    const onSkip = vi.fn();
    render(<SvgGuidePlayer guide={guide} document={document} onClose={onClose} onSkip={onSkip} />);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(screen.getByText("Thêm thân.")).toBeTruthy();
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(screen.getByText("Vẽ đầu.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Bỏ qua hướng dẫn" }));
    expect(onSkip).toHaveBeenCalledOnce();
    expect(onClose).not.toHaveBeenCalled();
  });
});
