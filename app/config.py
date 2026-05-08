from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL : str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_TIME:  int
    SEDNER_EMAIL: str
    EMAIL_PASSWORD: str
    TESTING: bool = False
    # Use this for Pydantic v2
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
