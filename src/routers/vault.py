import secrets
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select, not_

from .. import model
from ..dao import get_vault
from ..depends import DbSession, UserTokenInfo, get_user_token
from ..utils import datetime_to_ts, generate_secret, get_keyhash

router = APIRouter()

@router.post('/list')
def list_vault(user_token: UserTokenInfo, req: Request, db: DbSession):
  host = req.base_url.netloc +  '/sync'
  user_id = user_token.user_id

  user_vaults = db.exec(select(model.Vault).where(
    model.Vault.owner_id == user_id,
    not_(model.Vault.deleted),
  ))

  shared_vaults = db.exec(select(model.Vault).join(
    model.VaultShare,
  ).where(
    model.VaultShare.user_id == user_id,
    not_(model.Vault.deleted),
  ))

  def convert(vaults):
    result = []
    for vault in vaults:
      result.append({
        'id': vault.id,
        'name': vault.name,
        'created': datetime_to_ts(vault.created_at),
        'password': vault.password,
        'salt': vault.salt,
        'host': host,
      })
    
    return result

  vaults = convert(user_vaults)
  shared = convert(shared_vaults)

  return {
    'vaults': vaults,
    'shared': shared,
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

class DeleteVaultRequest(BaseModel):
  vault_uid: int
  token: str

@router.post('/delete')
def delete_vault(db: DbSession, req: DeleteVaultRequest):
  user_token = get_user_token(req.token, db)

  vault = get_vault(db, req.vault_uid, user_token.user_id)
  
  if vault:
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
  user_token = get_user_token(req.token, db)

  vault = get_vault(db, req.vault_uid, user_token.user_id, True)

  if not vault:
    raise HTTPException(404)

  if not secrets.compare_digest(vault.key_hash, req.keyhash):
    return {
      'error': 'Invalid password'
    }

  return {}

class LsitVaultShareRequest(BaseModel):
  vault_uid: int
  token: str

@router.post('/share/list')
def list_share(db: DbSession, req: LsitVaultShareRequest):
  user_token = get_user_token(req.token, db)

  vault = get_vault(db, req.vault_uid, user_token.user_id)
  if not vault:
    raise HTTPException(403)

  shares = []
  for user in vault.shared_users:
    shares.append({
      'uid': str(user.id),
      'name': user.name,
      'email': user.email,
      'accepted': True,
    })

  return {
    'shares': shares,
  }

class RemoveVaultShareRequest(BaseModel):
  vault_uid: int
  share_uid: Optional[str]
  token: str

@router.post('/share/remove')
def remove_share(db: DbSession, req: RemoveVaultShareRequest):
  user_token = get_user_token(req.token, db)

  query = select(model.VaultShare).where(
    model.VaultShare.vault_id == req.vault_uid,
  )

  is_owner = bool(req.share_uid)
  # check if user can access vault
  vault = get_vault(db, req.vault_uid, user_token.user_id, not is_owner)
  if not vault:
    raise HTTPException(403)

  if is_owner:
    query = query.where(
      model.VaultShare.user_id == req.share_uid,
    )
  else:
    query = query.where(
      model.VaultShare.user_id == user_token.user_id,
    )

  share = db.exec(query).one_or_none()
  if share:
    db.delete(share)
    db.commit()

  return {}

class InviteVaultShareRequest(BaseModel):
  vault_uid: int
  email: str
  token: str

@router.post('/share/invite')
def invite_share(db: DbSession, req: InviteVaultShareRequest):
  user_token = get_user_token(req.token, db)

  vault = get_vault(db, req.vault_uid, user_token.user_id)
  if not vault:
    raise HTTPException(403)

  user = db.exec(select(model.User).where(
    model.User.email == req.email,
  )).one_or_none()

  if not user:
    return {
      'error': 'User not found'
    }
  
  vault.shared_users.append(user)
  db.add(vault)
  db.commit()

  return {}