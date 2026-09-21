# INSPECT-AI AI Engine — Phase 4

Phase 4 adds document intelligence.

## Pipeline

Document image
-> OCR (Tesseract)
-> normalized text
-> structured field extraction
-> optional supervised document classification (TF-IDF + Logistic Regression)
-> cross-document consistency checks

## Production behavior

OCR dependencies are optional and documented in services/api/requirements-documents.txt. The API returns a clear service-unavailable response when the OCR runtime is not installed instead of silently returning fabricated text.

The classifier is never trained from hidden labels. A caller must provide labeled documents before a model can be fitted.
