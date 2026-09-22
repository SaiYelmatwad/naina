import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------- Auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    # Upper bound matters, not just a lower one: bcrypt silently truncates at
    # 72 bytes, so an unbounded password gives users a false sense of length.
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(default="", max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Skills ----------
class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    level: float = Field(ge=0, le=1, default=0.5)
    category: str = Field(default="general", max_length=60)


class SkillOut(SkillIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Scan ----------
class ScanRequest(BaseModel):
    # Upper bound protects the TF-IDF/vector step from pathological input
    # (someone pasting an entire PDF) from turning into an O(n) CPU spike.
    role_text: str = Field(min_length=3, max_length=8000)


class SkillSignal(BaseModel):
    skill: str
    level: float
    weight: float


class ScanResult(BaseModel):
    score: int
    verdict: str
    matched: list[SkillSignal]
    gaps: list[SkillSignal]
    explanation: list[str]


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role_text: str
    score: float
    created_at: dt.datetime


# ---------- Applications ----------
ALLOWED_STATUSES = {"applied", "interview", "offer", "rejected"}


class ApplicationIn(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role_title: str = Field(min_length=1, max_length=200)
    status: str = Field(default="applied")
    match_score: float | None = Field(default=None, ge=0, le=100)

    @field_validator("status")
    @classmethod
    def status_must_be_known(cls, v: str) -> str:
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"status must be one of {sorted(ALLOWED_STATUSES)}")
        return v


class ApplicationOut(ApplicationIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: dt.datetime


# ---------- Pagination ----------
class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int
    has_next: bool


class ScanHistoryPage(BaseModel):
    items: list[ScanOut]
    meta: PageMeta


class ApplicationPage(BaseModel):
    items: list[ApplicationOut]
    meta: PageMeta
