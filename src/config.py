from pydantic import BaseModel, BaseSettings

DEFAULT_FILE_AGES = {
  '*': 30,
  'md': 90,
}

class PurgeSettings(BaseModel):
  enabled: bool = True
  # in hours
  interval: int = 1

  # in days
  vault_age: int = 30
  pending_age: int = 7
  # in days
  file_ages: dict[str, int] = DEFAULT_FILE_AGES

class Settings(BaseSettings):
  echo: bool = False
  debug: bool = False

  purge: PurgeSettings = PurgeSettings()

  class Config:
    env_file = '.env'
    env_nested_delimiter = '__'

settings = Settings()

def init():
  import logging

  logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
  
  if settings.debug:
    from sqlalchemy import log as sqlalchemy_log

    # Patch to avoid duplicate sql echo
    sqlalchemy_log._add_default_handler = lambda x: None  


init()