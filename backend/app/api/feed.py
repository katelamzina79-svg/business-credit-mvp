from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import Application, Company, User
from app.services.smart_feed import SmartFeedService

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("")
def personalized_feed(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Return rule-based tips tailored to the client's latest application."""
    application = (
        db.query(Application)
        .filter(Application.client_id == user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .first()
    )
    company = db.get(Company, application.company_id) if application else None
    okved = company.okved if company else ""
    status = application.status if application else "draft"
    score = int(application.score) if application and application.score is not None else 0

    return {
        "source_application_id": application.id if application else None,
        "suggestions": SmartFeedService.get_suggestions(okved=okved, status=status, score=score),
    }
