import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.auth.views import router as auth_router
from app.core import lifespan
from app.core.config import get_settings
from app.probe.views import router as probe_router
from app.api.routes.post import router as post_router

logger = logging.getLogger(__name__)


app = FastAPI(
    title="minimal fastapi postgres template",
    version="7.0.0",
    description="https://github.com/rafsaf/minimal-fastapi-postgres-template",
    openapi_url="/openapi.json",
    docs_url="/",
    lifespan=lifespan.lifespan,
)

# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",#前端Vite
        "http://localhost:8000"#后端
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(probe_router, prefix="/probe", tags=["probe"])
app.include_router(post_router, prefix="/api", tags=["posts"])



# Guards against HTTP Host Header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_settings().security.allowed_hosts,
)
