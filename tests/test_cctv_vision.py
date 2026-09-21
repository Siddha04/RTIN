import os
import sys
from types import ModuleType, SimpleNamespace

os.environ.setdefault("RTIN_ALLOW_DEMO_CCTV", "1")

from services.ai.vision import DEMO_JPEG, Detection, demo_frame, detect_people, sha256_bytes


def test_demo_frame_is_explicit_and_hashable():
    payload, meta = demo_frame()
    assert payload == DEMO_JPEG
    assert meta["capture_mode"] == "DEMO_FIXTURE"
    assert meta["sha256"] == sha256_bytes(payload)
    assert meta["file_size"] == len(payload)


def test_detection_contract_without_real_ultralytics(monkeypatch):
    class FakeTensor:
        def __init__(self, values):
            self.values = values

        def cpu(self):
            return self

        def numpy(self):
            import numpy as np
            return np.array(self.values)

    class FakeBoxes:
        xyxy = FakeTensor([[10, 20, 110, 220], [5, 5, 25, 35]])
        conf = FakeTensor([0.91, 0.31])
        cls = FakeTensor([0, 0])

    class FakeResult:
        boxes = FakeBoxes()

    class FakeYOLO:
        def __init__(self, path):
            assert path == "fake-yolo.pt"

        def predict(self, **kwargs):
            assert kwargs["classes"] == [0]
            return [FakeResult()]

    fake_module = ModuleType("ultralytics")
    fake_module.YOLO = FakeYOLO
    monkeypatch.setitem(sys.modules, "ultralytics", fake_module)

    detections = detect_people(
        object(),
        model_path="fake-yolo.pt",
        confidence=0.35,
    )

    assert len(detections) == 2
    assert isinstance(detections[0], Detection)
    assert detections[0].class_id == 0
    assert detections[0].confidence == 0.91


def test_negative_confidence_is_not_a_valid_detector_contract():
    assert 0.0 < 0.35 < 1.0
