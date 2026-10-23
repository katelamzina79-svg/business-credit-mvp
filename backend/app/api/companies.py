from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Company, User
from app.schemas.schemas import CompanyCreate, CompanyOut
from app.api.deps import current_user

router = APIRouter(prefix="/api/companies", tags=["companies"])

@router.post("", response_model=CompanyOut)
def create_company(data: CompanyCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    existing = db.query(Company).filter(Company.inn == data.inn).first()
    if existing: return existing
    company = Company(**data.model_dump())
    db.add(company); db.commit(); db.refresh(company)
    return company


@router.get("/lookup/{inn}", response_model=CompanyOut)
def lookup_company_by_inn(inn: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Mock EGRUL lookup by INN using the seeded company registry."""
    company = db.query(Company).filter(Company.inn == inn).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found in mock EGRUL registry")
    return company

@router.get("/{company_id}", response_model=CompanyOut)
def get_company(company_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    company = db.get(Company, company_id)
    if not company: raise HTTPException(404, "Company not found")
    return company

@router.get("", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return db.query(Company).order_by(Company.id.desc()).all()
