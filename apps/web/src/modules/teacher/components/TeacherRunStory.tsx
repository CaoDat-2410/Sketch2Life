import { useId, useState } from "react";
import { FormField } from "../../../shared/ui";
import { teacherRunApi, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { FormActionBar } from "./FormActionBar";
import { storyVideoCopy as text } from "../services/teacherRunCopy";
import { canRewrite, validHint } from "../services/teacherStoryVideo";

interface Props {
  run: TeacherRun;
  execute: (fingerprint: unknown[], action: (key: string) => Promise<unknown>) => Promise<void>;
  planFenced?: boolean;
}

export function TeacherRunStory({ run, execute, planFenced = false }: Props) {
  const hintId = useId();
  const [hint, setHint] = useState("");
  const [invalid, setInvalid] = useState(false);
  if (run.story_revision_no === null || !run.story) return null;
  const story = run.story;
  const revision = run.story_revision_no;
  const hash = run.story_sha256;
  const showRewrite = !planFenced && canRewrite(run);
  const showConfirm = !planFenced && run.story_status === "DRAFT" && !!hash;
  const showConfirmAgain = !planFenced && run.story_status !== "DRAFT" && run.story_confirmation_required === true && ["SCRIPT_REVIEW", "SAFETY_BLOCKED"].includes(run.run_state) && !!hash;

  function rewrite() {
    if (!validHint(hint)) { setInvalid(true); return; }
    setInvalid(false);
    const value = hint.trim() || undefined;
    void execute(["rewrite", run.run_id, revision, hash, value], (key) => teacherRunApi.rewrite(run.run_id, revision, hash ?? undefined, value, key));
  }
  function confirm() {
    if (!hash) return;
    void execute(["confirmStory", run.run_id, revision, hash], (key) => teacherRunApi.confirmStory(run.run_id, revision, hash, key));
  }
  function confirmAgain() {
    if (!hash) return;
    void execute(["confirmStoryAgain", run.run_id, revision, hash], (key) => teacherRunApi.confirmStory(run.run_id, revision, hash, key));
  }

  return (
    <section className="cozy-form-section cozy-form-stack tp-run-section">
      <div className="tp-form-section-intro">
        <h3>Kịch bản · {story.title}</h3>
      </div>
      <div className="cozy-form-stack">
        <p className="tp-story-copy">{story.story.opening}</p>
        <p className="tp-story-copy">{story.story.middle}</p>
        <p className="tp-story-copy">{story.story.ending}</p>
      </div>
      {story.scenes.length > 0 && (
        <div className="tp-scene-list">
          {story.scenes.map((scene, i) => (
            <div key={i} className="tp-scene-card">
              <h3>{scene.title}</h3>
              {/* A learning script stores its narration as the action too. */}
              {scene.action?.trim() !== scene.narration?.trim() && <p>{scene.action}</p>}
              <p>{scene.narration}</p>
            </div>
          ))}
        </div>
      )}
      {showRewrite && (
        <FormField
          label={text.hint}
          htmlFor={hintId}
          labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}
          help="Tối đa 400 ký tự trên một dòng."
          error={invalid ? text.invalidHint : undefined}
        >
          <input id={hintId} className="cozy-input" value={hint} onChange={(e) => setHint(e.target.value)} />
        </FormField>
      )}
      {(showRewrite || showConfirm || showConfirmAgain) && (
        <FormActionBar>
          {showRewrite && <button type="button" className="s2l-button" onClick={rewrite}>{text.rewrite}</button>}
          {showConfirm && <button type="button" className="s2l-button is-primary" onClick={confirm}>{text.confirm}</button>}
          {showConfirmAgain && <button type="button" className="s2l-button is-primary" onClick={confirmAgain}>{text.confirmAgain}</button>}
        </FormActionBar>
      )}
    </section>
  );
}
