import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { teacherRunApi, type TeacherRun } from "../../../../shared/api/teacherRunApi";
import * as uploads from "../../../../shared/api/teacherOccurrenceApi";
import { inputCopy } from "../../services/teacherRunCopy";
import { runFileMediaType } from "../../services/teacherRunInputs";
import { TeacherRunInputs } from "../TeacherRunInputs";
import { TeacherRunCameraCapture } from "../TeacherRunCameraCapture";

const originalMediaDevices = Object.getOwnPropertyDescriptor(navigator, "mediaDevices");
const originalCreateObjectURL = Object.getOwnPropertyDescriptor(URL, "createObjectURL");
const originalRevokeObjectURL = Object.getOwnPropertyDescriptor(URL, "revokeObjectURL");
const originalPlay = Object.getOwnPropertyDescriptor(HTMLMediaElement.prototype, "play");
const originalVideoWidth = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, "videoWidth");
const originalVideoHeight = Object.getOwnPropertyDescriptor(HTMLVideoElement.prototype, "videoHeight");
const originalGetContext = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, "getContext");
const originalToBlob = Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype, "toBlob");

let getUserMedia: ReturnType<typeof vi.fn>;
let drawImage: ReturnType<typeof vi.fn>;
let canvasSizes: Array<[number, number]>;
let nextObjectUrl: number;

function restoreDescriptor(target: object, key: PropertyKey, descriptor: PropertyDescriptor | undefined) {
  if (descriptor) Object.defineProperty(target, key, descriptor);
  else Reflect.deleteProperty(target, key);
}

function mockStream() {
  const track = { stop: vi.fn() } as unknown as MediaStreamTrack;
  const stream = { getTracks: () => [track] } as unknown as MediaStream;
  return { stream, track };
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

function renderInputs() {
  const run = {
    run_id: "run",
    run_state: "INPUT_REVIEW",
    run_revision: 4,
    context_revision: 2,
    context_confirmed: false,
    context_snapshot_sha256: "abc",
    context_snapshot: { age_months: 48, objectives: [], teacher_direction: "", activity_title: null },
    candidate: null,
    understanding_revision: null,
    job_state: null,
  } as unknown as TeacherRun;
  vi.spyOn(teacherRunApi, "transcript").mockResolvedValue({ state: "NONE", text: null, transcript_revision: null, transcript_sha256: null } as never);
  render(<TeacherRunInputs run={run} refresh={async () => {}} fail={vi.fn()} lifecycle={vi.fn()} />);
}

beforeEach(() => {
  getUserMedia = vi.fn();
  drawImage = vi.fn();
  canvasSizes = [];
  nextObjectUrl = 0;
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
  Object.defineProperty(URL, "createObjectURL", { configurable: true, value: vi.fn(() => `blob:teacher-photo-${++nextObjectUrl}`) });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
  Object.defineProperty(HTMLMediaElement.prototype, "play", { configurable: true, value: vi.fn().mockResolvedValue(undefined) });
  Object.defineProperty(HTMLVideoElement.prototype, "videoWidth", { configurable: true, get: () => 4032 });
  Object.defineProperty(HTMLVideoElement.prototype, "videoHeight", { configurable: true, get: () => 3024 });
  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    configurable: true,
    value: function (this: HTMLCanvasElement) {
      canvasSizes.push([this.width, this.height]);
      return { drawImage };
    },
  });
  Object.defineProperty(HTMLCanvasElement.prototype, "toBlob", {
    configurable: true,
    value: function (this: HTMLCanvasElement, callback: BlobCallback, type?: string) {
      callback(new Blob(["jpeg-payload"], { type: type ?? "image/jpeg" }));
    },
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  restoreDescriptor(navigator, "mediaDevices", originalMediaDevices);
  restoreDescriptor(URL, "createObjectURL", originalCreateObjectURL);
  restoreDescriptor(URL, "revokeObjectURL", originalRevokeObjectURL);
  restoreDescriptor(HTMLMediaElement.prototype, "play", originalPlay);
  restoreDescriptor(HTMLVideoElement.prototype, "videoWidth", originalVideoWidth);
  restoreDescriptor(HTMLVideoElement.prototype, "videoHeight", originalVideoHeight);
  restoreDescriptor(HTMLCanvasElement.prototype, "getContext", originalGetContext);
  restoreDescriptor(HTMLCanvasElement.prototype, "toBlob", originalToBlob);
});

it("requests a rear camera only after the button is pressed and shows an inline muted preview", async () => {
  const { stream } = mockStream();
  getUserMedia.mockResolvedValue(stream);
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);

  expect(getUserMedia).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  const video = await screen.findByLabelText("Xem trước camera") as HTMLVideoElement;
  await waitFor(() => expect(video.srcObject).toBe(stream));

  expect(getUserMedia).toHaveBeenCalledWith({ video: { facingMode: { ideal: "environment" } }, audio: false });
  expect(video.muted).toBe(true);
  expect(video.playsInline).toBe(true);
  expect(video.autoplay).toBe(true);
});

it("does not request another stream while the first permission request is pending", async () => {
  const request = deferred<MediaStream>();
  const { stream } = mockStream();
  getUserMedia.mockReturnValue(request.promise);
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  const openButton = screen.getByRole("button", { name: "Mở camera" });

  await act(async () => {
    fireEvent.click(openButton);
    fireEvent.click(openButton);
  });
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  await act(async () => { request.resolve(stream); await request.promise; });
  await screen.findByLabelText("Xem trước camera");
});

it("shoots a resized JPEG and stops the live track", async () => {
  const { stream, track } = mockStream();
  getUserMedia.mockResolvedValue(stream);
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");

  fireEvent.click(screen.getByRole("button", { name: "Chụp ảnh" }));
  expect(await screen.findByRole("img", { name: "Ảnh chụp bức tranh" })).toBeTruthy();
  expect(track.stop).toHaveBeenCalledTimes(1);
  expect(drawImage).toHaveBeenCalledTimes(1);
  expect(canvasSizes).toEqual([[1920, 1440]]);
});

it("retakes by opening a fresh stream and revokes the previous still preview", async () => {
  const first = mockStream();
  const second = mockStream();
  getUserMedia.mockResolvedValueOnce(first.stream).mockResolvedValueOnce(second.stream);
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);

  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");
  fireEvent.click(screen.getByRole("button", { name: "Chụp ảnh" }));
  await screen.findByRole("img", { name: "Ảnh chụp bức tranh" });
  fireEvent.click(screen.getByRole("button", { name: "Chụp lại" }));

  await waitFor(() => expect(getUserMedia).toHaveBeenCalledTimes(2));
  const nextVideo = await screen.findByLabelText("Xem trước camera") as HTMLVideoElement;
  await waitFor(() => expect(nextVideo.srcObject).toBe(second.stream));
  expect(first.track.stop).toHaveBeenCalledTimes(1);
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:teacher-photo-1");
});

it("uses the captured JPEG as a .jpg File within the existing artwork limit", async () => {
  const { stream } = mockStream();
  const onCapture = vi.fn();
  getUserMedia.mockResolvedValue(stream);
  render(<TeacherRunCameraCapture onCapture={onCapture} />);

  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");
  fireEvent.click(screen.getByRole("button", { name: "Chụp ảnh" }));
  await screen.findByRole("img", { name: "Ảnh chụp bức tranh" });
  fireEvent.click(screen.getByRole("button", { name: "Dùng ảnh này" }));

  expect(onCapture).toHaveBeenCalledTimes(1);
  const file = onCapture.mock.calls[0][0] as File;
  expect(file.name).toMatch(/^ve-cua-be-\d+\.jpg$/);
  expect(file.type).toBe("image/jpeg");
  expect(file.size).toBeGreaterThan(0);
  expect(file.size).toBeLessThanOrEqual(20 * 1024 * 1024);
  expect(runFileMediaType(file, "RUN_ARTWORK")).toBe("image/jpeg");
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:teacher-photo-1");
});

it("stops tracks on close and unmount", async () => {
  const closed = mockStream();
  getUserMedia.mockResolvedValue(closed.stream);
  const view = render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");
  fireEvent.click(screen.getByRole("button", { name: "Đóng camera" }));
  expect(closed.track.stop).toHaveBeenCalledTimes(1);

  const unmounted = mockStream();
  getUserMedia.mockResolvedValue(unmounted.stream);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");
  view.unmount();
  expect(unmounted.track.stop).toHaveBeenCalledTimes(1);
});

it("stops a stream that resolves after the camera was closed", async () => {
  const request = deferred<MediaStream>();
  const late = mockStream();
  getUserMedia.mockReturnValue(request.promise);
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  fireEvent.click(screen.getByRole("button", { name: "Đóng camera" }));

  await act(async () => { request.resolve(late.stream); await request.promise; });
  expect(late.track.stop).toHaveBeenCalledTimes(1);
});

it("stops a stream that resolves after unmount", async () => {
  const request = deferred<MediaStream>();
  const late = mockStream();
  getUserMedia.mockReturnValue(request.promise);
  const view = render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  view.unmount();

  await act(async () => { request.resolve(late.stream); await request.promise; });
  expect(late.track.stop).toHaveBeenCalledTimes(1);
});

it("disables camera controls while the form is busy", async () => {
  const { stream, track } = mockStream();
  getUserMedia.mockResolvedValue(stream);
  const view = render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");

  view.rerender(<TeacherRunCameraCapture disabled onCapture={vi.fn()} />);
  expect((screen.getByRole("button", { name: "Chụp ảnh" }) as HTMLButtonElement).disabled).toBe(true);
  expect((screen.getByRole("button", { name: "Đóng camera" }) as HTMLButtonElement).disabled).toBe(true);
  expect(getUserMedia).toHaveBeenCalledTimes(1);
  view.unmount();
  expect(track.stop).toHaveBeenCalledTimes(1);
});

it.each([
  ["NotAllowedError", "Không thể cấp quyền truy cập camera."],
  ["SecurityError", "Không thể cấp quyền truy cập camera."],
  ["NotFoundError", "Không tìm thấy camera phù hợp."],
  ["OverconstrainedError", "Không tìm thấy camera phù hợp."],
  ["NotReadableError", "Camera đang bận"],
])("shows the Vietnamese fallback for %s", async (name, message) => {
  getUserMedia.mockRejectedValue(new DOMException("Camera unavailable", name));
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain(message);
  expect(alert.textContent).toContain("Bạn vẫn có thể chọn ảnh từ thiết bị.");
});

it("explains when camera access is unsupported or unavailable in an insecure context", async () => {
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: undefined });
  render(<TeacherRunCameraCapture onCapture={vi.fn()} />);
  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));

  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("kết nối không an toàn");
  expect(alert.textContent).toContain("Bạn vẫn có thể chọn ảnh từ thiết bị.");
  expect(getUserMedia).not.toHaveBeenCalled();
});

it("keeps the existing artwork upload path for a camera photo", async () => {
  const { stream } = mockStream();
  getUserMedia.mockResolvedValue(stream);
  const upload = vi.spyOn(uploads, "uploadFileForPurpose").mockResolvedValue("upl_camera");
  const attach = vi.spyOn(teacherRunApi, "attachArtwork").mockResolvedValue({} as never);
  renderInputs();

  fireEvent.click(screen.getByRole("button", { name: "Mở camera" }));
  await screen.findByLabelText("Xem trước camera");
  fireEvent.click(screen.getByRole("button", { name: "Chụp ảnh" }));
  await screen.findByRole("img", { name: "Ảnh chụp bức tranh" });
  fireEvent.click(screen.getByRole("button", { name: "Dùng ảnh này" }));
  expect(screen.getByText(/^ve-cua-be-\d+\.jpg$/)).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: inputCopy.upload }));
  await waitFor(() => expect(attach).toHaveBeenCalledWith("run", "upl_camera", 4, expect.any(String)));
  const file = upload.mock.calls[0][0] as File;
  expect(file.name).toMatch(/\.jpg$/);
  expect(file.type).toBe("image/jpeg");
  expect(upload).toHaveBeenCalledWith(file, "run", "RUN_ARTWORK", "image/jpeg", expect.any(Object));
});
