from pydantic import BaseSettings

class Settings(BaseSettings):
  echo: bool = False
  debug: bool = False

  class Config:
    env_file = '.env'

settings = Settings()