from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables / .env.

    See .env.example for the full list. Nothing here should ever be a hard-coded
    business value (rates, thresholds, fee amounts) -- those live in the `setting`
    table (app.models.foundation.Setting) so they're editable without a deploy,
    per the source doc's repeated "never hard-code this" rule.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://erp:erp@localhost:5432/holiday_home_erp"
    cors_origins: str = "http://localhost:4200"
    upload_dir: str = "./uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
