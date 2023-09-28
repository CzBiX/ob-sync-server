import asyncio
import datetime
import logging
import os
import shutil
from typing import Optional

from sqlmodel import Session, select

from . import model
from .config import PurgeSettings
from .depends import engine
from .storage import get_vault_dir
from src import storage

logger = logging.getLogger(__name__)

def check_sql_dialect():
  assert engine.dialect.name == 'sqlite', 'Purging is only supported on SQLite for now'

class Purger:
  config: PurgeSettings
  task: Optional[asyncio.Task]

  def __init__(self, config: PurgeSettings):
    check_sql_dialect()

    self.config = config

  async def start(self):
    self.task = asyncio.create_task(self._loop())
  
  async def stop(self):
    self.task.cancel()

    logger.info('Waiting for purger task to stop...')
    await asyncio.wait_for(self.task, None)
  
  async def _loop(self):
    time_delta = datetime.timedelta(hours=self.config.interval)
    interval = time_delta.total_seconds()

    while True:
      logger.info('Next purge in %s', time_delta)
      try:
        await asyncio.sleep(interval)
      except asyncio.CancelledError:
        logger.debug('Purger task cancelled')
        return

      logger.info('Purging...')

      await asyncio.to_thread(self.purge)

  def purge(self):
    with Session(engine) as db:
      db.execute('BEGIN IMMEDIATE')
      self._purge_deleted_vaults(db)
      self._purge_pending_upload_files(db)
    
      db.execute('VACUUM')
  
  def _purge_pending_upload_files(self, db: Session):
    time_delta = datetime.timedelta(days=self.config.pending_age)
    created_before = datetime.datetime.now() - time_delta
    pending_files = db.exec(select(model.PendingFile)
      .where(
        model.PendingFile.created_at <= created_before,
        model.PendingFile.type == model.PendingFileType.UPLOAD,
      )
    )

    for pending_file in pending_files:
      path = storage.get_file_path(pending_file.vault_id, pending_file.hash)
      if os.path.exists(path):
        os.remove(path)
      
      db.delete(pending_file)
    
    logger.info('Purged %d pending upload files', len(db.deleted))
    db.commit()
  
  def _purge_deleted_vaults(self, db: Session):
    vaults = db.exec(select(model.Vault).where(model.Vault.deleted))
    for vault in vaults:
      self._purge_deleted_vault(db, vault)
  
  def _purge_deleted_vault(self, db: Session, vault: model.Vault):
    logger.debug('Purging deleted vault, id: %d, name: %s', vault.id, vault.name)

    db.query(model.PendingFile).filter(
      model.PendingFile.vault_id == vault.id
    ).delete()

    db.query(model.VaultShare).filter(
      model.VaultShare.vault_id == vault.id
    ).delete()

    logger.debug('Vault shares deleted')

    assert vault.id is not None
    dir_path = get_vault_dir(vault.id)
    shutil.rmtree(dir_path)

    logger.debug('Vault directory deleted')

    db.query(model.DocumentRecord).filter(
      model.DocumentRecord.vault_id == vault.id
    ).delete()

    logger.debug('Document records deleted')

    db.delete(vault)
    logger.info('Purged vault, id: %d, name: %s', vault.id, vault.name)

    db.commit()
