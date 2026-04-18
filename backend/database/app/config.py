from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    data_dir: str = "../data"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
