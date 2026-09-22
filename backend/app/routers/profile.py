from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=schemas.UserOut)
def read_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/skills", response_model=list[schemas.SkillOut])
def list_skills(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Skill).filter(models.Skill.owner_id == current_user.id).all()


@router.post("/skills", response_model=schemas.SkillOut, status_code=201)
def add_skill(
    payload: schemas.SkillIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    skill = models.Skill(**payload.model_dump(), owner_id=current_user.id)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    skill = (
        db.query(models.Skill)
        .filter(models.Skill.id == skill_id, models.Skill.owner_id == current_user.id)
        .first()
    )
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
