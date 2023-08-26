from sqlmodel import Session, select, not_, or_

from . import model


def get_vault(
  db: Session,
  vault_uid: int,
  user_id: int,
  include_shared: bool = False,
):
  query = select(model.Vault).where(
    model.Vault.id == vault_uid,
    not_(model.Vault.deleted),
  )

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

  vault = db.exec(query).one_or_none()

  return vault

def check_vault_access(
  db: Session,
  vault_uid: int,
  user_id: int,
  include_shared: bool = False,
):
  vault = get_vault(db, vault_uid, user_id, include_shared)

  return bool(vault)