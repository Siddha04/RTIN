from types import SimpleNamespace

from services.ai.assignment_optimizer import (
    assign_targets,
    institution_priority,
    select_targets,
)


def test_high_risk_target_is_prioritized():
    low = SimpleNamespace(id="INS-001", report_variance=0.01)
    high = SimpleNamespace(id="INS-002", report_variance=0.20)
    low_risk = SimpleNamespace(risk_score=20, anomaly=False)
    high_risk = SimpleNamespace(risk_score=85, anomaly=True)

    low_score, _ = institution_priority(low, low_risk)
    high_score, _ = institution_priority(high, high_risk)

    assert high_score > low_score


def test_target_selection_is_deterministic():
    institutions = [
        SimpleNamespace(id="INS-002", report_variance=0.10),
        SimpleNamespace(id="INS-001", report_variance=0.10),
    ]
    risk = {
        "INS-001": SimpleNamespace(risk_score=70, anomaly=False),
        "INS-002": SimpleNamespace(risk_score=70, anomaly=False),
    }

    first = select_targets(institutions, risk, 2)
    second = select_targets(institutions, risk, 2)

    assert [row[0].id for row in first] == [row[0].id for row in second]
    assert [row[0].id for row in first] == ["INS-001", "INS-002"]


def test_assignment_excludes_home_district_and_recent_pairings():
    institution = SimpleNamespace(id="INS-001", district="Salem")
    good = SimpleNamespace(
        id="USR-01",
        assigned_district="Salem",
        home_district="Chennai",
    )
    home_conflict = SimpleNamespace(
        id="USR-02",
        assigned_district="Salem",
        home_district="Salem",
    )
    targets = [(institution, "risk=80.0", 80.0)]

    assignments = assign_targets(
        targets,
        [home_conflict, good],
        recent_pairings=set(),
    )

    assert len(assignments) == 1
    assert assignments[0]["inspector"].id == "USR-01"


def test_assignment_respects_cooling_period():
    institution = SimpleNamespace(id="INS-001", district="Salem")
    inspector = SimpleNamespace(
        id="USR-01",
        assigned_district="Salem",
        home_district="Chennai",
    )

    assignments = assign_targets(
        [(institution, "risk=80", 80)],
        [inspector],
        recent_pairings={("USR-01", "INS-001")},
    )

    assert assignments == []
