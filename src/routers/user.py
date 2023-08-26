from typing import Annotated
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from ..utils import generate_token, verify_password

from ..depends import DbSession, UserInfo, get_user_token
from ..model import User, UserToken

router = APIRouter()

class UserSigninRequest(BaseModel):
  email: str
  password: str

@router.post('/signin')
def user_signin(db: DbSession, req: UserSigninRequest):
  user = db.exec(select(User).where(UserInfo.email == req.email)).one_or_none()
  if not user or not verify_password(req.password, user.salt, user.password):
    raise HTTPException(401)
  
  token = generate_token()
  user_token = UserToken(user_id=user.id, token=token)

  db.add(user_token)
  db.commit()

  return {
    'email': user.email,
    'license': '',
    'name': user.name,
    'token': token,
  }

@router.post('/info')
def user_info(user: UserInfo):
  return {
    'email': user.email,
    'mfa': False,
    'credit': 0,
    'discount': None,
    'license': '',
    'name': user.name,
    'payment': '',
    'uid': str(user.id),
  }

@router.post('/signout')
def user_signout(db: DbSession, token: Annotated[str, Body(embed=True)]):
  try:
    user_token = get_user_token(token, db)
    db.delete(user_token)
    db.commit()
  except HTTPException:
    # ignore invalid token
    pass

  return {}