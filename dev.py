#!/usr/bin/env python3

from sqlalchemy import log as sqlalchemy_log

sqlalchemy_log._add_default_handler = lambda x: None  # Patch to avoid duplicate logging

def main():
  from uvicorn import run
  
  run('src.web:app', reload=True, reload_dirs=['src'], host='0.0.0.0')

if __name__ == '__main__':
  main()