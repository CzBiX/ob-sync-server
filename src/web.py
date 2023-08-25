import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware import cors
from fastapi.responses import JSONResponse

from .routers import sync, subscription, user, vault

logger = logging.getLogger(__name__)

app = FastAPI()

OBSIDIAN_APP_URLS = (
  'app://obsidian.md',
  'capacitor://localhost',
  'http://localhost',
)

app.add_middleware(
  cors.CORSMiddleware,
  allow_origins=OBSIDIAN_APP_URLS,
  allow_methods=('*',),
  allow_credentials=True,
)

@app.exception_handler(HTTPException)
def catch_exceptions(_, exc: HTTPException):
  logger.warn('Exception caught', exc_info=exc)
  data = {
    'error': exc.detail,
    'status_code': exc.status_code,
  }
  
  return JSONResponse(data)

app.include_router(sync.router, prefix='/sync')
app.include_router(subscription.router, prefix='/subscription')
app.include_router(user.router, prefix='/user')
app.include_router(vault.router, prefix='/vault')