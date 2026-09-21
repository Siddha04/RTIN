"""Real-time CCTV person detection utilities.

Ultralytics/OpenCV are intentionally imported lazily so the core API and CI
remain lightweight. Production deployments should install requirements-vision.txt
and provide a real YOLO weights file through YOLO_MODEL_PATH.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any


class VisionDependencyError(RuntimeError):
    """Raised when optional computer-vision dependencies are unavailable."""


class VisionCaptureError(RuntimeError):
    """Raised when a CCTV source cannot produce a frame."""


@dataclass(frozen=True)
class Detection:
    class_id: int
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int
    track_id: int | None = None


# Valid 1x1 JPEG fixture used only for deterministic tests/demo environments.
DEMO_JPEG = bytes.fromhex(
    "ffd8ffe000104a46494600010100000100010000ffdb004300"
    "080606070605080707070909080a0c140d0c0b0b0c191213"
    "141d1a1f1e1d1a1c1c2024273027222529221c1c2837292c"
    "2f30333434341f27393d38323c2e333432ffc0000b080001"
    "0001011100ffc40014000100000000000000000000000000"
    "0000ffc40014100100000000000000000000000000000000"
    "00da0008010100003f00d2cf20ffda000c03010002110311"
    "003f00d2cf20ffd9"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def capture_frame(source: str, *, timeout_seconds: float = 8.0) -> tuple[bytes, dict[str, Any]]:
    """Capture one JPEG frame from a local/RTSP/HTTP video source."""
    if not source:
        raise VisionCaptureError("CCTV source URL/path is empty")

    try:
        import cv2
    except ImportError as exc:
        raise VisionDependencyError(
            "OpenCV is not installed. Install services/api/requirements-vision.txt"
        ) from exc

    # OpenCV VideoCapture does not expose one portable timeout API across
    # backends, so frame availability is bounded by the backend itself.
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        capture.release()
        raise VisionCaptureError(f"Unable to open CCTV source: {source}")

    ok, frame = capture.read()
    capture.release()

    if not ok or frame is None:
        raise VisionCaptureError("CCTV source opened but returned no frame")

    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
    if not ok:
        raise VisionCaptureError("Failed to JPEG-encode CCTV frame")

    payload = encoded.tobytes()
    return payload, {
        "capture_mode": "LIVE_STREAM",
        "source": source,
        "sha256": sha256_bytes(payload),
        "file_size": len(payload),
        "timeout_seconds": timeout_seconds,
    }


def demo_frame() -> tuple[bytes, dict[str, Any]]:
    """Return a deterministic fixture; only valid for explicit test/demo mode."""
    if os.getenv("RTIN_ALLOW_DEMO_CCTV", "0") != "1":
        raise VisionCaptureError("Demo CCTV frame is disabled")
    payload = DEMO_JPEG
    return payload, {
        "capture_mode": "DEMO_FIXTURE",
        "source": "embedded-test-fixture",
        "sha256": sha256_bytes(payload),
        "file_size": len(payload),
    }


def detect_people(
    frame_bgr: Any,
    *,
    model_path: str | None = None,
    confidence: float = 0.35,
) -> list[Detection]:
    """Detect people (COCO class 0) with an Ultralytics YOLO model."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise VisionDependencyError(
            "Ultralytics is not installed. Install services/api/requirements-vision.txt"
        ) from exc

    weights = model_path or os.getenv("YOLO_MODEL_PATH")
    if not weights:
        raise VisionCaptureError(
            "YOLO_MODEL_PATH is not configured; provide a real YOLO weights file"
        )

    model = YOLO(weights)
    results = model.predict(
        source=frame_bgr,
        conf=confidence,
        classes=[0],
        verbose=False,
    )

    detections: list[Detection] = []
    if not results:
        return detections

    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    classes = boxes.cls.cpu().numpy()

    for coords, score, cls_id in zip(xyxy, confs, classes):
        if int(cls_id) != 0:
            continue
        x1, y1, x2, y2 = [int(v) for v in coords.tolist()]
        detections.append(
            Detection(
                class_id=0,
                confidence=float(score),
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )
        )

    return detections




def track_people(
    frame_bgr: Any,
    *,
    model_path: str | None = None,
    confidence: float = 0.35,
    tracker: str = "bytetrack.yaml",
) -> list[Detection]:
    """Track people with Ultralytics' built-in ByteTrack/BoT-SORT backends."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise VisionDependencyError(
            "Ultralytics is not installed. Install services/api/requirements-vision.txt"
        ) from exc

    weights = model_path or os.getenv("YOLO_MODEL_PATH")
    if not weights:
        raise VisionCaptureError(
            "YOLO_MODEL_PATH is not configured; provide a real YOLO weights file"
        )

    model = YOLO(weights)
    results = model.track(
        source=frame_bgr,
        conf=confidence,
        classes=[0],
        tracker=tracker,
        persist=True,
        verbose=False,
    )

    detections: list[Detection] = []
    if not results:
        return detections

    result = results[0]
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    classes = boxes.cls.cpu().numpy()
    ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else [None] * len(xyxy)

    for coords, score, cls_id, track_id in zip(xyxy, confs, classes, ids):
        if int(cls_id) != 0:
            continue
        x1, y1, x2, y2 = [int(v) for v in coords.tolist()]
        detections.append(
            Detection(
                class_id=0,
                confidence=float(score),
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                track_id=None if track_id is None else int(track_id),
            )
        )

    return detections

def analyze_stream_once(
    source: str,
    *,
    model_path: str | None = None,
    confidence: float = 0.35,
    tracking: bool = False,
) -> dict[str, Any]:
    """Capture one frame and run person detection on it."""
    try:
        frame_bytes, capture_meta = capture_frame(source)
    except (VisionDependencyError, VisionCaptureError):
        if os.getenv("RTIN_ALLOW_DEMO_CCTV", "0") == "1":
            frame_bytes, capture_meta = demo_frame()
        else:
            raise

    try:
        import cv2
    except ImportError as exc:
        raise VisionDependencyError(
            "OpenCV is not installed. Install services/api/requirements-vision.txt"
        ) from exc

    import numpy as np

    frame = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise VisionCaptureError("Captured JPEG could not be decoded")

    detections = (
        track_people(
            frame,
            model_path=model_path,
            confidence=confidence,
        )
        if tracking
        else detect_people(
            frame,
            model_path=model_path,
            confidence=confidence,
        )
    )
    return {
        "person_count": len(detections),
        "tracking_enabled": tracking,
        "detections": [
            {
                "confidence": round(d.confidence, 4),
                "bbox": [d.x1, d.y1, d.x2, d.y2],
                "track_id": d.track_id,
            }
            for d in detections
        ],
        "capture": capture_meta,
    }
