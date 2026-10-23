from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Application, Company, User, StatusHistory, AuditLog, ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationOut
from app.api.deps import current_user, banker_only

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.post("", response_model=ApplicationOut)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Company, data.company_id): raise HTTPException(404, "Company not found")
    app = Application(client_id=user.id, status=ApplicationStatus.draft.value, **data.model_dump())
    db.add(app); db.flush()
    db.add(StatusHistory(application_id=app.id, to_status=app.status))
    db.add(AuditLog(user_id=user.id, action="application.created", entity_type="application", entity_id=app.id))
    db.commit(); db.refresh(app)
    return app

@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    q = db.query(Application)
    if user.role != "banker": q = q.filter(Application.client_id == user.id)
    return q.order_by(Application.created_at.desc()).all()

@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    app = db.get(Application, application_id)
    if not app: raise HTTPException(404, "Application not found")
    if user.role != "banker" and app.client_id != user.id: raise HTTPException(403, "Forbidden")
    return app

@router.post("/{application_id}/submit", response_model=ApplicationOut)
def submit(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    app = db.get(Application, application_id)
    if not app or (user.role != "banker" and app.client_id != user.id): raise HTTPException(404, "Application not found")
    if app.status != ApplicationStatus.draft.value: raise HTTPException(409, "Only draft can be submitted")
    old = app.status; app.status = ApplicationStatus.submitted.value
    db.add(StatusHistory(application_id=app.id, from_status=old, to_status=app.status))
    db.add(AuditLog(user_id=user.id, action="application.submitted", entity_type="application", entity_id=app.id))
    db.commit(); db.refresh(app)
    return app

@router.get("/banker/queue", response_model=list[ApplicationOut])
def banker_queue(db: Session = Depends(get_db), user: User = Depends(banker_only)):
    return db.query(Application).filter(Application.status.in_([ApplicationStatus.submitted.value, ApplicationStatus.data_check.value, ApplicationStatus.scoring.value])).order_by(Application.created_at).all()
