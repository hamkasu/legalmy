from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    ANTHROPIC_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
