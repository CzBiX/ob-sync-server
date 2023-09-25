import logging
from typing import Callable, Optional
from alembic.migration import MigrationContext
from alembic.operations import Operations
import sqlalchemy as sa

logger = logging.getLogger(__name__)

def _create_database(op: Operations):
  conn = op.get_bind()
  inspector = sa.inspect(conn)

  # database is created before adding the version feature
  has_table = inspector.has_table('user')
  if not has_table:
    from .model import create_db_and_tables

    create_db_and_tables(conn)

  context = op.get_context()
  context._ensure_version_table()
  
  version = 1 if has_table else LATEST_VERSION
  context.execute(
    context._version.insert().values(str(version))
  )

  return version

def _from_1(op: Operations):
  op.add_column('documentrecord', sa.Column(
    'relatedpath', sa.String(), nullable=False, index=True, server_default=''
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

  logger.info(f'Current database version: {version}')

  while version < LATEST_VERSION:
    logger.info(f'Running migration from {version}')

    with context.begin_transaction():
      action = _ACTIONS[version]
      version = action(op) or (version + 1)

      context.execute(
        context._version.update().values(
          version_num=str(version)
        )
      )

