from typing import Annotated

from fastapi import Body, Depends, HTTPException
from sqlalchemy import event
from sqlmodel import Session, select

from .config import settings
from .model import DB_URL, User, UserToken, get_engine

engine = get_engine(DB_URL, settings.echo)

@event.listens_for(engine, 'connect')
def conn_wal_mode(conn, _):
  conn.execute('PRAGMA journal_mode=WAL')
  conn.execute('PRAGMA synchronous=NORMAL')

def db_migrations():
  from .migration import run_migrations

  with engine.begin() as conn:
    run_migrations(conn)

db_migrations()

def db_session():
  with Session(engine) as session:
    yield session

DbSession = Annotated[Session, Depends(db_session)]

def get_user_token(token: Annotated[str, Body(embed=True)], session: DbSession):
  if not token:
    raise HTTPException(401)
  
  query = select(UserToken).where(UserToken.token == token)
  user_token = session.exec(query).one_or_none()

  if not user_token:
    raise HTTPException(403)
  
  return user_token

UserTokenInfo = Annotated[UserToken, Depends(get_user_token)]

def get_user(token: UserTokenInfo):
  return token.user

UserInfo = Annotated[User, Depends(get_user)]