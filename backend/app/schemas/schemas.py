from pydantic import BaseModel, ConfigDict, Field
from app.models.models import UserRole, ApplicationStatus

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)
    role: UserRole = UserRole.client

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    role: UserRole

class CompanyCreate(BaseModel):
    inn: str = Field(min_length=10, max_length=12)
    name: str
    okved: str
    revenue: float = 0
    debt: float = 0
    overdue_days: int = 0

class CompanyOut(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class ApplicationCreate(BaseModel):
    company_id: int
    product: str
    amount: float = Field(gt=0)
    term_months: int = Field(gt=0)
    purpose: str | None = None

class ApplicationOut(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    status: ApplicationStatus
    score: int | None = None
    risk_level: str | None = None
    score_factors: list[dict] | None = None
    decision_recommendation: str | None = None
    decision_reasons: list[str] | None = None
    bki_overdue_days: int | None = None
    recommended_amount: float | None = None
    external_checks: dict | None = None
