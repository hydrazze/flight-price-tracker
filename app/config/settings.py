from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):

    bot_token: SecretStr

    travelpayouts_api_key: SecretStr

    database_url: str

    redis_url: str = "redis://localhost:6379/0"

    price_check_interval: int = Field(default=3600, gt=0)

    sql_echo: bool = False


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
