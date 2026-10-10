from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.health import router as health_router
from app.routes.calls import router as calls_router
from app.routes.webhooks import router as webhooks_router
from app.routes.profiles import router as profiles_router
from app.database import get_db, close_db_connection, create_indexes
from app.config import MONGODB_DB_NAME
from app.config import ALLOWED_ORIGINS

# Global collection variable - will be set in lifespan
db_collection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global db_collection
    # Initialize MongoDB client
    client = await get_db()
    db_collection = client[MONGODB_DB_NAME]["calls"]
    await create_indexes()
    yield
    # Cleanup
    await close_db_connection()


app = FastAPI(
    title="Home Credit LAP Voice Agent Backend",
    description="Backend for Retell AI voice agent assessment",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration - allow origins from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(calls_router)
app.include_router(webhooks_router)
app.include_router(profiles_router)
