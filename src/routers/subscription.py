from fastapi import APIRouter

router = APIRouter()

@router.post('/list')
def list_subscription():
  return {
    'sync': True,
  }