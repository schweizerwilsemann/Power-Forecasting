from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.dependencies import get_container
from .api.routes import router

app = FastAPI(title='PV Power Forecasting API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)


@app.on_event('startup')
def startup_event() -> None:
    container = get_container()
    if container.model_gateway.is_ready():
        # Prime the cache to avoid load latency on first request.
        try:
            container.model_gateway.get_state()
        except Exception:
            # Allow the application to start; endpoints will surface precise errors.
            pass
