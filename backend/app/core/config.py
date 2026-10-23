from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://credit:credit@localhost:5432/credit_mvp"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
