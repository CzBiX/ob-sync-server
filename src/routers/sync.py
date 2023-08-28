import asyncio
from dataclasses import dataclass
import json
import logging
import math
import secrets

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, col, func, not_, select

from .. import dao, model, storage
from ..config import settings
from ..dao import check_vault_access
from ..depends import DbSession, engine, get_user_token
from ..utils import datetime_to_ts

logger = logging.getLogger(__name__)

router = APIRouter()

SYNC_SIZE_LIMIT = 10 * 1024 * 1024 * 1024
CHUNK_SIZE = 2 * 1024 * 1024

@router.get('')
def index():
  return PlainTextResponse('Sync server')

@router.websocket('')
async def websocket(ws: WebSocket, db: DbSession):
  await ws.accept()

  conn = None

  try:
    conn = await UserSyncConn.auth(ws, db)
    await conn.loop()
  except WebSocketDisconnect:
    pass
  except Exception as e:
    logger.warn('websocket error', exc_info=True)
    await ws.send_json({
      'error': 'internal error',
      'message': str(e),
    })
  finally:
    if conn:
      conn.disconnect()

if settings.debug:
  @router.get('/status')
  def status():
    vaults = [
      {
        'id': vault.vault_id,
        'size': vault.size,
        'conn_devices': [conn.device for conn in vault.conns],
      }
      for vault in vaultStates.values()
    ]
    return {
      'vaults': vaults,
      'vaults_count': len(vaults),
    }

def size_to_pieces(size: int):
  return math.ceil(size / CHUNK_SIZE)

def record_to_msg(record: model.DocumentRecord):
  msg = {
    'uid': record.id,
    'path': record.path,
    'hash': record.hash,
    'folder': record.folder,
    'deleted': record.deleted,
    'ctime': record.ctime,
    'mtime': record.mtime,
  }

  if not record.folder and not record.deleted:
    msg['size'] = record.size
  
  return msg

def record_to_history(record: model.DocumentRecord):
  return {
    'uid': record.id,
    'path': record.path,
    'folder': record.folder,
    'device': record.device,
    'size': record.size,
    'deleted': record.deleted,
    'ts': datetime_to_ts(record.created_at),
  }

class UserVaultState:
  def __init__(self, vault_id: str):
    self.vault_id = vault_id

    self.conns: list['UserSyncConn'] = []
    self.db = Session(engine)

    self.vault = self._get_vault()
  
  def _get_vault(self):
    vault = dao.get_vault(self.db, self.vault_id)

    if not vault:
      raise Exception('Vault not found')

    return vault
  
  def get_size(self):
    size = self.db.exec(select(func.sum(model.DocumentRecord.size)).where(
      model.DocumentRecord.vault_id == self.vault_id,
    )).one()

    return size or 0
  
  def hash_exists(self, hash: str):
    record = self.db.exec(select(model.DocumentRecord).where(
      model.DocumentRecord.vault_id == self.vault_id,
      model.DocumentRecord.hash == hash,
    )).one_or_none()

    return record is not None
  
  def get_record(self, uid: int):
    record = self.db.exec(select(model.DocumentRecord).where(
      model.DocumentRecord.vault_id == self.vault_id,
      model.DocumentRecord.id == uid,
    )).one()

    return record
  
  def get_deleted(self):
    record_tuples = self.db.exec(
      select(
        model.DocumentRecord,
        func.max(model.DocumentRecord.id),
      ).where(
        model.DocumentRecord.vault_id == self.vault_id,
      ).group_by(
        model.DocumentRecord.path,
      ).having(
        model.DocumentRecord.deleted,
      ).order_by(
        col(model.DocumentRecord.id).desc()
      )
    ).all()

    records = [record[0] for record in record_tuples]
    return records
  
  def get_history(self, path: str, last: int):
    query = select(model.DocumentRecord).where(
      model.DocumentRecord.vault_id == self.vault_id,
      model.DocumentRecord.path == path,
    )
    if last:
      query = query.where(model.DocumentRecord.id < last)

    records = self.db.exec(query.order_by(
      col(model.DocumentRecord.id).desc()
    )).all()

    # TODO: limit records count

    return records
  
  def get_updates(self, last: int, initial: bool):
    max_id = self.db.exec(select(func.max(model.DocumentRecord.id)).where(
      model.DocumentRecord.vault_id == self.vault_id,
    )).one() or 0

    if last == max_id:
      return max_id, []
    
    assert last < max_id

    query = select(
      model.DocumentRecord,
      func.max(model.DocumentRecord.id),
    ).where(
      model.DocumentRecord.vault_id == self.vault_id,
      model.DocumentRecord.id > last,
    ).group_by(
      model.DocumentRecord.path,
    )

    if initial:
      query = query.having(not_(model.DocumentRecord.deleted))
    
    query = query.order_by(
      model.DocumentRecord.id
    )
    
    return max_id, map(lambda r: r[0], self.db.exec(query))
  
  async def restore(self, uid: int, device: str):
    old_record = self.get_record(uid)

    new_record = model.DocumentRecord(**old_record.dict(
      exclude={'id', 'deleted', 'device', 'created_at'}
    ), device=device)

    await self.push(new_record)

    return new_record
  
  def join(conn: 'UserSyncConn', user_id: int, vault_id: int, keyhash: str):
    vault_state = vaultStates.get(vault_id) 
    if not vault_state:
      vault_state = UserVaultState(vault_id)
      vaultStates[vault_id] = vault_state
    
    vault = vault_state.vault
    if not check_vault_access(vault_state.db, vault_id, user_id, True):
      raise Exception('Auth failed')

    if not secrets.compare_digest(vault.key_hash, keyhash):
      raise Exception('Invalid password')
    
    logger.debug('vault join, vault_id: %d, device: %s', vault_id, conn.device)
    vault_state.conns.append(conn)

    return vault_state
  
  def leave(self, conn: 'UserSyncConn'):
    logger.debug('vault leave, vault_id: %d, device: %s', self.vault_id, conn.device)
    self.conns.remove(conn)

    if len(self.conns) == 0:
      del vaultStates[self.vault_id]
      self.db.close()
  
  async def push(self, record: model.DocumentRecord):
    self.db.add(record)
    self.db.commit()

    msg = record_to_msg(record)
    msg['op'] = 'push'

    for c in self.conns:
      await c.send(msg)

vaultStates: dict[int, UserVaultState] = {}

@dataclass
class UserSyncConn:
  ws: WebSocket
  device: str
  vault: UserVaultState | None = None
  
  def disconnect(self):
    if self.vault:
      self.vault.leave(self)
      self.vault = None
  
  async def send(self, data):
    await self.ws.send_json(data)

  async def result(self, error: str | None = None):
    msg = {
      'res': 'ok' if not error else 'err',
    }
    
    if error:
      msg['error'] = error
    
    await self.send(msg)

  async def loop(self):
    while True:
      msg = await self.ws.receive_json() 
      await self.handle(msg)
  
  async def auth(ws: WebSocket, db: DbSession):
    msg = await ws.receive_json()
    assert msg['op'] == 'init'

    device = msg['device']
    user_token = get_user_token(msg['token'], db)

    conn = UserSyncConn(ws, device)
    vault = UserVaultState.join(
      conn, user_token.user_id, msg['id'], msg['keyhash']
    )
    conn.vault = vault

    await conn.result()

    asyncio.create_task(conn.send_records(msg['version'], msg['initial']))

    return conn
  
  async def on_push(self, msg: dict):
    if not msg['folder'] and not msg['deleted']:
      pieces = msg['pieces']
      if pieces and not self.vault.hash_exists(msg['hash']):
        f = storage.get_file_object(self.vault.vault_id, msg['hash'], False)
        try:
          for _ in range(pieces):
            await self.send({
              # HACK: anything other than 'ok'
              'res': 'missing-blobs'
            })
            chunk = await self.receive_binary()
            f.write(chunk)
        finally:
          f.close()

    record = model.DocumentRecord(
      vault_id=self.vault.vault_id,
      path=msg['path'],
      hash=msg['hash'],
      folder=msg['folder'],
      deleted=msg['deleted'],
      size=msg.get('size', 0),
      device=self.device,
      ctime=msg['ctime'],
      mtime=msg['mtime'],
    )

    await self.vault.push(record)
    await self.result()
  
  async def on_pull(self, msg: dict):
    uid = msg['uid']
    record = self.vault.get_record(uid)
    pieces = size_to_pieces(record.size)

    msg = {
      'size': record.size,
      'pieces': pieces,
      'deleted': record.deleted,
    }

    await self.send(msg)

    if record.size > 0:
      f = storage.get_file_object(self.vault.vault_id, record.hash)
      try:
        for _ in range(pieces):
          chunk = f.read(CHUNK_SIZE)
          await self.ws.send_bytes(chunk)
      finally:
        f.close()
  
  async def get_deleted(self):
    deleted = self.vault.get_deleted()

    items = [record_to_history(record) for record in deleted]
    
    await self.send({
      'items': items,
    })
  
  async def get_history(self, msg: dict):
    path = msg['path']
    last = msg['last']
    records = self.vault.get_history(path, last)

    items = [record_to_history(record) for record in records]
    
    await self.send({
      'items': items,
      'more': False,
    })
  
  async def restore(self, msg: dict):
    uid = msg['uid']

    await self.vault.restore(uid, self.device)
    await self.result()
  
  async def send_records(self, version: int, initial: bool):
    [lastest, records] = self.vault.get_updates(version, initial)

    for record in records:
      msg = record_to_msg(record)
      msg['op'] = 'push'

      await self.send(msg)

    await self.send({
      'op': 'ready',
      'version': lastest,
    })
  
  async def receive_binary(self):
    while True:
      msg = await self.ws.receive()
      if 'text' in msg:
        data = json.loads(msg['text'])
        assert data['op'] == 'ping'

        await self.send({
          'op': 'pong',
        })
        continue
      
      return msg['bytes']

  async def handle(self, msg: dict):
    logger.debug('handle msg: %s', msg)
    op = msg['op']

    match op:
      case 'size':
        await self.send({
          'size': self.vault.get_size(),
          'limit': SYNC_SIZE_LIMIT,
        })
      case 'ping':
        await self.send({
          'op': 'pong'
        })
      case 'push':
        await self.on_push(msg)
      case 'pull':
        await self.on_pull(msg)
      case 'deleted':
        await self.get_deleted()
      case 'history':
        await self.get_history(msg)
      case 'restore':
        await self.restore(msg)
      case _:
        await self.result()
