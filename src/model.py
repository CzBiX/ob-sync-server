from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint, create_engine


class User(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  email: str = Field(unique=True)
  password: str
  salt: str
  name: str
  created_at: datetime = Field(default_factory=datetime.now)

class UserToken(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  user_id: int = Field(index=True, foreign_key='user.id')
  token: str = Field(index=True)
  created_at: datetime = Field(default_factory=datetime.now)

  user: User = Relationship()

class VaultShare(SQLModel, table=True):
  vault_id: int = Field(foreign_key='vault.id', primary_key=True)
  user_id: int = Field(foreign_key='user.id', primary_key=True)
  created_at: datetime = Field(default_factory=datetime.now)

class Vault(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  owner_id: int = Field(index=True, foreign_key='user.id')
  name: str
  password: str
  key_hash: str
  salt: str
  deleted: bool = Field(default=False)
  created_at: datetime = Field(default_factory=datetime.now)

  owner: User = Relationship()
  shared_users: list[User] = Relationship(link_model=VaultShare)

class DocumentRecord(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  vault_id: int = Field(index=True, foreign_key='vault.id')
  path: str = Field(index=True)
  relatedpath: str = Field(default='')
  hash: str = Field(index=True)
  folder: bool
  deleted: bool = Field(default=False)
  size: int = Field(default=0)
  device: str
  ctime: int
  mtime: int
  created_at: datetime = Field(default_factory=datetime.now)

  vault: Vault = Relationship()

class PendingFile(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  vault_id: int = Field(foreign_key='vault.id')
  hash: str
  created_at: datetime = Field(default_factory=datetime.now)

  __table_args__ = (
    UniqueConstraint('vault_id', 'hash'),
  )

def get_engine(db_url: str, echo: bool = False):
  return create_engine(db_url, echo=echo, connect_args={
    'check_same_thread': False
  })

def create_db_and_tables(engine):
  SQLModel.metadata.create_all(engine)

DB_PATH = 'data/data.db'
DB_URL = 'sqlite:///' + DB_PATH
