from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel, create_engine


class User(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  email: str = Field(index=True)
  password: str
  salt: str
  name: str
  created_at: datetime = Field(default_factory=datetime.now)

class UserToken(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  user_id: int = Field(index=True, foreign_key='user.id')
  token: str = Field(index=True)
  created_at: datetime = Field(default_factory=datetime.now)

  user: User = Relationship(sa_relationship_kwargs={'uselist':False})

class Vault(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  owner_id: int = Field(index=True, foreign_key='user.id')
  name: str
  password: str
  key_hash: str
  salt: str
  deleted: bool = Field(default=False)
  created_at: datetime = Field(default_factory=datetime.now)

  owner: User = Relationship(sa_relationship_kwargs={'uselist':False})

class DocumentRecord(SQLModel, table=True):
  id: Optional[int] = Field(default=None, primary_key=True)
  vault_id: int = Field(index=True, foreign_key='vault.id')
  path: str = Field(index=True)
  hash: str = Field(index=True)
  device: str
  folder: bool
  deleted: bool = Field(default=False)
  size: int = Field(default=0)
  pieces: int = Field(default=0)
  ctime: int
  mtime: int
  created_at: datetime = Field(default_factory=datetime.now)

  vault: Vault = Relationship(sa_relationship_kwargs={'uselist':False})

def get_engine(db_url: str, echo: bool = False):
  return create_engine(db_url, echo=echo, connect_args={
    'check_same_thread': False
  })

def create_db_and_tables(engine):
  SQLModel.metadata.create_all(engine)

DB_URL = 'sqlite:///data/data.db'

if __name__ == '__main__':
  create_db_and_tables(get_engine(DB_URL, echo=True))