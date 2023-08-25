from typing import Annotated

from fastapi import Body, Depends, HTTPException
from sqlmodel import Session, select

from .model import get_engine, DB_URL, User, UserToken
from .config import settings


engine = get_engine(DB_URL, settings.echo)

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