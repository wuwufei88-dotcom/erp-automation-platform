from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.registry import init_registry
from app.api.router import api_router
from app.api.stream import router as stream_router
from app.api.ws import router as ws_router
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    from app.models import Base
    from app.database import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    init_registry(settings.agent_config_dir)
    logger.info("Agent registry initialized")

    from app.cache import get_redis
    await get_redis()
    logger.info("Redis connected")
    yield
    from app.cache import close_redis
    await close_redis()


app = FastAPI(title="ERP Delivery Platform", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")
