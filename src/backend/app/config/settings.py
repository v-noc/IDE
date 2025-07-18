from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    ARANGO_HOST: str = "http://localhost:8529"
    ARANGO_USER: str = "app_user"
    ARANGO_PASSWORD: str = "app_password"
    ARANGO_DB: str = "_system"
    PORT: int = 8000
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    def is_production(self) -> bool:
        return self.APP_ENV == "production"

settings = Settings()
