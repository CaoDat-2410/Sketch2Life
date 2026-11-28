import { useCallback, useEffect, useRef, useState } from "react";
import { encodeRecordingWav } from "../services/recordingWav";

type Mode = "closed" | "opening" | "recording" | "processing" | "ready";
type Props = { disabled?: boolean; onCapture: (file: File) => void };
const fallback = " Bạn vẫn có thể chọn tệp âm thanh từ thiết bị.";
const unsupported = "Không thể ghi âm trong trình duyệt hoặc kết nối không an toàn này." + fallback;
const conversionError = "Không thể xử lý bản ghi âm lúc này." + fallback;
function errorMessage(error: unknown) {
  const name = error && typeof error === "object" && "name" in error ? String(error.name) : "";
  if (name === "NotAllowedError" || name === "SecurityError") return "Không được cấp quyền sử dụng micro." + fallback;
  if (name === "NotFoundError" || name === "OverconstrainedError") return "Không tìm thấy micro phù hợp." + fallback;
  if (name === "NotReadableError" || name === "AbortError") return "Micro đang bận hoặc không thể sử dụng." + fallback;
  return unsupported;
}
function stopTracks(stream: MediaStream) { stream.getTracks().forEach((track) => track.stop()); }

export function TeacherRunAudioCapture({ disabled = false, onCapture }: Props) {
  const [mode, setMode] = useState<Mode>("closed");
  const [message, setMessage] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [recording, setRecording] = useState<{ file: File; url: string } | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const url = useRef<string | null>(null);
  const generation = useRef(0);
  const active = useRef(false);
  const mounted = useRef(true);
  const release = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    timer.current = null;
    if (stream.current) stopTracks(stream.current);
    stream.current = null;
  }, []);
  const clearPreview = useCallback(() => {
    if (url.current) URL.revokeObjectURL(url.current);
    url.current = null;
    setRecording(null);
  }, []);
  const close = useCallback(() => {
    generation.current++;
    active.current = false;
    const current = recorder.current;
    recorder.current = null;
    if (current && current.state !== "inactive") current.stop();
    release(); clearPreview(); setMessage(""); setMode("closed");
  }, [clearPreview, release]);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false; generation.current++; active.current = false;
      const current = recorder.current; recorder.current = null;
      if (current && current.state !== "inactive") current.stop();
      release();
      if (url.current) URL.revokeObjectURL(url.current);
      url.current = null;
    };
  }, [release]);
  const stop = useCallback(() => {
    const current = recorder.current;
    if (!current || current.state === "inactive") return;
    setMode("processing");
    current.stop();
    release();
  }, [release]);
  const start = useCallback(async () => {
    if (disabled || active.current) return;
    active.current = true;
    const id = ++generation.current;
    clearPreview(); setMessage(""); setElapsed(0); setMode("opening");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined" || typeof AudioContext === "undefined") {
      active.current = false; setMode("closed"); setMessage(unsupported); return;
    }
    try {
      const result = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current || generation.current !== id) { stopTracks(result); return; }
      stream.current = result;
      const current = new MediaRecorder(result);
      recorder.current = current;
      const chunks: Blob[] = [];
      current.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
      current.onerror = () => {
        if (generation.current !== id || !mounted.current) return;
        generation.current++; active.current = false; recorder.current = null; release(); setMode("closed"); setMessage(conversionError);
      };
      current.onstop = () => {
        if (!mounted.current || generation.current !== id) return;
        recorder.current = null;
        void (async () => {
          let context: AudioContext | null = null;
          try {
            const blob = new Blob(chunks, { type: current.mimeType });
            const bytes = await blob.arrayBuffer();
            if (!mounted.current || generation.current !== id) return;
            context = new AudioContext();
            const decoded = await context.decodeAudioData(bytes);
            if (!mounted.current || generation.current !== id) return;
            const wav = encodeRecordingWav(decoded);
            const now = Date.now();
            const file = new File([wav], `ghi-am-${now}.wav`, { type: "audio/wav", lastModified: now });
            const preview = URL.createObjectURL(wav);
            url.current = preview; active.current = false; setRecording({ file, url: preview }); setMode("ready");
          } catch {
            if (mounted.current && generation.current === id) { setMode("closed"); setMessage(conversionError); }
          } finally {
            if (context) await context.close().catch(() => undefined);
            if (generation.current === id) active.current = false;
          }
        })();
      };
      current.start(); setMode("recording");
      const started = Date.now();
      timer.current = setInterval(() => {
        const seconds = Math.floor((Date.now() - started) / 1000);
        setElapsed(Math.min(seconds, 120));
        if (Date.now() - started >= 119000) stop();
      }, 250);
    } catch (error) {
      release();
      if (mounted.current && generation.current === id) { active.current = false; recorder.current = null; setMode("closed"); setMessage(errorMessage(error)); }
    }
  }, [clearPreview, disabled, release, stop]);
  return (
    <div className="tp-run-camera">
      {mode === "closed" && <button type="button" className="s2l-button" disabled={disabled} onClick={() => void start()}>Ghi âm</button>}
      {message && <p className="s2l-alert" role="alert">{message}</p>}
      {mode !== "closed" && <div className="tp-run-camera-session">
        {mode === "opening" && <p className="s2l-note" role="status">Đang mở micro…</p>}
        {mode === "recording" && <p className="s2l-note" role="status">Đang ghi âm: {elapsed} / 120 giây</p>}
        {mode === "processing" && <p className="s2l-note" role="status">Đang xử lý bản ghi âm…</p>}
        {mode === "ready" && recording && <audio controls src={recording.url} aria-label="Nghe lại bản ghi âm" style={{ maxWidth: "100%" }} />}
        <div className="tp-run-camera-actions">
          {mode === "recording" && <button type="button" className="s2l-button is-primary" disabled={disabled} onClick={stop}>Dừng ghi âm</button>}
          {mode === "ready" && recording && <><button type="button" className="s2l-button" disabled={disabled} onClick={() => void start()}>Ghi âm lại</button><button type="button" className="s2l-button is-primary" disabled={disabled} onClick={() => { const file = recording.file; close(); onCapture(file); }}>Dùng bản ghi này</button></>}
          <button type="button" className="s2l-button" disabled={disabled} onClick={close}>Đóng ghi âm</button>
        </div>
      </div>}
    </div>
  );
}
