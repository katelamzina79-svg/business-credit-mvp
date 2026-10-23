from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.api import auth, companies, applications
from app.db.session import SessionLocal

app = FastAPI(title="Business Credit MVP API", version="0.1.0", description="SME credit application MVP backend")
templates = Jinja2Templates(directory="templates")
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(applications.router)

@app.get("/health", tags=["system"])
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse("list.html", {"request": request, "title": "Credit MVP"})
