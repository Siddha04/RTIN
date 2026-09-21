"""Deterministic risk-aware inspection assignment optimizer."""

from __future__ import annotations

from typing import Any, Iterable


def _text(value: Any) -> str:
    return str(value or "").strip().lower()


def institution_priority(
    institution: Any,
    risk_record: Any | None,
) -> tuple[float, str]:
    risk = float(getattr(risk_record, "risk_score", 0.0) or 0.0)
    anomaly = bool(getattr(risk_record, "anomaly", False))
    variance = float(getattr(institution, "report_variance", 0.0) or 0.0)
    priority = (
        0.65 * risk
        + 20.0 * float(anomaly)
        + 15.0 * min(variance / 0.30, 1.0)
    )
    reason = (
        f"risk={risk:.1f}; anomaly={'yes' if anomaly else 'no'}; "
        f"report_variance={variance:.3f}"
    )
    return priority, reason


def inspector_pair_score(
    inspector: Any,
    institution: Any,
    workload: dict[str, int],
) -> tuple[float, str]:
    score = 0.0
    reasons: list[str] = []

    assigned = _text(getattr(inspector, "assigned_district", ""))
    district = _text(getattr(institution, "district", ""))
    home = _text(getattr(inspector, "home_district", ""))

    if assigned and district and assigned == district:
        score += 15.0
        reasons.append("assigned-district match")

    if home and district and home == district:
        return -10_000.0, "home-district conflict"

    load = workload.get(str(inspector.id), 0)
    score -= 10.0 * load
    reasons.append(f"current_load={load}")

    return score, "; ".join(reasons)


def select_targets(
    institutions: Iterable[Any],
    risk_by_institution: dict[str, Any],
    target_count: int,
) -> list[tuple[Any, str, float]]:
    scored = []
    for institution in institutions:
        risk_record = risk_by_institution.get(str(institution.id))
        score, reason = institution_priority(institution, risk_record)
        scored.append((institution, reason, score))

    scored.sort(key=lambda item: (-item[2], str(item[0].id)))
    return scored[: max(0, target_count)]


def assign_targets(
    targets: list[tuple[Any, str, float]],
    inspectors: Iterable[Any],
    recent_pairings: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    workload: dict[str, int] = {}
    assignments: list[dict[str, Any]] = []
    inspectors_sorted = sorted(inspectors, key=lambda value: str(value.id))

    for institution, target_reason, target_score in targets:
        candidates = []
        for inspector in inspectors_sorted:
            inspector_id = str(inspector.id)
            institution_id = str(institution.id)

            if (inspector_id, institution_id) in recent_pairings:
                continue

            pair_score, pair_reason = inspector_pair_score(
                inspector, institution, workload
            )
            if pair_score <= -10_000.0:
                continue

            candidates.append((pair_score, inspector_id, inspector, pair_reason))

        if not candidates:
            continue

        candidates.sort(key=lambda item: (-item[0], item[1]))
        pair_score, inspector_id, inspector, pair_reason = candidates[0]
        workload[inspector_id] = workload.get(inspector_id, 0) + 1

        assignments.append({
            "institution": institution,
            "inspector": inspector,
            "target_score": round(target_score, 3),
            "target_reason": target_reason,
            "pair_score": round(pair_score, 3),
            "pair_reason": pair_reason,
        })

    return assignments
