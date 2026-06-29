from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session_path: Path = Path("./data/telegram.session")
    telegram_channel: str = ""

    database_path: Path = Path("./data/job_radar.db")

    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    dashboard_user: str = "admin"
    dashboard_pass: str = "changeme"
    host: str = "127.0.0.1"
    port: int = 8000

    google_sheets_credentials_path: Path = Path("./data/google_credentials.json")
    google_sheets_token_path: Path = Path("./data/google_token.json")
    google_sheet_id: str = ""
    csv_export_path: Path = Path("./data/exports")

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
