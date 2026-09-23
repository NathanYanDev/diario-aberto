from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    scraper_base_url: str = "https://imprensaoficial.jundiai.sp.gov.br"
    scraper_user_agent: str = "diario-aberto-bot/0.1"
    scraper_delay_seconds: float = 2.0
    scraper_fetch_attempts: int = 5
    scraper_wait_seconds: float = 5.0


settings = Settings()  # type: ignore
