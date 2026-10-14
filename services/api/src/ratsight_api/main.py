from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ratsight_api.api.router import api_router
from ratsight_api.infrastructure.config import get_settings
from ratsight_api.infrastructure.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="RatSight API",
    version="0.1.0",
    description=(
        "Evidence-aware urban movement simulation foundation. "
        "Preview outputs are synthetic and simulated."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(api_router)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    import logging

    logging.getLogger("ratsight.api").exception("unhandled_api_error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
