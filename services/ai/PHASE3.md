# INSPECT-AI AI Engine — Phase 3

Phase 3 adds the real computer-vision path for CCTV evidence and occupancy analytics.

## Runtime model

- OpenCV captures a frame from local, HTTP, or RTSP CCTV sources.
- Ultralytics YOLO detects COCO person class 0.
- Ultralytics tracking can use ByteTrack or BoT-SORT.
- Person count is written back to the CCTV feed.
- A CCTV observation is persisted into institutional AI history.
- Risk analysis therefore receives a measured CCTV headcount rather than an invented value.
- Snapshot evidence stores the SHA-256 of the actual captured JPEG bytes.

## Production configuration

Install optional vision dependencies:
pip install -r services/api/requirements-vision.txt

Configure:
YOLO_MODEL_PATH=/absolute/path/to/your/yolo-weights.pt

Do not enable RTIN_ALLOW_DEMO_CCTV in production.

## Test strategy

CI does not download YOLO/PyTorch weights. Vision unit tests mock the Ultralytics interface, while CCTV regression tests use an explicit embedded demo fixture. This keeps tests deterministic and prevents a test suite from treating a sample video as live surveillance.
