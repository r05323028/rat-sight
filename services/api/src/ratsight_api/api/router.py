from fastapi import APIRouter
from ratsight_api.api.routes.health import router as health_router
from ratsight_api.api.routes.layers import router as layers_router
from ratsight_api.api.routes.simulations import router as simulations_router
from ratsight_api.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(system_router)
api_router.include_router(layers_router)
api_router.include_router(simulations_router)
