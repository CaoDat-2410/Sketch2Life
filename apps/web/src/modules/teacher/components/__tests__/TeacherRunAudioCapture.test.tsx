import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { TeacherRunAudioCapture } from "../TeacherRunAudioCapture";
import { TeacherRunInputs } from "../TeacherRunInputs";
import { encodeRecordingWav, MAX_RECORDING_SAMPLES } from "../../services/recordingWav";
import { teacherRunApi, type TeacherRun } from "../../../../shared/api/teacherRunApi";
import * as uploads from "../../../../shared/api/teacherOccurrenceApi";
import { inputCopy } from "../../services/teacherRunCopy";
const read = (blob: Blob) => new Promise<ArrayBuffer>((resolve) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result as ArrayBuffer); reader.readAsArrayBuffer(blob); });
let track: { stop: ReturnType<typeof vi.fn> }; let getMedia: ReturnType<typeof vi.fn>; let instance: MockRecorder;
class MockRecorder {
 state: RecordingState = "inactive"; mimeType = "audio/webm"; ondataavailable: ((e: BlobEvent) => void) | null = null; onstop: (() => void) | null = null; onerror: (() => void) | null = null;
 constructor() { instance = this; } start() { this.state = "recording"; } stop() { this.state = "inactive"; this.ondataavailable?.({ data: new Blob(["sound"]) } as BlobEvent); this.onstop?.(); }
}
const audio = (length = 48000, sampleRate = 48000) => ({ length, sampleRate, numberOfChannels: 2, getChannelData: (channel: number) => new Float32Array(length).fill(channel ? 0.25 : 0.75) } as AudioBuffer);
const closeContext = vi.fn(async () => {}); class MockAudioContext { decodeAudioData = vi.fn(async () => audio()); close = closeContext; }
beforeEach(() => {
 track = { stop: vi.fn() }; getMedia = vi.fn(async () => ({ getTracks: () => [track] }));
 vi.stubGlobal("MediaRecorder", MockRecorder); vi.stubGlobal("AudioContext", MockAudioContext);
 Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia: getMedia } });
 Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => "blob:preview") }); Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
 Object.defineProperty(Blob.prototype, "arrayBuffer", { configurable: true, value: function () { return read(this); } });
});
afterEach(() => { cleanup(); vi.useRealTimers(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });
it("encodes mono PCM WAV and caps samples", async () => {
 const wav = encodeRecordingWav(audio()); const view = new DataView(await read(wav));
 expect(wav.type).toBe("audio/wav"); expect(view.getUint32(4, true)).toBe(32036); expect(view.getUint16(20, true)).toBe(1); expect(view.getUint16(22, true)).toBe(1); expect(view.getUint32(24, true)).toBe(16000); expect(view.getUint16(34, true)).toBe(16); expect(view.getUint32(40, true)).toBe(32000); expect(view.getInt16(44, true)).toBe(16383);
 expect(encodeRecordingWav(audio(121 * 16000, 16000)).size).toBe(44 + MAX_RECORDING_SAMPLES * 2);
});
it("records, selects WAV and uploads it", async () => {
 vi.spyOn(teacherRunApi, "transcript").mockResolvedValue({ state: "NONE" } as never); vi.spyOn(teacherRunApi, "idea").mockResolvedValue({} as never); const upload = vi.spyOn(uploads, "uploadFileForPurpose").mockResolvedValue("ref");
 const run = { run_id: "run", run_state: "INPUT_REVIEW", run_revision: 1, context_revision: 1, candidate: null, understanding_revision: null } as TeacherRun;
 render(<TeacherRunInputs run={run} refresh={async () => {}} fail={vi.fn()} lifecycle={vi.fn()} />); fireEvent.click(screen.getByRole("button", { name: "Ghi âm" })); fireEvent.click(await screen.findByRole("button", { name: "Dừng ghi âm" })); expect(track.stop).toHaveBeenCalledTimes(1);
 fireEvent.click(await screen.findByRole("button", { name: "Dùng bản ghi này" })); expect(screen.getByText(/ghi-am-.*\.wav/)).toBeTruthy(); fireEvent.click(screen.getByRole("button", { name: inputCopy.submitIdea }));
 await waitFor(() => expect(upload).toHaveBeenCalledWith(expect.any(File), "run", "RUN_AUDIO", "audio/wav", expect.any(Object))); expect(upload.mock.calls[0][0].type).toBe("audio/wav"); expect(closeContext).toHaveBeenCalled();
});
it("releases tracks on cancel and unmount", async () => {
 const view = render(<TeacherRunAudioCapture onCapture={vi.fn()} />); fireEvent.click(screen.getByText("Ghi âm")); await screen.findByText("Dừng ghi âm"); fireEvent.click(screen.getByText("Đóng ghi âm")); expect(track.stop).toHaveBeenCalledTimes(1); fireEvent.click(screen.getByText("Ghi âm")); await screen.findByText("Dừng ghi âm"); view.unmount(); expect(track.stop).toHaveBeenCalledTimes(2);
});
it("releases late permission and prevents duplicate requests", async () => {
 let resolve!: (value: unknown) => void; getMedia.mockImplementation(() => new Promise((r) => { resolve = r; })); render(<TeacherRunAudioCapture onCapture={vi.fn()} />); const button = screen.getByText("Ghi âm"); fireEvent.click(button); fireEvent.click(button); fireEvent.click(screen.getByText("Đóng ghi âm")); await act(async () => resolve({ getTracks: () => [track] })); expect(getMedia).toHaveBeenCalledTimes(1); expect(track.stop).toHaveBeenCalledTimes(1);
});
it("automatically stops before 120 seconds", async () => {
 vi.useFakeTimers(); render(<TeacherRunAudioCapture onCapture={vi.fn()} />); await act(async () => { fireEvent.click(screen.getByText("Ghi âm")); }); await act(async () => { await vi.advanceTimersByTimeAsync(119000); }); expect(instance.state).toBe("inactive"); expect(track.stop).toHaveBeenCalledTimes(1);
});
it("explains denied permission and unsupported browsers", async () => {
 getMedia.mockRejectedValueOnce({ name: "NotAllowedError" }); render(<TeacherRunAudioCapture onCapture={vi.fn()} />); fireEvent.click(screen.getByText("Ghi âm")); expect((await screen.findByRole("alert")).textContent).toMatch(/quyền.*chọn tệp/); vi.stubGlobal("MediaRecorder", undefined); fireEvent.click(screen.getByText("Ghi âm")); expect(screen.getByRole("alert").textContent).toMatch(/trình duyệt.*chọn tệp/);
});
