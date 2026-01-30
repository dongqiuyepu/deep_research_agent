from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
