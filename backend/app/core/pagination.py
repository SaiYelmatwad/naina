from fastapi import Query
from sqlalchemy.orm import Query as ORMQuery

from app.config import settings


def pagination_params(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(
        settings.default_page_size, ge=1, le=settings.max_page_size, description="Items per page"
    ),
):
    return {"page": page, "page_size": page_size}


def paginate(query: ORMQuery, page: int, page_size: int) -> tuple[list, int]:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total
