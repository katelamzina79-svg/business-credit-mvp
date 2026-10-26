from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.api import auth, companies, applications, feed
from app.db.session import SessionLocal

app = FastAPI(title="Business Credit MVP API", version="0.2.0", description="SME credit application MVP backend")
templates = Jinja2Templates(directory="templates")
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(applications.router)
app.include_router(feed.router)

@app.get("/health", tags=["system"])
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse("client_login.html", {"request": request, "title": "Вход · Бизнес.Кредит"})

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def client_login(request: Request):
    return templates.TemplateResponse("client_login.html", {"request": request, "title": "Вход клиента · Бизнес.Кредит"})

@app.get("/client", response_class=HTMLResponse, include_in_schema=False)
def client_dashboard(request: Request):
    return templates.TemplateResponse("client.html", {"request": request, "title": "Главная · Кабинет клиента", "page": "dashboard"})

@app.get("/client/applications/new", response_class=HTMLResponse, include_in_schema=False)
def client_new_application(request: Request):
    return templates.TemplateResponse("client.html", {"request": request, "title": "Новая заявка · Кабинет клиента", "page": "new"})

@app.get("/client/applications", response_class=HTMLResponse, include_in_schema=False)
def client_applications(request: Request):
    return templates.TemplateResponse("client.html", {"request": request, "title": "Мои заявки · Кабинет клиента", "page": "applications"})

@app.get("/client/feed", response_class=HTMLResponse, include_in_schema=False)
def client_feed(request: Request):
    return templates.TemplateResponse("client.html", {"request": request, "title": "Подсказки · Кабинет клиента", "page": "feed"})

@app.get("/banker/login", response_class=HTMLResponse, include_in_schema=False)
def banker_login(request: Request):
    return templates.TemplateResponse("banker_login.html", {"request": request, "title": "Вход банкира · Бизнес.Кредит"})

@app.get("/banker", response_class=HTMLResponse, include_in_schema=False)
def banker_page(request: Request):
    return templates.TemplateResponse("banker_dashboard.html", {"request": request, "title": "Главная · Кабинет банкира", "page": "dashboard"})

@app.get("/banker/applications", response_class=HTMLResponse, include_in_schema=False)
def banker_applications(request: Request):
    return templates.TemplateResponse("banker_queue.html", {"request": request, "title": "Заявки · Кабинет банкира", "page": "applications"})
