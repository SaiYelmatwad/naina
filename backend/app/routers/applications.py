from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.pagination import paginate, pagination_params
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])


def _get_owned_application(db: Session, application_id: int, owner_id: int) -> models.Application:
    row = (
        db.query(models.Application)
        .filter(models.Application.id == application_id, models.Application.owner_id == owner_id)
        .first()
    )
    if not row:
        # Same 404 whether the row doesn't exist or belongs to someone else —
        # never leak which one it is, that's an enumeration/authorization leak.
        raise HTTPException(status_code=404, detail="Application not found")
    return row


@router.get("", response_model=schemas.ApplicationPage)
def list_applications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    pagination: dict = Depends(pagination_params),
):
    query = (
        db.query(models.Application)
        .filter(models.Application.owner_id == current_user.id)
        .order_by(models.Application.created_at.desc())
    )
    items, total = paginate(query, pagination["page"], pagination["page_size"])
    has_next = pagination["page"] * pagination["page_size"] < total
    return schemas.ApplicationPage(
        items=items,
        meta=schemas.PageMeta(
            total=total, page=pagination["page"], page_size=pagination["page_size"], has_next=has_next
        ),
    )


@router.post("", response_model=schemas.ApplicationOut, status_code=201)
def create_application(
    payload: schemas.ApplicationIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    app_row = models.Application(**payload.model_dump(), owner_id=current_user.id)
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return app_row


@router.patch("/{application_id}", response_model=schemas.ApplicationOut)
def update_application(
    application_id: int,
    payload: schemas.ApplicationIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    row = _get_owned_application(db, application_id, current_user.id)
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    row = _get_owned_application(db, application_id, current_user.id)
    db.delete(row)
    db.commit()
