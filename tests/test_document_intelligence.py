from services.ai.documents import DocumentClassifier, compare_documents, extract_fields


def test_document_field_extraction():
    text = (
        "Institution ID: INS-001 "
        "Attendance Rate: 82.5% "
        "Beneficiaries: 58 "
        "Grant Amount: INR 125,000 "
        "Reference No: DOSJE/2026/441 "
        "Report Date: 21/09/2026"
    )
    fields = extract_fields(text)

    assert fields["institution_id"] == "INS-001"
    assert fields["attendance_rate"] == 82.5
    assert fields["beneficiary_count"] == 58
    assert fields["grant_amount"] == 125000.0
    assert fields["reference_number"] == "DOSJE/2026/441"
    assert fields["report_date"] == "21/09/2026"


def test_document_consistency_detects_conflicting_fields():
    result = compare_documents([
        {"institution_id": "INS-001", "beneficiary_count": 58},
        {"institution_id": "INS-001", "beneficiary_count": 66},
    ])

    assert result["status"] == "CONFLICTS_FOUND"
    assert result["conflict_count"] == 1
    assert result["conflicts"][0]["field"] == "beneficiary_count"


def test_document_classifier_requires_explicit_labeled_training_data():
    classifier = DocumentClassifier()
    texts = [
        "attendance register beneficiary attendance daily biometric",
        "attendance sheet present absent staff roll",
        "beneficiary attendance monthly register",
        "grant utilization expenditure sanctioned amount fund statement",
        "utilization certificate grant expenditure balance",
        "financial grant statement sanctioned release expenditure",
    ]
    labels = ["ATTENDANCE"] * 3 + ["FINANCIAL"] * 3

    train = classifier.fit(texts, labels)
    prediction = classifier.predict("sanctioned grant expenditure utilization statement")

    assert train["status"] == "TRAINED"
    assert train["samples"] == 6
    assert set(train["classes"]) == {"ATTENDANCE", "FINANCIAL"}
    assert prediction["status"] == "PREDICTED"
    assert prediction["label"] in {"ATTENDANCE", "FINANCIAL"}
    assert 0.0 <= prediction["confidence"] <= 1.0
