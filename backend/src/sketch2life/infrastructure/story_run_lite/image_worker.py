"""Windows Job Object constrained image admission and V2 JPEG normalization."""

from __future__ import annotations

import ctypes
import hashlib
import io
import multiprocessing
import os
import tempfile
import time
import warnings
from ctypes import wintypes
from pathlib import Path
from typing import Any

from sketch2life.application.ports.story_run_lite import ImageNormalizerPort, NormalizedImage
from sketch2life.domain.story_run_lite import (
    MAX_IMAGE_PIXELS,
    MAX_UPLOAD_BYTES,
    MODEL_INPUT_LIMIT_BYTES,
)

WORKER_MEMORY_LIMIT_BYTES = 1_073_741_824
WORKER_CPU_LIMIT_PERCENT = 25
WORKER_DEADLINE_SECONDS = 120
_MODEL_JPEG_LIMIT_BYTES = MODEL_INPUT_LIMIT_BYTES - 32_768


class ImageNormalizationError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _CpuRateControlInformation(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]


class _BasicAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class _BasicAndIoAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("BasicInfo", _BasicAccountingInformation),
        ("IoInfo", _IoCounters),
    ]


class _WindowsJobObject:
    """Apply process-memory, CPU-rate/time, and kill-on-close limits before decoding."""

    _JOB_OBJECT_LIMIT_PROCESS_TIME = 0x00000002
    _JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
    _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
    _JOB_OBJECT_CPU_RATE_CONTROL_ENABLE = 0x00000001
    _JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP = 0x00000004
    _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
    _JOB_OBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION = 8
    _JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION = 15
    _PROCESS_TERMINATE = 0x0001
    _PROCESS_SET_QUOTA = 0x0100
    _PROCESS_QUERY_INFORMATION = 0x0400

    def __init__(self, *, memory_bytes: int, cpu_percent: int, cpu_seconds: int) -> None:
        if os.name != "nt":
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE", "Verified Windows Job Object support is required."
            )
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self._kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self._kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self._kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self._kernel32.QueryInformationJobObject.restype = wintypes.BOOL
        self._kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self._kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._handle = self._kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE", "Windows could not create a constrained worker job."
            )
        self._closed = False
        self._configure(memory_bytes=memory_bytes, cpu_percent=cpu_percent, cpu_seconds=cpu_seconds)

    def _configure(self, *, memory_bytes: int, cpu_percent: int, cpu_seconds: int) -> None:
        extended = _ExtendedLimitInformation()
        extended.BasicLimitInformation.LimitFlags = (
            self._JOB_OBJECT_LIMIT_PROCESS_MEMORY
            | self._JOB_OBJECT_LIMIT_PROCESS_TIME
            | self._JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        extended.BasicLimitInformation.PerProcessUserTimeLimit = cpu_seconds * 10_000_000
        extended.ProcessMemoryLimit = memory_bytes
        if not self._kernel32.SetInformationJobObject(
            self._handle,
            self._JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(extended),
            ctypes.sizeof(extended),
        ):
            self.close()
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE",
                "Windows could not enforce worker memory and time limits.",
            )
        cpu = _CpuRateControlInformation(
            ControlFlags=self._JOB_OBJECT_CPU_RATE_CONTROL_ENABLE
            | self._JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP,
            CpuRate=cpu_percent * 100,
        )
        if not self._kernel32.SetInformationJobObject(
            self._handle,
            self._JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION,
            ctypes.byref(cpu),
            ctypes.sizeof(cpu),
        ):
            self.close()
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE", "Windows could not enforce the worker CPU hard cap."
            )

    def assign(self, process_id: int) -> None:
        process = self._kernel32.OpenProcess(
            self._PROCESS_TERMINATE | self._PROCESS_SET_QUOTA | self._PROCESS_QUERY_INFORMATION,
            False,
            process_id,
        )
        if not process:
            self.close()
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE",
                "Windows could not open the worker process for job assignment.",
            )
        try:
            assigned = self._kernel32.AssignProcessToJobObject(self._handle, process)
        finally:
            self._kernel32.CloseHandle(process)
        if not assigned:
            self.close()
            raise ImageNormalizationError(
                "WORKER_LIMITS_UNAVAILABLE",
                "Windows could not assign the decoder to its constrained job.",
            )

    def measurements(self) -> dict[str, int]:
        """Read back enforced limits and OS accounting before closing the job."""

        extended = _ExtendedLimitInformation()
        accounting = _BasicAndIoAccountingInformation()
        cpu = _CpuRateControlInformation()
        queries = (
            (
                self._JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                extended,
            ),
            (
                self._JOB_OBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION,
                accounting,
            ),
            (
                self._JOB_OBJECT_CPU_RATE_CONTROL_INFORMATION,
                cpu,
            ),
        )
        for information_class, value in queries:
            returned = wintypes.DWORD()
            if not self._kernel32.QueryInformationJobObject(
                self._handle,
                information_class,
                ctypes.byref(value),
                ctypes.sizeof(value),
                ctypes.byref(returned),
            ):
                raise ImageNormalizationError(
                    "WORKER_LIMITS_UNAVAILABLE",
                    "Windows could not read back worker limits and usage measurements.",
                )
        return {
            "memory_limit_bytes": int(extended.ProcessMemoryLimit),
            "peak_memory_bytes": int(extended.PeakProcessMemoryUsed),
            "cpu_user_time_100ns": int(accounting.BasicInfo.TotalUserTime),
            "cpu_kernel_time_100ns": int(accounting.BasicInfo.TotalKernelTime),
            "cpu_hard_cap_percent": int(cpu.CpuRate // 100),
        }

    def close(self) -> None:
        if not self._closed:
            self._kernel32.CloseHandle(self._handle)
            self._closed = True


class WindowsJobObjectImageNormalizer(ImageNormalizerPort):
    """Decode only after the worker is assigned verified process-enforced OS limits."""

    def __init__(
        self,
        *,
        temporary_root: Path,
        memory_limit_bytes: int = WORKER_MEMORY_LIMIT_BYTES,
        cpu_limit_percent: int = WORKER_CPU_LIMIT_PERCENT,
        deadline_seconds: int = WORKER_DEADLINE_SECONDS,
    ) -> None:
        if (
            memory_limit_bytes < 128 * 1024 * 1024
            or not 1 <= cpu_limit_percent <= 100
            or deadline_seconds < 1
        ):
            raise ValueError("worker resource limits are invalid")
        self._root = temporary_root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._memory = memory_limit_bytes
        self._cpu_percent = cpu_limit_percent
        self._deadline = deadline_seconds

    def normalize(
        self, snapshot: bytes, *, original_media_type: str, sha256: str
    ) -> NormalizedImage:
        if not snapshot or len(snapshot) > MAX_UPLOAD_BYTES:
            raise ImageNormalizationError(
                "IMAGE_TOO_LARGE", "Original image is outside the upload limit."
            )
        if hashlib.sha256(snapshot).hexdigest() != sha256:
            raise ImageNormalizationError(
                "IMAGE_HASH_MISMATCH", "Quarantine snapshot digest changed."
            )
        if original_media_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ImageNormalizationError(
                "UNSUPPORTED_MEDIA_TYPE", "Only JPEG, PNG, and WebP are accepted."
            )
        input_fd, input_name = tempfile.mkstemp(
            prefix="storyrun-input-", suffix=".bin", dir=self._root
        )
        output_fd, output_name = tempfile.mkstemp(
            prefix="storyrun-derived-", suffix=".jpg", dir=self._root
        )
        os.close(output_fd)
        try:
            with os.fdopen(input_fd, "wb") as output:
                output.write(snapshot)
                output.flush()
                os.fsync(output.fileno())
            context = multiprocessing.get_context("spawn")
            parent, child = context.Pipe(duplex=True)
            process = context.Process(
                target=_normalize_worker,
                args=(input_name, output_name, original_media_type, sha256, child),
                daemon=False,
            )
            process.start()
            child.close()
            job: _WindowsJobObject | None = None
            measurements: dict[str, int] | None = None
            try:
                job = _WindowsJobObject(
                    memory_bytes=self._memory,
                    cpu_percent=self._cpu_percent,
                    cpu_seconds=max(1, self._deadline // 2),
                )
                job.assign(process.pid or 0)
                # The worker blocks before opening the input or importing Pillow until this signal.
                parent.send("DECODE")
                if not parent.poll(self._deadline):
                    process.terminate()
                    process.join(timeout=2)
                    raise ImageNormalizationError(
                        "WORKER_TIMEOUT", "Image worker exceeded its deadline."
                    )
                result = parent.recv()
                process.join(timeout=2)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                    raise ImageNormalizationError(
                        "WORKER_TIMEOUT", "Image worker did not exit after its result."
                    )
                if process.exitcode == 0 and isinstance(result, dict):
                    if job is None:
                        raise ImageNormalizationError(
                            "WORKER_LIMITS_UNAVAILABLE", "Image worker had no constrained job."
                        )
                    measurements = job.measurements()
                    if (
                        measurements["memory_limit_bytes"] != self._memory
                        or measurements["cpu_hard_cap_percent"] != self._cpu_percent
                        or not 0 < measurements["peak_memory_bytes"] <= self._memory
                    ):
                        raise ImageNormalizationError(
                            "WORKER_LIMITS_UNAVAILABLE",
                            "Windows did not report the expected worker limits and usage.",
                        )
            except ImageNormalizationError:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                raise
            except (EOFError, OSError, RuntimeError) as exc:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=2)
                raise ImageNormalizationError(
                    "IMAGE_WORKER_FAILED", "Image worker failed closed."
                ) from exc
            finally:
                parent.close()
                if job is not None:
                    job.close()
            if process.exitcode != 0 or not isinstance(result, dict):
                raise ImageNormalizationError("IMAGE_WORKER_FAILED", "Image worker failed closed.")
            if result.get("error"):
                raise ImageNormalizationError(
                    str(result["error"]), "Image could not be admitted safely."
                )
            if measurements is None or not isinstance(result.get("worker_elapsed_ms"), int):
                raise ImageNormalizationError(
                    "WORKER_LIMITS_UNAVAILABLE",
                    "Windows worker limit and runtime measurements are unavailable.",
                )
            try:
                output_bytes = Path(output_name).read_bytes()
            except OSError:
                raise ImageNormalizationError(
                    "IMAGE_WORKER_FAILED", "Derived model image is unavailable."
                ) from None
            if not output_bytes or len(output_bytes) > MODEL_INPUT_LIMIT_BYTES:
                raise ImageNormalizationError(
                    "MODEL_INPUT_TOO_LARGE", "Derived model image exceeds the V2 limit."
                )
            digest = hashlib.sha256(output_bytes).hexdigest()
            if digest != result.get("derived_sha256"):
                raise ImageNormalizationError(
                    "IMAGE_WORKER_FAILED", "Derived image hash verification failed."
                )
            return NormalizedImage(
                original_media_type=str(result["original_media_type"]),
                original_sha256=sha256,
                original_size_bytes=len(snapshot),
                width=int(result["width"]),
                height=int(result["height"]),
                derived_media_type="image/jpeg",
                derived_sha256=digest,
                derived_size_bytes=len(output_bytes),
                derived_bytes=output_bytes,
                worker_memory_limit_bytes=self._memory,
                worker_cpu_percent=self._cpu_percent,
                worker_deadline_seconds=self._deadline,
                worker_peak_memory_bytes=int(measurements["peak_memory_bytes"]),
                worker_cpu_user_time_100ns=int(measurements["cpu_user_time_100ns"]),
                worker_cpu_kernel_time_100ns=int(measurements["cpu_kernel_time_100ns"]),
                worker_cpu_hard_cap_percent=int(measurements["cpu_hard_cap_percent"]),
                worker_elapsed_ms=int(result["worker_elapsed_ms"]),
            )
        finally:
            Path(input_name).unlink(missing_ok=True)
            Path(output_name).unlink(missing_ok=True)


def _normalize_worker(
    input_path: str,
    output_path: str,
    declared_media_type: str,
    expected_sha256: str,
    connection: Any,
) -> None:
    """Child process entrypoint. No decoder/parser runs before the parent releases its gate."""

    try:
        if connection.recv() != "DECODE":
            connection.send({"error": "WORKER_GATE_CLOSED"})
            return
        started = time.perf_counter()
        try:
            data = Path(input_path).read_bytes()
        except OSError:
            connection.send({"error": "QUARANTINE_UNAVAILABLE"})
            return
        if (
            not 1 <= len(data) <= MAX_UPLOAD_BYTES
            or hashlib.sha256(data).hexdigest() != expected_sha256
        ):
            connection.send({"error": "IMAGE_HASH_MISMATCH"})
            return
        try:
            from PIL import Image, ImageOps
        except ImportError:
            connection.send({"error": "IMAGE_DECODER_UNAVAILABLE"})
            return
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        try:
            with Image.open(io.BytesIO(data)) as opened:
                media_type = {
                    "JPEG": "image/jpeg",
                    "PNG": "image/png",
                    "WEBP": "image/webp",
                }.get(opened.format or "")
                if media_type is None or media_type != declared_media_type:
                    connection.send({"error": "UNSUPPORTED_MEDIA_TYPE"})
                    return
                if getattr(opened, "n_frames", 1) != 1:
                    connection.send({"error": "IMAGE_INVALID"})
                    return
                width, height = opened.size
                if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                    connection.send({"error": "IMAGE_TOO_LARGE"})
                    return
                opened.load()
                oriented = ImageOps.exif_transpose(opened)
                if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                    rgba = oriented.convert("RGBA")
                    background = Image.new("RGB", rgba.size, (255, 255, 255))
                    background.paste(rgba, mask=rgba.getchannel("A"))
                    rgb = background
                else:
                    rgb = oriented.convert("RGB")
                normalized = _encode_model_jpeg(rgb, Image)
        except Image.DecompressionBombError:
            connection.send({"error": "IMAGE_TOO_LARGE"})
            return
        except Image.DecompressionBombWarning:
            connection.send({"error": "IMAGE_TOO_LARGE"})
            return
        except (OSError, ValueError, SyntaxError):
            connection.send({"error": "IMAGE_INVALID"})
            return
        digest = hashlib.sha256(normalized).hexdigest()
        try:
            Path(output_path).write_bytes(normalized)
        except OSError:
            connection.send({"error": "IMAGE_WORKER_FAILED"})
            return
        connection.send(
            {
                "original_media_type": media_type,
                "width": width,
                "height": height,
                "derived_sha256": digest,
                "worker_elapsed_ms": max(1, int((time.perf_counter() - started) * 1000)),
            }
        )
    except (EOFError, OSError):
        return
    finally:
        connection.close()


def _encode_model_jpeg(image: Any, image_module: Any) -> bytes:
    current = image
    for attempt in range(10):
        quality = max(62, 90 - (attempt * 4))
        buffer = io.BytesIO()
        current.save(buffer, format="JPEG", quality=quality, optimize=True, progressive=False)
        encoded = buffer.getvalue()
        if len(encoded) <= _MODEL_JPEG_LIMIT_BYTES:
            return encoded
        factor = min(0.88, max(0.25, (_MODEL_JPEG_LIMIT_BYTES / len(encoded)) ** 0.5 * 0.92))
        width = max(1, int(current.width * factor))
        height = max(1, int(current.height * factor))
        if (width, height) == current.size:
            break
        current = current.resize((width, height), image_module.Resampling.LANCZOS)
    raise ImageNormalizationError(
        "MODEL_INPUT_TOO_LARGE", "Image could not be normalized below the V2 input limit."
    )


__all__ = [
    "ImageNormalizationError",
    "WORKER_CPU_LIMIT_PERCENT",
    "WORKER_DEADLINE_SECONDS",
    "WORKER_MEMORY_LIMIT_BYTES",
    "WindowsJobObjectImageNormalizer",
]
