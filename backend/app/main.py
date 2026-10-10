from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import extract, summarize, score, pipeline
from app.pipeline.embedding.faiss_index import FAISSIndex
from app.services.cache import RedisCache
import logging

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting LexRisk Pipeline Service")
    # Startup: initialize FAISS index and Redis
    app.state.faiss_index = FAISSIndex(settings.faiss_index_dir)
    app.state.cache = RedisCache(settings.redis_url)
    await app.state.cache.connect()
    yield
    logger.info("Shutting down LexRisk Pipeline Service")
    await app.state.cache.disconnect()

app = FastAPI(
    title="LexRisk Pipeline Service",
    description="Contract clause extraction, summarization, and risk scoring",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
app.include_router(extract.router, prefix="", tags=["extract"])
app.include_router(summarize.router, prefix="", tags=["summarize"])
app.include_router(score.router, prefix="", tags=["score"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "lexrisk-backend"}
