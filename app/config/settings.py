from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    travelpayouts_api_key: str
    travelpayouts_api_key: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()