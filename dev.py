#!/usr/bin/env python3

import logging

logging.root.setLevel(logging.DEBUG)

def main():
  from uvicorn import run
  
  run('src.web:app', reload=True, reload_dirs=['src'], host='0.0.0.0')

if __name__ == '__main__':
  main()