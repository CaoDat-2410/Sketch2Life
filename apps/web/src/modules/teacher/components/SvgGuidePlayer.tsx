import { useEffect, useRef, useState } from "react";
import type { SketchStrokeGuideV3, SvgDocumentV1 } from "../../../shared/api/teacherSvgCatalogApi";

export function revealedGuidePathIds(guide: SketchStrokeGuideV3, throughStep: number): string[] {
  const revealed = new Set<string>();
  guide.stages.slice(0, throughStep + 1).forEach((stage) => {
    const newPaths = new Set(stage.new_path_ids);
    stage.animation_order.forEach((pathId) => {
      if (newPaths.has(pathId)) revealed.add(pathId);
    });
  });
  return [...revealed];
}

export interface SvgGuidePlayerProps {
  guide: SketchStrokeGuideV3;
  document: SvgDocumentV1;
  onClose: () => void;
  onSkip?: () => void;
}

export function SvgGuidePlayer({ guide, document, onClose, onSkip }: SvgGuidePlayerProps) {
  const stages = guide.stages.slice(0, 8);
  const playerRef = useRef<HTMLDivElement>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const stage = stages[stepIndex];
  const revealedIds = revealedGuidePathIds(guide, stepIndex);
  const pathById = new Map(document.paths.map((path) => [path.path_id, path]));
  const revealedPaths = revealedIds.map((pathId) => pathById.get(pathId)).filter((path) => path !== undefined);
  const close = onSkip ?? onClose;

  useEffect(() => {
    playerRef.current?.focus();
  }, []);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setStepIndex((index) => Math.max(0, index - 1));
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        setStepIndex((index) => Math.min(stages.length - 1, index + 1));
      } else if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, stages.length]);

  if (stages.length === 0 || !stage) {
    return (
      <div ref={playerRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="svg-guide-player-title" style={overlayStyle}>
        <section style={playerStyle}>
          <h2 id="svg-guide-player-title">Chưa có bước hướng dẫn</h2>
          <button type="button" onClick={onClose} style={secondaryButton}>Đóng</button>
        </section>
      </div>
    );
  }

  return (
    <div data-s2l-presenting="true" ref={playerRef} tabIndex={-1} role="dialog" aria-modal="true" aria-labelledby="svg-guide-player-title" style={overlayStyle}>
      <section style={playerStyle}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 18 }}>
          <div>
            <p style={{ margin: "0 0 5px", color: "#627366", fontSize: 13, fontWeight: 700, letterSpacing: ".05em", textTransform: "uppercase" }}>Hướng dẫn vẽ · {stepIndex + 1}/{stages.length}</p>
            <h2 id="svg-guide-player-title" style={{ margin: 0, fontSize: 26 }}>{guide.title_vi}</h2>
          </div>
          <button type="button" onClick={onClose} aria-label="Đóng hướng dẫn" style={iconButton}>×</button>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))", gap: 24, alignItems: "center", flex: 1 }}>
          <div style={{ minHeight: 280, display: "grid", placeItems: "center", padding: 24, borderRadius: 22, border: "1px solid #d8e1d7", background: "radial-gradient(circle at 50% 42%, #fff 0 52%, #f2f7f1 100%)" }}>
            <svg data-testid="svg-guide-svg" viewBox={document.view_box} role="img" aria-label={guide.title_vi} style={{ width: "100%", maxWidth: 760, height: "min(60vh, 540px)", overflow: "visible", color: "#315f42" }}>
              {revealedPaths.map((path) => (
                <path
                  key={path.path_id}
                  data-path-id={path.path_id}
                  d={path.d}
                  fill={path.fill ?? "none"}
                  stroke={path.stroke ?? "currentColor"}
                  strokeWidth={path.stroke_width ?? 2}
                  vectorEffect="non-scaling-stroke"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ))}
            </svg>
          </div>
          <aside style={{ display: "grid", gap: 18, alignContent: "center" }}>
            <div>
              <p style={{ margin: "0 0 8px", color: "#607064", fontSize: 13, fontWeight: 700 }}>BƯỚC {stepIndex + 1}</p>
              <p aria-live="polite" style={{ margin: 0, fontSize: 25, lineHeight: 1.4, color: "#26372b" }}>{stage.instruction_vi}</p>
            </div>
            <div aria-label="Tiến độ hướng dẫn" style={{ display: "flex", gap: 7 }}>
              {stages.map((item, index) => (
                <span key={item.step_index} aria-current={index === stepIndex ? "step" : undefined} style={{ height: 7, flex: 1, borderRadius: 999, background: index <= stepIndex ? "#4f8563" : "#d9e2d8" }} />
              ))}
            </div>
          </aside>
        </div>

        <footer style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button type="button" onClick={close} style={secondaryButton}>Bỏ qua hướng dẫn</button>
          <div style={{ display: "flex", gap: 10 }}>
            <button type="button" disabled={stepIndex === 0} onClick={() => setStepIndex((index) => Math.max(0, index - 1))} style={secondaryButton}>← Trước</button>
            {stepIndex < stages.length - 1 ? (
              <button type="button" onClick={() => setStepIndex((index) => Math.min(stages.length - 1, index + 1))} style={primaryButton}>Tiếp →</button>
            ) : (
              <button type="button" onClick={onClose} style={primaryButton}>Hoàn tất</button>
            )}
          </div>
        </footer>
      </section>
    </div>
  );
}

const overlayStyle = {
  position: "fixed" as const,
  inset: 0,
  zIndex: 1000,
  padding: 20,
  display: "grid",
  placeItems: "center",
  background: "rgba(24, 34, 27, .72)",
};

const playerStyle = {
  width: "min(1200px, 100%)",
  minHeight: "min(760px, 92vh)",
  boxSizing: "border-box" as const,
  display: "flex",
  flexDirection: "column" as const,
  justifyContent: "space-between",
  gap: 22,
  padding: "clamp(20px, 4vw, 42px)",
  borderRadius: 24,
  background: "#fbfcf8",
  color: "#28342b",
  boxShadow: "0 30px 90px rgba(10, 20, 12, .35)",
};

const primaryButton = {
  border: 0,
  borderRadius: 999,
  padding: "12px 20px",
  background: "#315f42",
  color: "#fff",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButton = {
  border: "1px solid #cad7ca",
  borderRadius: 999,
  padding: "11px 18px",
  background: "#fff",
  color: "#2f4535",
  fontWeight: 700,
  cursor: "pointer",
};

const iconButton = {
  width: 42,
  height: 42,
  borderRadius: 999,
  border: "1px solid #cad7ca",
  background: "#fff",
  color: "#2f4535",
  fontSize: 26,
  lineHeight: 1,
  cursor: "pointer",
};
