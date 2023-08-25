from datetime import datetime
import hashlib
import secrets
import string
import uuid


def scrypt_key(pwd: bytes, salt: bytes):
  return hashlib.scrypt(
    pwd, salt=salt,
    n=32768, r=8, p=1, dklen=32, maxmem=64*1024*1024
  )

def get_keyhash(pwd: str, salt: str):
  key = scrypt_key(pwd.encode(), salt.encode())
  return hashlib.sha256(key).hexdigest()

def generate_secret(len: int = 20):
  salt = ''
  for i in range(len):
    salt += secrets.choice(string.printable)
  
  return salt

def hash_password(pwd: str, salt: str):
  return scrypt_key(pwd.encode(), salt.encode()).hex()

def verify_password(pwd: str, salt: str, hash: str):
  return secrets.compare_digest(hash_password(pwd, salt), hash)

def generate_token():
  u = uuid.uuid4()

  return u.hex

def datetime_to_ts(dt: datetime):
  return int(dt.timestamp() * 1000)

def ts_to_datetime(ts: int):
  return datetime.fromtimestamp(ts / 1000)