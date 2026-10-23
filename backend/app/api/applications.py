from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Application, Company, User, StatusHistory, AuditLog, ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationOut
from app.schemas.workflow import TransitionRequest, StatusHistoryOut
from app.api.deps import current_user, banker_only
from app.services.workflow import validate_transition

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _get_visible_application(application_id: int, db: Session, user: User) -> Application:
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if user.role != "banker" and application.client_id != user.id:
        raise HTTPException(status_code=403, detail="You cannot access this application")
    return application


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not db.get(Company, data.company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    application = Application(client_id=user.id, status=ApplicationStatus.draft.value, **data.model_dump())
    db.add(application)
    db.flush()
    db.add(StatusHistory(application_id=application.id, from_status=None, to_status=application.status))
    db.add(AuditLog(user_id=user.id, action="application.created", entity_type="application", entity_id=application.id))
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(Application)
    if user.role != "banker":
        query = query.filter(Application.client_id == user.id)
    return query.order_by(Application.created_at.desc()).all()


# Declare fixed paths before /{application_id} so "banker" isn't parsed as an ID.
@router.get("/banker/queue", response_model=list[ApplicationOut])
def banker_queue(db: Session = Depends(get_db), user: User = Depends(banker_only)):
    queue_statuses = [ApplicationStatus.submitted.value, ApplicationStatus.data_check.value, ApplicationStatus.scoring.value]
    return db.query(Application).filter(Application.status.in_(queue_statuses)).order_by(Application.created_at).all()


@router.get("/{application_id}/history", response_model=list[StatusHistoryOut])
def application_history(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    application = _get_visible_application(application_id, db, user)
    return db.query(StatusHistory).filter(StatusHistory.application_id == application.id).order_by(StatusHistory.created_at, StatusHistory.id).all()


@router.post("/{application_id}/submit", response_model=ApplicationOut)
def submit(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    application = _get_visible_application(application_id, db, user)
    if application.status != ApplicationStatus.draft.value:
        raise HTTPException(status_code=409, detail="Only a draft application can be submitted")
    _apply_transition(application, ApplicationStatus.submitted.value, db, user, "application.submitted")
    db.commit()
    db.refresh(application)
    return application


@router.post("/{application_id}/transition", response_model=ApplicationOut)
def transition_application(application_id: int, data: TransitionRequest, db: Session = Depends(get_db), user: User = Depends(banker_only)):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    target = data.target_status.value
    try:
        validate_transition(application.status, target)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    action = f"application.status_changed:{application.status}->{target}"
    _apply_transition(application, target, db, user, action)
    if data.comment:
        # Comments are retained in the audit action so the MVP doesn't need a migration.
        db.add(AuditLog(user_id=user.id, action=f"comment:{data.comment}", entity_type="application", entity_id=application.id))
    db.commit()
    db.refresh(application)
    return application


@router.get("/{application_id}", response_model=ApplicationOut)
def get_application(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _get_visible_application(application_id, db, user)


def _apply_transition(application: Application, target: str, db: Session, user: User, action: str) -> None:
    previous = application.status
    application.status = target
    db.add(StatusHistory(application_id=application.id, from_status=previous, to_status=target))
    db.add(AuditLog(user_id=user.id, action=action, entity_type="application", entity_id=application.id))
