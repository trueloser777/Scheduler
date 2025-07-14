from fastapi import APIRouter


router = APIRouter(prefix='/v1')


for api_router in []:
    router.include_router(api_router)
