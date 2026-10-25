from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models.models import Application, Company, User
from app.services.smart_feed import SmartFeedService

router = APIRouter(tags=["feed"])
templates = Jinja2Templates(directory="templates")


def _get_feed_data(db: Session, user: User) -> dict:
    application = (
        db.query(Application)
        .filter(Application.client_id == user.id)
        .order_by(Application.created_at.desc(), Application.id.desc())
        .first()
    )
    company = db.get(Company, application.company_id) if application else None
    suggestions = SmartFeedService.get_suggestions(
        okved=company.okved if company else "",
        status=application.status if application else "draft",
        score=int(application.score) if application and application.score is not None else 0,
    )
    return {"source_application_id": application.id if application else None, "suggestions": suggestions}


@router.get("/api/feed")
def personalized_feed(db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Return rule-based tips tailored to the client's latest application."""
    return _get_feed_data(db, user)


@router.get("/feed/snippet", include_in_schema=False)
def personalized_feed_snippet(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Render Petos' feed snippet as an authenticated Jinja fragment."""
    data = _get_feed_data(db, user)
    return templates.TemplateResponse(
        "feed_snippet.html",
        {"request": request, "suggestions": data["suggestions"]},
    )
