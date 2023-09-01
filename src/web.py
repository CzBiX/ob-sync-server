import logging

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .routers import sync, subscription, user, vault

logger = logging.getLogger(__name__)

app = FastAPI()

OBSIDIAN_APP_URLS = (
  'app://obsidian.md',
  'capacitor://localhost',
  'http://localhost',
)

@app.exception_handler(HTTPException)
def catch_exceptions(_, exc: HTTPException):
  logger.warn('Exception caught', exc_info=exc)
  data = {
    'error': exc.detail,
    'status_code': exc.status_code,
  }
  
  return JSONResponse(data)

@app.middleware('http')
async def add_cors_headers(request: Request, call_next):
  if request.method == 'OPTIONS':
    headers = {}

    if origin := request.headers.get('origin'):
      headers['Access-Control-Allow-Origin'] = origin

    if method := request.headers.get('access-control-request-method'):
      headers['Access-Control-Allow-Methods'] = method

    if h := request.headers.get("access-control-request-headers"):
      headers['Access-Control-Allow-Headers'] = h

    return Response(status_code=204, headers=headers)
  
  response = await call_next(request)

  response.headers['Access-Control-Allow-Origin'] = '*'
  
  return response

app.include_router(sync.router, prefix='/sync')
app.include_router(subscription.router, prefix='/subscription')
app.include_router(user.router, prefix='/user')
app.include_router(vault.router, prefix='/vault')