from typing import Optional
from pydantic import BaseSettings, PostgresDsn, validator
import secrets


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Financial Planning API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        
        # Default to local development database
        return "postgresql://postgres:password@localhost:5432/financial_planning"
    
    # Redis (for caching and Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # External APIs
    LINEAR_API_URL: str = "https://api.linear.app/graphql"
    LINEAR_CLIENT_ID: Optional[str] = None
    LINEAR_CLIENT_SECRET: Optional[str] = None
    
    # Formula engine settings
    MAX_FORMULA_LENGTH: int = 1000
    ALLOWED_MATH_FUNCTIONS: list = [
        "abs", "round", "min", "max", "sum", "pow", "sqrt",
        "ceil", "floor", "log", "log10", "exp", "sin", "cos", "tan"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings() 