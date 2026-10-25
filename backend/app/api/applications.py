from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db, SessionLocal
from app.models.models import Application, Company, User, StatusHistory, AuditLog, ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationOut
from app.schemas.workflow import TransitionRequest, StatusHistoryOut
from app.api.deps import current_user, banker_only
from app.services.workflow import validate_transition
from app.services.external_checks import run_external_checks
from app.services.credit_pipeline import evaluate_application

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
    if data.product not in {"credit", "overdraft", "working_capital"}:
        raise HTTPException(status_code=422, detail="Unsupported credit product")
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
    return query.order_by(Application.created_at.desc(), Application.id.desc()).all()


# Fixed path must be declared before /{application_id}.
@router.get("/banker/queue")
def banker_queue(db: Session = Depends(get_db), user: User = Depends(banker_only)):
    queue_statuses = [
        ApplicationStatus.submitted.value,
        ApplicationStatus.data_check.value,
        ApplicationStatus.scoring.value,
        ApplicationStatus.approved.value,
        ApplicationStatus.other_terms.value,
        ApplicationStatus.documents_required.value,
        ApplicationStatus.signing.value,
    ]
    applications = (
        db.query(Application)
        .filter(Application.status.in_(queue_statuses))
        .order_by(Application.created_at, Application.id)
        .all()
    )
    result = []
    for application in applications:
        company = db.get(Company, application.company_id)
        result.append({
            "application": ApplicationOut.model_validate(application).model_dump(mode="json"),
            "company": {
                "id": company.id,
                "inn": company.inn,
                "name": company.name,
                "okved": company.okved,
                "revenue": float(company.revenue or 0),
                "debt": float(company.debt or 0),
                "overdue_days": company.overdue_days or 0,
            },
        })
    return result


@router.get("/{application_id}/history", response_model=list[StatusHistoryOut])
def application_history(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    application = _get_visible_application(application_id, db, user)
    return db.query(StatusHistory).filter(StatusHistory.application_id == application.id).order_by(StatusHistory.created_at, StatusHistory.id).all()


@router.post("/{application_id}/submit", response_model=ApplicationOut)
def submit(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    application = _get_visible_application(application_id, db, user)
    if application.status != ApplicationStatus.draft.value:
        # This status guard makes repeated submissions idempotent: the pipeline is queued once.
        raise HTTPException(status_code=409, detail="Only a draft application can be submitted")
    company = db.get(Company, application.company_id)
    if not company:
        raise HTTPException(status_code=422, detail="Company record is missing; cannot run checks")

    _apply_transition(application, ApplicationStatus.submitted.value, db, user, "application.submitted")
    _apply_transition(application, ApplicationStatus.data_check.value, db, user, "application.external_checks.started")
    db.commit()
    db.refresh(application)
    background_tasks.add_task(_process_application_pipeline, application.id, user.id)
    return application


@router.post("/{application_id}/sign", response_model=ApplicationOut)
def sign_offer(application_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Only the client can sign the demo offer")
    application = _get_visible_application(application_id, db, user)
    if application.status not in {ApplicationStatus.approved.value, ApplicationStatus.other_terms.value}:
        raise HTTPException(status_code=409, detail="The application has no offer ready for signing")
    _apply_transition(application, ApplicationStatus.signing.value, db, user, "application.offer_signed_demo")
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
    if application.status == ApplicationStatus.scoring.value and target in {
        ApplicationStatus.approved.value,
        ApplicationStatus.other_terms.value,
        ApplicationStatus.documents_required.value,
        ApplicationStatus.rejected.value,
    }:
        db.add(AuditLog(user_id=user.id, action=f"application.decision_recommendation:{application.decision_recommendation};chosen:{target}", entity_type="application", entity_id=application.id))
    action = f"application.status_changed:{application.status}->{target}"
    _apply_transition(application, target, db, user, action)
    if data.comment:
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


def _process_application_pipeline(application_id: int, actor_id: int) -> None:
    """Run mock checks/scoring after the submit response; status guard prevents duplicate work."""
    with SessionLocal() as task_db:
        application = task_db.get(Application, application_id)
        actor = task_db.get(User, actor_id)
        if not application or not actor or application.status != ApplicationStatus.data_check.value:
            return
        company = task_db.get(Company, application.company_id)
        if not company:
            task_db.add(AuditLog(user_id=actor.id, action="application.pipeline_failed:company_missing", entity_type="application", entity_id=application.id))
            task_db.commit()
            return
        try:
            checks = run_external_checks(company)
            result = evaluate_application(application, company, checks)
            application.score = result["score"]
            application.risk_level = result["risk_level"]
            application.score_factors = result["score_factors"]
            application.decision_recommendation = result["decision_recommendation"]
            application.decision_reasons = result["decision_reasons"]
            application.bki_overdue_days = result["bki_overdue_days"]
            application.recommended_amount = result["recommended_amount"]
            application.external_checks = result["external_checks"]
            _apply_transition(application, ApplicationStatus.scoring.value, task_db, actor, "application.scoring.completed")
            task_db.commit()
        except Exception:
            task_db.rollback()
            task_db.add(AuditLog(user_id=actor.id, action="application.pipeline_failed:unexpected_error", entity_type="application", entity_id=application.id))
            task_db.commit()
