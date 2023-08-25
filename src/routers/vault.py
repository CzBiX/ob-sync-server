from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select, not_

from .. import model
from ..depends import DbSession, UserInfo, get_user_token
from ..utils import datetime_to_ts, generate_secret, get_keyhash

router = APIRouter()

@router.post('/list')
def list_vault(user: UserInfo, req: Request, db: DbSession):
  host = req.base_url.netloc +  '/sync'

  user_vaults = db.exec(select(model.Vault).where(
    model.Vault.owner_id == user.id,
    not_(model.Vault.deleted),
  ))

  vaults = []
  for vault in user_vaults:
    vaults.append({
      'id': vault.id,
      'name': vault.name,
      'created': datetime_to_ts(vault.created_at),
      'password': vault.password,
      'salt': vault.salt,
      'host': host,
    })

  return {
    'shared': [],
    'vaults': vaults,
  }

class CreateVaultRequest(BaseModel):
  name: str
  keyhash: str | None
  salt: str | None
  token: str

@router.post('/create')
def create_vault(db: DbSession, req: CreateVaultRequest):
  user = get_user_token(req.token, db).user

  if not req.keyhash:
    password = generate_secret()
    req.salt = generate_secret()
    req.keyhash = get_keyhash(password, req.salt)
  else:
    password = ''

  vault = model.Vault(
    owner_id=user.id,
    name=req.name,
    password=password,
    salt=req.salt,
    key_hash=req.keyhash,
  )

  db.add(vault)
  db.commit()

  return {}

def get_vault(db: DbSession, vault_uid: int, user: UserInfo):
  vault = db.exec(select(model.Vault).where(
    model.Vault.id == vault_uid,
    model.Vault.owner_id == user.id,
    not_(model.Vault.deleted),
  )).one()

  return vault

class DeleteVaultRequest(BaseModel):
  vault_uid: int
  token: str

@router.post('/delete')
def delete_vault(db: DbSession, req: DeleteVaultRequest):
  user = get_user_token(req.token, db).user

  vault = get_vault(db, req.vault_uid, user)
  
  vault.deleted = True

  db.add(vault)
  db.commit()

  return {}

class AccessVaultRequest(BaseModel):
  token: str
  vault_uid: int
  keyhash: str

@router.post('/access')
def access_vault(db: DbSession, req: AccessVaultRequest):
  user = get_user_token(req.token, db).user

  vault = get_vault(db, req.vault_uid, user)

  if vault.key_hash != req.keyhash:
    raise HTTPException(403)

  return {}
