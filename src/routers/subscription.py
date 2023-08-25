from fastapi import APIRouter

router = APIRouter()

@router.post('/subscription/list')
def list_subscription():
  return {
    'sync': True,
  }