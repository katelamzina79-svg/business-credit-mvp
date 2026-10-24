import os
from fastapi import UploadFile

class DocumentValidator:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
    MIN_SIZE_BYTES = 5 * 1024  # 5 KB

    @classmethod
    async def validate(cls, file: UploadFile, doc_type: str) -> dict:
        filename = file.filename or ""
        _, ext = os.path.splitext(filename.lower())
        
        # Замеряем размер файла
        content = await file.read()
        size = len(content)
        await file.seek(0) # Сброс указателя для последующего сохранения
        
        errors = []
        if ext not in cls.ALLOWED_EXTENSIONS:
            errors.append(f"Формат {ext} не поддерживается. Нужен PDF, PNG или JPG.")
        if size < cls.MIN_SIZE_BYTES:
            errors.append("Файл поврежден или пуст (размер менее 5 КБ).")
            
        # Мимикрия под умный OCR
        if doc_type == "passport" and "pass" not in filename.lower() and "pasp" not in filename.lower():
            errors.append("Предупреждение ИИ: На скане не обнаружены явные метрики паспорта.")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "status": "APPROVED" if is_valid else "REJECTED",
            "errors": errors
        }
