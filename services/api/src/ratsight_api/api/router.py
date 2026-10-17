from fastapi import APIRouter
from ratsight_api.api.routes.administrative_districts import (
    router as administrative_districts_router,
)
from ratsight_api.api.routes.health import router as health_router
from ratsight_api.api.routes.layers import router as layers_router
from ratsight_api.api.routes.rodent_reports import router as rodent_reports_router
from ratsight_api.api.routes.simulations import router as simulations_router
from ratsight_api.api.routes.stormwater_pipelines import router as stormwater_pipelines_router
from ratsight_api.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(system_router)
api_router.include_router(layers_router)
api_router.include_router(simulations_router)
api_router.include_router(administrative_districts_router)
api_router.include_router(stormwater_pipelines_router)
api_router.include_router(rodent_reports_router)
