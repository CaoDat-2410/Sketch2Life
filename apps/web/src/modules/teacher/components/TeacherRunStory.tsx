import { useState } from "react";
import { teacherRunApi, type TeacherRun } from "../../../shared/api/teacherRunApi";
import { storyVideoCopy as text } from "../services/teacherRunCopy";
import { canRewrite, validHint } from "../services/teacherStoryVideo";

interface Props { run: TeacherRun; execute: (fingerprint: unknown[], action: (key: string) => Promise<unknown>) => Promise<void> }
export function TeacherRunStory({ run, execute }: Props) {
  const [hint, setHint] = useState(""); const [invalid, setInvalid] = useState(false);
  if (run.story_revision_no === null || !run.story) return null;
  const story = run.story; const revision = run.story_revision_no; const hash = run.story_sha256;
  function rewrite() {
    if (!validHint(hint)) { setInvalid(true); return; }
    setInvalid(false); const value = hint.trim() || undefined;
    void execute(["rewrite", run.run_id, revision, hash, value], key => teacherRunApi.rewrite(run.run_id, revision, hash ?? undefined, value, key));
  }
  return <section><h2>{story.title}</h2><p>{story.story.opening}</p><p>{story.story.middle}</p><p>{story.story.ending}</p>{story.scenes.map((scene, i) => <div key={i}><h3>{scene.title}</h3><p>{scene.action}</p><p>{scene.narration}</p></div>)}
    {canRewrite(run) && <><label>{text.hint}<input value={hint} onChange={e => setHint(e.target.value)} /></label>{invalid && <p role="alert">{text.invalidHint}</p>}<button type="button" onClick={rewrite}>{text.rewrite}</button></>}
    {run.run_state === "SCRIPT_REVIEW" && run.story_status === "DRAFT" && hash && <button type="button" onClick={() => void execute(["confirmStory", run.run_id, revision, hash], key => teacherRunApi.confirmStory(run.run_id, revision, hash, key))}>{text.confirm}</button>}
  </section>;
}
