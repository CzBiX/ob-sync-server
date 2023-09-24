import logging
from typing import Callable, Optional
from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

logger = logging.getLogger(__name__)

def _create_database(op: Operations):
  from .model import create_db_and_tables

  create_db_and_tables(op.get_bind())

  context = op.get_context()
  context._ensure_version_table()
  
  context.execute(
    context._version.insert().values(str(LATEST_VERSION))
  )

  return LATEST_VERSION

def _from_1(op: Operations):
  op.add_column('documentrecord', sa.Column(
    'relatedpath', sa.String(), nullable=False, index=True, default=''
  ))


_ACTIONS: list[Callable[[Operations], Optional[int]]] = [
  _create_database,
  _from_1,
]

LATEST_VERSION = len(_ACTIONS)

def run_migrations(conn):
  context = MigrationContext.configure(conn, opts={'version_table': 'db_version'})
  op = Operations(context)

  version = context.get_current_revision()
  version = int(version) if version else 0

  while version < LATEST_VERSION:
    logger.info(f'Running migration {version}')

    with context.begin_transaction():
      action = _ACTIONS[version]
      version = action(op) or (version + 1)

      context.execute(
        context._version.update().values(
          version_num=str(version)
        )
      )
  
  context.connection.rollback()
  
