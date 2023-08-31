import os


PREFIX = 'data/blobs'

def get_vault_dir(vault_id: int):
  return os.path.join(PREFIX, str(vault_id))

def get_file_path(vault_id: int, path_hash: str):
  path = os.path.join(
    PREFIX, str(vault_id),
    path_hash[:2], path_hash[2:4], path_hash[4:],
  )
  
  return path

def get_file_object(vault_id: int, path_hash: str, readonly: bool = True):
  path = get_file_path(vault_id, path_hash)

  if not readonly:
    os.makedirs(os.path.dirname(path), exist_ok=True)

  f = open(path, 'rb' if readonly else 'wb')

  return f
