import os


PREFIX = 'data/blobs'

def get_file_object(vault_id: int, path_hash: str, readonly: bool = True):
  path = os.path.join(PREFIX, str(vault_id), path_hash[:2], path_hash[2:])

  if not readonly:
    os.makedirs(os.path.dirname(path), exist_ok=True)

  f = open(path, 'rb' if readonly else 'wb')

  return f
