import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.pagination import paginate, pagination_params
from app.database import get_db
from app.deps import get_current_user
from app.matching.scorer import score_role

router = APIRouter(prefix="/scan", tags=["scan"])
logger = logging.getLogger("signalwork")


@router.post("", response_model=schemas.ScanResult)
def run_scan(
    payload: schemas.ScanRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    skills = [
        {"name": s.name, "level": s.level}
        for s in db.query(models.Skill).filter(models.Skill.owner_id == current_user.id).all()
    ]
    result = score_role(payload.role_text, skills)

    # Persist the scan for history / trend tracking.
    record = models.Scan(
        owner_id=current_user.id,
        role_text=payload.role_text,
        score=result.score,
        matched_skills=",".join(m.skill for m in result.matched),
        gap_skills=",".join(g.skill for g in result.gaps),
    )
    db.add(record)
    db.commit()

    logger.info(
        "scan_completed user_id=%s score=%s matched=%s gaps=%s",
        current_user.id,
        result.score,
        len(result.matched),
        len(result.gaps),
    )

    return schemas.ScanResult(
        score=result.score,
        verdict=result.verdict,
        matched=[
            schemas.SkillSignal(skill=m.skill, level=m.level, weight=m.weight) for m in result.matched
        ],
        gaps=[schemas.SkillSignal(skill=g.skill, level=g.level, weight=g.weight) for g in result.gaps],
        explanation=result.explanation,
    )


@router.get("/history", response_model=schemas.ScanHistoryPage)
def scan_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    pagination: dict = Depends(pagination_params),
):
    query = (
        db.query(models.Scan)
        .filter(models.Scan.owner_id == current_user.id)
        .order_by(models.Scan.created_at.desc())
    )
    items, total = paginate(query, pagination["page"], pagination["page_size"])
    has_next = pagination["page"] * pagination["page_size"] < total
    return schemas.ScanHistoryPage(
        items=items,
        meta=schemas.PageMeta(
            total=total, page=pagination["page"], page_size=pagination["page_size"], has_next=has_next
        ),
    )
