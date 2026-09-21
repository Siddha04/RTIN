"""Document OCR, classification and consistency analysis.

OCR is optional and loaded lazily. Classification uses a supervised TF-IDF
+ LogisticRegression pipeline only when caller-supplied labeled examples are
available. No hidden document labels are embedded in the application.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class DocumentDependencyError(RuntimeError):
    """Raised when optional OCR dependencies are missing."""


class DocumentAnalysisError(RuntimeError):
    """Raised when a document cannot be analyzed."""


@dataclass
class OCRResult:
    text: str
    confidence: float
    provider: str


def ocr_image(image_bytes: bytes, language: str = "eng") -> OCRResult:
    if not image_bytes:
        raise DocumentAnalysisError("document image is empty")

    try:
        from PIL import Image
        import pytesseract
    except ImportError as exc:
        raise DocumentDependencyError(
            "Install services/api/requirements-documents.txt for OCR"
        ) from exc

    try:
        image = Image.open(io.BytesIO(image_bytes))
        data = pytesseract.image_to_data(
            image,
            lang=language,
            output_type=pytesseract.Output.DICT,
        )
        text = pytesseract.image_to_string(image, lang=language).strip()
    except Exception as exc:
        raise DocumentAnalysisError(f"OCR failed: {exc}") from exc

    confidences = []
    for raw in data.get("conf", []):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value >= 0:
            confidences.append(value)

    confidence = (
        round(sum(confidences) / len(confidences) / 100.0, 3)
        if confidences
        else 0.0
    )
    return OCRResult(text=text, confidence=confidence, provider="tesseract")


def normalize_text(text: str) -> str:
    return " ".join((text or "").split())


def extract_fields(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)

    patterns = {
        "institution_id": r"(?:institution|inst)[ ]*(?:id|no|number)?[ ]*[:#_-]?[ ]*([A-Z]{2,8}-[0-9]{3,8})(?:[^A-Z0-9]|$)",
        "attendance_rate": r"attendance(?:[ ]+rate)?[ ]*[:=-][ ]*([0-9]{1,3}(?:[.][0-9]+)?)[ ]*%",
        "beneficiary_count": r"beneficiar(?:y|ies)[ ]*(?:count|total)?[ ]*[:=-][ ]*([0-9]{1,6})(?:[^0-9]|$)",
        "grant_amount": r"(?:grant|fund|sanctioned[ ]+amount)[ ]*[:=-][ ]*(?:INR|Rs[.]?)?[ ]*([0-9,]+(?:[.][0-9]+)?)",
        "reference_number": r"(?:reference|ref|file)[ ]*(?:no|number)?[ ]*[:=-][ ]*([A-Z0-9/_-]{4,40})(?:[^A-Z0-9/_-]|$)",
        "report_date": r"(?:report[ ]+date|date)[ ]*[:=-][ ]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})(?:[^0-9/-]|$)",
    }

    output: dict[str, Any] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            output[field] = None
            continue
        value = match.group(1).strip()
        if field == "attendance_rate":
            output[field] = float(value)
        elif field == "beneficiary_count":
            output[field] = int(value)
        elif field == "grant_amount":
            output[field] = float(value.replace(",", ""))
        else:
            output[field] = value
    return output


class DocumentClassifier:
    """TF-IDF + LogisticRegression classifier trained from supplied labels."""

    def __init__(self) -> None:
        self._pipeline = None
        self._classes: list[str] = []

    def fit(self, texts: Sequence[str], labels: Sequence[str]) -> dict[str, Any]:
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        if len(set(labels)) < 2:
            raise ValueError("at least two document classes are required")
        if len(texts) < 6:
            raise ValueError("at least 6 labeled documents are required")

        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline

        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=1,
                max_features=5000,
            )),
            ("classifier", LogisticRegression(
                max_iter=1000,
                random_state=42,
            )),
        ])
        self._pipeline.fit(list(texts), list(labels))
        self._classes = [str(value) for value in self._pipeline.classes_]
        return {
            "status": "TRAINED",
            "model": "tfidf-logistic-regression",
            "classes": self._classes,
            "samples": len(texts),
        }

    def predict(self, text: str) -> dict[str, Any]:
        if self._pipeline is None:
            return {
                "status": "MODEL_NOT_TRAINED",
                "label": None,
                "confidence": 0.0,
            }

        prediction = str(self._pipeline.predict([text])[0])
        probabilities = self._pipeline.predict_proba([text])[0]
        confidence = float(max(probabilities))
        return {
            "status": "PREDICTED",
            "label": prediction,
            "confidence": round(confidence, 3),
        }


def compare_documents(documents: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Find field conflicts across extracted document records."""
    fields = (
        "institution_id",
        "attendance_rate",
        "beneficiary_count",
        "grant_amount",
        "reference_number",
        "report_date",
    )
    conflicts: list[dict[str, Any]] = []
    for field in fields:
        values = [
            document.get(field)
            for document in documents
            if document.get(field) is not None
        ]
        unique = {str(value) for value in values}
        if len(unique) > 1:
            conflicts.append({
                "field": field,
                "values": values,
                "status": "CONFLICT",
            })

    return {
        "document_count": len(documents),
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "status": "CONFLICTS_FOUND" if conflicts else "CONSISTENT",
    }