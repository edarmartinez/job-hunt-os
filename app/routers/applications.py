from __future__ import annotations
from typing import List, Optional, Iterable, Dict
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, asc, desc
from ..database import get_db, engine, Base
from ..models import Application
from ..schemas import ApplicationCreate, ApplicationUpdate, ApplicationOut, ListQueryParams, EMPLOYMENT_TYPES, STAGES, STATUSES
from ..deps import require_api_key
from ..utils.csv_export import iter_csv

router = APIRouter()

# Create tables if missing (simple MVP). In real life, use Alembic migrations.
Base.metadata.create_all(bind=engine)

def _validate_business_rules(payload: ApplicationCreate | ApplicationUpdate):
    # Custom 400s instead of 422 for certain rules
    if payload.salary_min is not None and payload.salary_max is not None:
        if payload.salary_min > payload.salary_max:
            raise HTTPException(status_code=400, detail="salary_min must be <= salary_max")
    if payload.employment_type is not None and payload.employment_type not in EMPLOYMENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid employment_type")
    if payload.stage is not None and payload.stage not in STAGES:
        raise HTTPException(status_code=400, detail="Invalid stage")
    if payload.status is not None and payload.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

def _apply_filters(stmt, params: ListQueryParams):
    if params.search:
        s = f"%{params.search.lower()}%"
        stmt = stmt.where(or_(func.lower(Application.company).like(s), func.lower(Application.role).like(s)))
    if params.stage:
        stmt = stmt.where(Application.stage == params.stage)
    if params.status:
        stmt = stmt.where(Application.status == params.status)
    return stmt

def _apply_ordering(stmt, params: ListQueryParams):
    # Secondary sort by id for stability
    col = getattr(Application, params.order_by)
    ordering = asc(col) if params.order_dir == "asc" else desc(col)
    return stmt.order_by(ordering, desc(Application.id))

@router.get("/applications", response_model=dict)
def list_applications(
    search: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    order_by: str = "created_at",
    order_dir: str = "desc",
    db: Session = Depends(get_db),
):
    params = ListQueryParams(
        search=search,
        stage=stage,
        status=status,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )
    # Convert invalid enum/order values into 400s
    try:
        params.validate_enums()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    base_stmt = select(Application)
    base_stmt = _apply_filters(base_stmt, params)
    count_stmt = select(func.count()).select_from(_apply_filters(select(Application), params).subquery())

    total = db.execute(count_stmt).scalar_one()

    base_stmt = _apply_ordering(base_stmt, params)
    base_stmt = base_stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

    items = db.execute(base_stmt).scalars().all()
    out_items = [ApplicationOut.model_validate(i) for i in items]

    return {
        "items": [i.model_dump() for i in out_items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
    }

@router.get("/applications/{app_id}", response_model=ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    obj = db.get(Application, app_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return ApplicationOut.model_validate(obj)

@router.post("/applications", response_model=ApplicationOut, dependencies=[Depends(require_api_key)])
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    _validate_business_rules(payload)
    obj = Application(
        company=payload.company,
        role=payload.role,
        location=payload.location,
        source=payload.source,
        link=str(payload.link) if payload.link else None,
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        employment_type=payload.employment_type,
        stage=payload.stage,
        status=payload.status,
        next_action_date=payload.next_action_date,
        notes=payload.notes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return ApplicationOut.model_validate(obj)

@router.put("/applications/{app_id}", response_model=ApplicationOut, dependencies=[Depends(require_api_key)])
def update_application(app_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    _validate_business_rules(payload)
    obj = db.get(Application, app_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "link" and value is not None:
            setattr(obj, field, str(value))
        else:
            setattr(obj, field, value)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return ApplicationOut.model_validate(obj)

@router.delete("/applications/{app_id}", status_code=204, dependencies=[Depends(require_api_key)])
def delete_application(app_id: int, db: Session = Depends(get_db)):
    obj = db.get(Application, app_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(obj)
    db.commit()
    return Response(status_code=204)

@router.get("/export.csv")
def export_csv(
    search: Optional[str] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
    db: Session = Depends(get_db),
):
    """
    Stream a CSV of the filtered set by internally paginating with page_size <= 100.
    """
    # Validate enums/order inputs once
    base_params = ListQueryParams(
        search=search, stage=stage, status=status,
        order_by=order_by, order_dir=order_dir,
        page=1, page_size=100  # respect the cap
    )
    try:
        base_params.validate_enums()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    def row_iter() -> Iterable[Dict[str, object]]:
        # header row first (iter_csv writes rows as-is)
        yield {
            "id": "id",
            "company": "company",
            "role": "role",
            "location": "location",
            "source": "source",
            "link": "link",
            "salary_min": "salary_min",
            "salary_max": "salary_max",
            "employment_type": "employment_type",
            "stage": "stage",
            "status": "status",
            "next_action_date": "next_action_date",
            "notes": "notes",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }

        page = 1
        while True:
            params = ListQueryParams(
                search=search,
                stage=stage,
                status=status,
                order_by=order_by,
                order_dir=order_dir,
                page=page,
                page_size=base_params.page_size,
            )

            stmt = select(Application)
            stmt = _apply_filters(stmt, params)
            stmt = _apply_ordering(stmt, params)
            stmt = stmt.offset((params.page - 1) * params.page_size).limit(params.page_size)

            rows = db.execute(stmt).scalars().all()
            if not rows:
                break

            for r in rows:
                yield {
                    "id": r.id,
                    "company": r.company,
                    "role": r.role,
                    "location": r.location,
                    "source": r.source,
                    "link": r.link,
                    "salary_min": r.salary_min,
                    "salary_max": r.salary_max,
                    "employment_type": r.employment_type,
                    "stage": r.stage,
                    "status": r.status,
                    "next_action_date": r.next_action_date.isoformat() if r.next_action_date else None,
                    "notes": r.notes,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                }

            page += 1

    from starlette.responses import StreamingResponse
    return StreamingResponse(
        iter_csv(row_iter()),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'}
    )
