# mypy: ignore-errors
from typing import Iterator, Optional
from sqlmodel import Session, col, func, select, not_, or_

from . import model

class Vault:
  @staticmethod
  def _get_query(
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

  @classmethod
  def get(
    cls,
    db: Session,
    vault_uid: int,
    user_id: Optional[int] = None,
    include_shared: bool = False,
  ):
    query = cls._get_query(vault_uid, user_id, include_shared)

    vault = db.exec(query).one_or_none()

    return vault

  @classmethod
  def check_access(
    cls, 
    db: Session,
    vault_uid: int,
    user_id: Optional[int] = None,
    include_shared: bool = False,
  ) -> bool:
    query = cls._get_query(vault_uid, user_id, include_shared)

    exists = db.exec(select(query.exists())).one()

    return exists

  @staticmethod
  def get_size(db: Session, vault_id: int):
    size = db.exec(select(func.sum(model.DocumentRecord.size)).where(
      model.DocumentRecord.vault_id == vault_id,
    )).one()

    return size or 0
    
  @staticmethod
  def get_hash_count(db: Session, vault_id: int, hash: str):
    count = db.exec(select(func.count(model.DocumentRecord.id)).where(
      model.DocumentRecord.vault_id == vault_id,
      model.DocumentRecord.hash == hash,
    )).one()

    return count

class DocumentRecord:
  @staticmethod
  def get(db: Session, vault_id: int, user_id: int):
    record = db.exec(select(model.DocumentRecord).where(
      model.DocumentRecord.vault_id == vault_id,
      model.DocumentRecord.id == user_id,
    )).one_or_none()

    return record
  
  @staticmethod
  def get_deleted(db: Session, vault_id: int) -> Iterator[model.DocumentRecord]:
    record_tuples = db.exec(
      select(
        model.DocumentRecord,
        func.max(model.DocumentRecord.id),
      ).where(
        model.DocumentRecord.vault_id == vault_id,
      ).group_by(
        model.DocumentRecord.path,
      ).having(
        model.DocumentRecord.deleted,
      ).order_by(
        col(model.DocumentRecord.id).asc()
      )
    )

    return map(lambda record: record[0], record_tuples)
  
  @staticmethod
  def get_history(
    db: Session,
    vault_id: int,
    path: str,
    last: int,
  ) -> Iterator[model.DocumentRecord]:
    query = select(model.DocumentRecord).where(
      model.DocumentRecord.vault_id == vault_id,
      model.DocumentRecord.path == path,
    )
    if last:
      query = query.where(model.DocumentRecord.id < last)

    records = db.exec(query.order_by(
      col(model.DocumentRecord.id).desc()
    ))

    # TODO: limit records count

    return records
  
  @staticmethod
  def get_updates(
    db: Session,
    vault_id: int,
    last: int,
    initial: bool,
  ) -> tuple[int, Iterator[model.DocumentRecord]]:
    max_id = db.exec(select(func.max(model.DocumentRecord.id)).where(
      model.DocumentRecord.vault_id == vault_id,
    )).one() or 0

    if last == max_id:
      return max_id, []
    
    assert last < max_id

    query = select(
      model.DocumentRecord,
      func.max(model.DocumentRecord.id),
    ).where(
      model.DocumentRecord.vault_id == vault_id,
      model.DocumentRecord.id > last,
    ).group_by(
      model.DocumentRecord.path,
    )

    if initial:
      query = query.having(not_(model.DocumentRecord.deleted))
    
    query = query.order_by(
      model.DocumentRecord.id
    )
    
    return max_id, map(lambda r: r[0], db.exec(query))