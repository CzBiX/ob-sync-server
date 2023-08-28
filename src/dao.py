from typing import Optional
from sqlmodel import Session, select, not_, or_

from . import model

def _get_vault_query(
  db: Session,
  vault_uid: int,
  user_id: Optional[int],
  include_shared: bool,
):
  query = select(model.Vault).where(
    model.Vault.id == vault_uid,
    not_(model.Vault.deleted),
  )

  if user_id is None:
    return query

  if include_shared:
    query = query.join(
      model.VaultShare,
      isouter=True,
    ).where(
      or_(
        model.Vault.owner_id == user_id,
        model.VaultShare.user_id == user_id,
      )
    ).distinct(model.Vault.id)
  else:
    query = query.where(
      model.Vault.owner_id == user_id,
    )

  return query

def get_vault(
  db: Session,
  vault_uid: int,
  user_id: Optional[int] = None,
  include_shared: bool = False,
):
  query = _get_vault_query(db, vault_uid, user_id, include_shared)

  vault = db.exec(query).one_or_none()

  return vault

def check_vault_access(
  db: Session,
  vault_uid: int,
  user_id: Optional[int] = None,
  include_shared: bool = False,
) -> bool:
  query = _get_vault_query(db, vault_uid, user_id, include_shared)

  exists = db.exec(select(query.exists())).one()

  return exists