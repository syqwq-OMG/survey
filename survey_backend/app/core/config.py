from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Survey System API"
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "survey_db"
    
    # 新增 JWT 相关配置
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # Token 7天有效

    class Config:
        env_file = ".env"

settings = Settings()