
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class Status(str, Enum):
    APPLIED = "Applied"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    status: Status
    job_url: str | None = None
    follow_up: date | None = None
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    source: str = Field(min_length=1, max_length=100)
    status: Status
    job_url: str | None = None
    follow_up: date | None = None
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: int
    company: str
    role: str
    source: str
    status: Status
    job_url: str | None = None
    follow_up: date | None = None
    notes: str | None = None

    model_config = {
        "from_attributes": True
    }


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: str
    password: str
