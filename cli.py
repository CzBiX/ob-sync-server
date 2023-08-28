#!/usr/bin/env python3

import argparse

from sqlmodel import Session

from src import model
from src.depends import engine
from src.utils import generate_secret, hash_password

parser = argparse.ArgumentParser()
sub_parser = parser.add_subparsers(dest='command')

create_database_parser = sub_parser.add_parser('create-database')

create_user_parser = sub_parser.add_parser('create-user')
create_user_parser.add_argument('name', type=str)
create_user_parser.add_argument('email', type=str)
create_user_parser.add_argument('password', type=str)

args = parser.parse_args()

def create_database():
  model.create_db_and_tables(engine)

def create_user(name: str, email: str, password: str):
  with Session(engine) as db:
    salt = generate_secret()
    password_hash = hash_password(password, salt)
    user = model.User(name=name, email=email, password=password_hash, salt=salt)
    db.add(user)
    db.commit()

    db.refresh(user)
  
  print(f'User created, uid: {user.id}.')

def main():
  match args.command:
    case 'create-database':
      create_database()
    case 'create-user':
      create_user(args.name, args.email, args.password)
    case _:
      parser.print_help()

if __name__ == '__main__':
  main()