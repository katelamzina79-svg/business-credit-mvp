from app.db.session import SessionLocal
from app.models.models import User, Company
from app.core.security import hash_password

def seed():
    db = SessionLocal()
    try:
        users = [
            ("client@example.com", "client123", "client"),
            ("banker@example.com", "banker123", "banker"),
        ]
        for email, password, role in users:
            if not db.query(User).filter_by(email=email).first():
                db.add(User(email=email, password_hash=hash_password(password), role=role))
        if not db.query(Company).filter_by(inn="7701234567").first():
            db.add(Company(inn="7701234567", name="ООО Альфа Трейд", okved="46.90", revenue=12000000, debt=1500000, overdue_days=0))
        if not db.query(Company).filter_by(inn="7707654321").first():
            db.add(Company(inn="7707654321", name="ООО Ритейл Плюс", okved="47.11", revenue=4500000, debt=3200000, overdue_days=45))
        db.commit()
    finally:
        db.close()

if __name__ == "__main__": seed()
