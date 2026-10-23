from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.models import ApplicationStatus

class TransitionRequest(BaseModel):
    target_status: ApplicationStatus
    comment: str | None = Field(default=None, max_length=500)

class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    application_id: int
    from_status: str | None
    to_status: str
    created_at: datetime
