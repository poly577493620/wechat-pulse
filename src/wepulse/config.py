from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "WePulse"
    host: str = "0.0.0.0"
    port: int = 8765
    data_dir: Path = Path("data")
    admin_token: str = "change-me"
    tz: str = "Asia/Shanghai"
    collect_interval_minutes: int = 60
    digest_hour: int = 6
    digest_minute: int = 0
    digest_webhook_url: str = ""
    wecom_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: str = ""
    weread_cookie: str = ""
    weread_content: bool = False
    request_timeout_seconds: int = 20
    user_agent: str = "Mozilla/5.0 WePulse/0.1"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "wepulse.db"


settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
