from __future__ import annotations
from typing import Optional, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, HttpUrl, ConfigDict

EMPLOYMENT_TYPES = {"full-time", "contract", "intern"}
STAGES = {"wishlist", "applied", "oa", "phone", "onsite", "offer", "rejected", "ghosted"}
STATUSES = {"active", "closed"}

class ApplicationBase(BaseModel):
    company: str = Field(..., max_length=200)
    role: str = Field(..., max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    source: Optional[str] = Field(None, max_length=200)
    link: Optional[HttpUrl] = Field(None)
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[str] = Field(None)  # validated manually to return 400 instead of 422
    stage: Optional[str] = Field(None)            # same
    status: Optional[str] = Field(None)           # same
    next_action_date: Optional[date] = None
    notes: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    company: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    source: Optional[str] = Field(None, max_length=200)
    link: Optional[HttpUrl] = None
    salary_min: Optional[int] = Field(None, ge=0)
    salary_max: Optional[int] = Field(None, ge=0)
    employment_type: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    next_action_date: Optional[date] = None
    notes: Optional[str] = None

class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company: str
    role: str
    location: Optional[str]
    source: Optional[str]
    link: Optional[HttpUrl]
    salary_min: Optional[int]
    salary_max: Optional[int]
    employment_type: Optional[str]
    stage: Optional[str]
    status: Optional[str]
    next_action_date: Optional[date]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class ListQueryParams(BaseModel):
    search: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    order_by: str = Field("created_at")
    order_dir: str = Field("desc")

    def validate_enums(self):
        if self.stage is not None and self.stage not in STAGES:
            raise ValueError("Invalid stage")
        if self.status is not None and self.status not in STATUSES:
            raise ValueError("Invalid status")
        if self.order_by not in {"created_at", "updated_at", "next_action_date"}:
            raise ValueError("Invalid order_by")
        if self.order_dir not in {"asc", "desc"}:
            raise ValueError("Invalid order_dir")
