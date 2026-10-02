from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.deps import current_user_id, db_session
from app.models.nutrition import NutritionEntry
from app.schemas.nutrition import *

router = APIRouter(prefix="/nutrition", tags=["nutrition"])


@router.post("", response_model=NutritionResponse, status_code=201)
def create(
    p: NutritionCreate, uid=Depends(current_user_id), db: Session = Depends(db_session)
):
    x = NutritionEntry(user_id=uid, **p.model_dump())
    db.add(x)
    db.commit()
    db.refresh(x)
    return x


@router.get("", response_model=NutritionPage)
def listing(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    uid=Depends(current_user_id),
    db: Session = Depends(db_session),
):
    q = select(NutritionEntry).where(NutritionEntry.user_id == uid)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    items = db.scalars(
        q.order_by(NutritionEntry.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return NutritionPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{eid}", response_model=NutritionResponse)
def get(eid: int, uid=Depends(current_user_id), db: Session = Depends(db_session)):
    x = db.scalar(
        select(NutritionEntry).where(
            NutritionEntry.id == eid, NutritionEntry.user_id == uid
        )
    )
    if not x:
        raise HTTPException(404, "Nutrition entry not found")
    return x


@router.patch("/{eid}", response_model=NutritionResponse)
def update(
    eid: int,
    p: NutritionUpdate,
    uid=Depends(current_user_id),
    db: Session = Depends(db_session),
):
    x = db.scalar(
        select(NutritionEntry).where(
            NutritionEntry.id == eid, NutritionEntry.user_id == uid
        )
    )
    if not x:
        raise HTTPException(404, "Nutrition entry not found")
    for k, v in p.model_dump(exclude_unset=True).items():
        setattr(x, k, v)
    db.commit()
    db.refresh(x)
    return x


@router.delete("/{eid}", status_code=204)
def delete(eid: int, uid=Depends(current_user_id), db: Session = Depends(db_session)):
    x = db.scalar(
        select(NutritionEntry).where(
            NutritionEntry.id == eid, NutritionEntry.user_id == uid
        )
    )
    if not x:
        raise HTTPException(404, "Nutrition entry not found")
    db.delete(x)
    db.commit()
