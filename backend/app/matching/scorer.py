"""
Core scoring logic: given a user's skill profile and a job posting's text,
produce a match score, ranked matched skills, ranked gaps, and a short
plain-language explanation for each — no black-box percentage.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.matching.embeddings import get_embedding_provider

MATCH_THRESHOLD = 0.30  # similarity above this counts a skill as "present" in the role text


@dataclass
class SkillScore:
    skill: str
    level: float
    weight: float  # how strongly the role text implies this skill (0-1)


@dataclass
class ScanResult:
    score: int
    verdict: str
    matched: list[SkillScore]
    gaps: list[SkillScore]
    explanation: list[str]


def _verdict(score: int) -> str:
    if score >= 75:
        return "Strong fit"
    if score >= 50:
        return "Worth applying"
    return "Reach role"


def score_role(role_text: str, skills: list[dict]) -> ScanResult:
    """
    skills: list of {"name": str, "level": float} from the user's stored profile.
    """
    provider = get_embedding_provider()

    weighted = []
    for s in skills:
        weight = provider.similarity(role_text, s["name"])
        weighted.append(SkillScore(skill=s["name"], level=s["level"], weight=weight))

    present = [w for w in weighted if w.weight >= MATCH_THRESHOLD]
    matched = sorted([w for w in present if w.level >= 0.55], key=lambda w: -w.weight)
    gaps = sorted([w for w in present if w.level < 0.55], key=lambda w: -w.weight)

    if not present:
        # Nothing in the profile maps to this posting at all.
        return ScanResult(
            score=20,
            verdict="Reach role",
            matched=[],
            gaps=[],
            explanation=["No strong overlap found between this posting and your current profile."],
        )

    avg_relevance = sum(w.weight for w in present) / len(present)
    avg_level_of_relevant = sum(w.level for w in present) / len(present)
    coverage = len(matched) / max(len(present), 1)

    raw = (coverage * 0.45) + (avg_level_of_relevant * 0.35) + (avg_relevance * 0.20)
    score = int(round(max(15, min(97, raw * 100))))

    explanation = []
    for m in matched[:3]:
        pct = round(m.level * 100)
        explanation.append(f"{m.skill}: strong match — profile level {pct}%.")
    for g in gaps[:3]:
        pct = round(g.level * 100)
        explanation.append(f"{g.skill}: gap — role signal detected, profile level only {pct}%.")

    fallback = ["Role text scanned; no individual skill crossed the reporting threshold."]

    return ScanResult(
        score=score,
        verdict=_verdict(score),
        matched=matched[:8],
        gaps=gaps[:8],
        explanation=explanation or fallback,
    )
