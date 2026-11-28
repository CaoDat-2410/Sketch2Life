import { useCallback, useEffect, useRef, useState } from "react";

const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;
const MAX_CAPTURE_EDGE = 1920;
const CAMERA_CONSTRAINTS: MediaStreamConstraints = {
  video: { facingMode: { ideal: "environment" } },
  audio: false,
};

type CameraMode = "closed" | "opening" | "live" | "capturing" | "captured";
type CapturedPhoto = { file: File; previewUrl: string };
type Props = { disabled?: boolean; onCapture: (file: File) => void };

function stopTracks(stream: MediaStream) {
  for (const track of stream.getTracks()) track.stop();
}

function cameraErrorMessage(error: unknown) {
  const name = error && typeof error === "object" && "name" in error ? String(error.name) : "";
  if (name === "NotAllowedError" || name === "SecurityError") {
    return "Không thể cấp quyền truy cập camera. Bạn vẫn có thể chọn ảnh từ thiết bị.";
  }
  if (name === "NotFoundError" || name === "OverconstrainedError" || name === "ConstraintNotSatisfiedError") {
    return "Không tìm thấy camera phù hợp. Bạn vẫn có thể chọn ảnh từ thiết bị.";
  }
  if (name === "NotReadableError") {
    return "Camera đang bận hoặc không thể sử dụng lúc này. Bạn vẫn có thể chọn ảnh từ thiết bị.";
  }
  return "Camera không khả dụng trong trình duyệt hoặc kết nối không an toàn này. Bạn vẫn có thể chọn ảnh từ thiết bị.";
}

function canvasJpeg(canvas: HTMLCanvasElement, quality: number) {
  return new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", quality));
}

export function TeacherRunCameraCapture({ disabled = false, onCapture }: Props) {
  const [mode, setMode] = useState<CameraMode>("closed");
  const [message, setMessage] = useState("");
  const [photo, setPhoto] = useState<CapturedPhoto | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const requestIdRef = useRef(0);
  const captureIdRef = useRef(0);
  const openingRef = useRef(false);
  const captureRunningRef = useRef(false);
  const mountedRef = useRef(true);

  const releaseStream = useCallback(() => {
    const stream = streamRef.current;
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    if (stream) stopTracks(stream);
  }, []);

  const clearPhoto = useCallback(() => {
    const previewUrl = previewUrlRef.current;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrlRef.current = null;
    setPhoto(null);
  }, []);

  const closeCamera = useCallback(() => {
    requestIdRef.current += 1;
    captureIdRef.current += 1;
    openingRef.current = false;
    captureRunningRef.current = false;
    releaseStream();
    clearPhoto();
    setMessage("");
    setMode("closed");
  }, [clearPhoto, releaseStream]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      requestIdRef.current += 1;
      captureIdRef.current += 1;
      openingRef.current = false;
      captureRunningRef.current = false;
      const stream = streamRef.current;
      streamRef.current = null;
      if (stream) stopTracks(stream);
      const previewUrl = previewUrlRef.current;
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrlRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (mode !== "live") return;
    const video = videoRef.current;
    const stream = streamRef.current;
    if (!video || !stream) return;
    video.srcObject = stream;
    void video.play().catch(() => undefined);
    return () => {
      if (video.srcObject === stream) video.srcObject = null;
    };
  }, [mode]);

  const openCamera = useCallback(async () => {
    if (disabled || openingRef.current || streamRef.current) return;
    openingRef.current = true;
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setMessage("");
    setMode("opening");

    const mediaDevices = typeof navigator === "undefined" ? undefined : navigator.mediaDevices;
    if (!mediaDevices?.getUserMedia) {
      openingRef.current = false;
      setMode("closed");
      setMessage("Camera không khả dụng trong trình duyệt hoặc kết nối không an toàn này. Bạn vẫn có thể chọn ảnh từ thiết bị.");
      return;
    }

    try {
      const stream = await mediaDevices.getUserMedia(CAMERA_CONSTRAINTS);
      if (!mountedRef.current || requestId !== requestIdRef.current) {
        stopTracks(stream);
        return;
      }
      streamRef.current = stream;
      setMode("live");
    } catch (error) {
      if (mountedRef.current && requestId === requestIdRef.current) {
        setMode("closed");
        setMessage(cameraErrorMessage(error));
      }
    } finally {
      if (requestId === requestIdRef.current) openingRef.current = false;
    }
  }, [disabled]);

  const shoot = useCallback(async () => {
    if (disabled || mode !== "live" || captureRunningRef.current) return;
    captureRunningRef.current = true;
    const captureId = captureIdRef.current + 1;
    captureIdRef.current = captureId;
    const requestId = requestIdRef.current;
    const video = videoRef.current;
    setMode("capturing");

    try {
      if (!video || video.videoWidth < 1 || video.videoHeight < 1) throw new Error("Camera preview is not ready.");
      const scale = Math.min(1, MAX_CAPTURE_EDGE / Math.max(video.videoWidth, video.videoHeight));
      const width = Math.max(1, Math.round(video.videoWidth * scale));
      const height = Math.max(1, Math.round(video.videoHeight * scale));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Canvas is unavailable.");
      context.drawImage(video, 0, 0, width, height);
      releaseStream();

      let blob: Blob | null = null;
      for (const quality of [0.88, 0.76, 0.64]) {
        blob = await canvasJpeg(canvas, quality);
        if (!blob || blob.size <= MAX_UPLOAD_BYTES) break;
      }
      if (!mountedRef.current || requestId !== requestIdRef.current || captureId !== captureIdRef.current) return;
      if (!blob || blob.size < 1) throw new Error("The camera could not create a photo.");
      if (blob.size > MAX_UPLOAD_BYTES) {
        setMode("closed");
        setMessage("Ảnh chụp vượt quá giới hạn 20 MiB. Hãy chụp lại hoặc chọn ảnh khác từ thiết bị.");
        return;
      }

      const timestamp = Date.now();
      const file = new File([blob], `ve-cua-be-${timestamp}.jpg`, { type: "image/jpeg", lastModified: timestamp });
      const previewUrl = URL.createObjectURL(blob);
      previewUrlRef.current = previewUrl;
      setPhoto({ file, previewUrl });
      setMode("captured");
    } catch {
      releaseStream();
      if (mountedRef.current && requestId === requestIdRef.current && captureId === captureIdRef.current) {
        setMode("closed");
        setMessage("Không thể tạo ảnh từ camera lúc này. Bạn vẫn có thể chọn ảnh từ thiết bị.");
      }
    } finally {
      if (captureId === captureIdRef.current) captureRunningRef.current = false;
    }
  }, [disabled, mode, releaseStream]);

  const retake = useCallback(() => {
    clearPhoto();
    setMessage("");
    void openCamera();
  }, [clearPhoto, openCamera]);

  const usePhoto = useCallback(() => {
    if (!photo || disabled) return;
    const file = photo.file;
    closeCamera();
    onCapture(file);
  }, [closeCamera, disabled, onCapture, photo]);

  return (
    <div className="tp-run-camera">
      {mode === "closed" && <button type="button" className="s2l-button" disabled={disabled} onClick={() => void openCamera()}>Mở camera</button>}
      {message && <p className="s2l-alert" role="alert">{message}</p>}
      {mode === "opening" && (
        <div className="tp-run-camera-actions">
          <p className="s2l-note" role="status">Đang mở camera…</p>
          <button type="button" className="s2l-button" disabled={disabled} onClick={closeCamera}>Đóng camera</button>
        </div>
      )}
      {mode === "live" && (
        <div className="tp-run-camera-session">
          <video ref={videoRef} className="tp-run-camera-preview" autoPlay playsInline muted aria-label="Xem trước camera" />
          <div className="tp-run-camera-actions">
            <button type="button" className="s2l-button is-primary" disabled={disabled} onClick={() => void shoot()}>Chụp ảnh</button>
            <button type="button" className="s2l-button" disabled={disabled} onClick={closeCamera}>Đóng camera</button>
          </div>
        </div>
      )}
      {mode === "capturing" && (
        <div className="tp-run-camera-actions">
          <p className="s2l-note" role="status">Đang xử lý ảnh…</p>
          <button type="button" className="s2l-button" disabled={disabled} onClick={closeCamera}>Đóng camera</button>
        </div>
      )}
      {mode === "captured" && photo && (
        <div className="tp-run-camera-session">
          <img className="tp-run-camera-preview" src={photo.previewUrl} alt="Ảnh chụp bức tranh" />
          <div className="tp-run-camera-actions">
            <button type="button" className="s2l-button" disabled={disabled} onClick={retake}>Chụp lại</button>
            <button type="button" className="s2l-button is-primary" disabled={disabled} onClick={usePhoto}>Dùng ảnh này</button>
            <button type="button" className="s2l-button" disabled={disabled} onClick={closeCamera}>Đóng camera</button>
          </div>
        </div>
      )}
    </div>
  );
}
