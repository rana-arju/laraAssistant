from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from motor.motor_asyncio import AsyncIOMotorClient
from qdrant_client import QdrantClient

# Import models
from app.models.user import User
from app.models.subscription import Subscription
from app.models.scheduled_post import ScheduledPost
from app.models.scheduled_email import ScheduledEmail
from app.models.ai_chat_log import AiChatLog, TokenUsage
from app.models.notification import Notification
# Remove this line!
from app.database.database import init_db, close_mongo_connection

# Import routers
from app.routes import user
from app.routes import ai_chat, voice_chat, schedule

# Import utilities
from app.utils.response import send_response, send_error
from app.core.error_handler import init_error_handlers
from app.core.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:

        await init_db()  # single centralized DB initialization
        logger.info(" MongoDB + Beanie initialized!")
   
        # Initialize Qdrant client
        app.state.qdrant = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333"))
        )
        
        logger.info("✅ Database connections initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database connections: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed.")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Lara Assistant AI Backend",
        description="FastAPI backend with MongoDB and Qdrant for AI chat, voice processing, and scheduling",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS configuration
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
    if allowed_origins != "*":
        try:
            allowed_origins = eval(allowed_origins)
        except:
            allowed_origins = ["*"]
    else:
        allowed_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # Include routers with API prefix
    app.include_router(user.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(ai_chat.router, prefix="/api/v1/ai/chat", tags=["AI Chat"])
    app.include_router(voice_chat.router, prefix="/api/v1/ai/voice", tags=["Voice Chat"])
    app.include_router(schedule.router, prefix="/api/v1/schedule", tags=["Scheduling"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}")
        return send_error(
            status_code=500,
            message="Internal server error",
            data={"error": str(exc)} if os.getenv("DEBUG", "false").lower() == "true" else None
        )
    
    # Root endpoints
    @app.get("/")
    async def root():
        return send_response(
            status_code=200,
            message="Lara Assistant AI Backend is running",
            data={
                "version": "1.0.0",
                "status": "healthy",
                "features": [
                    "ai_chat",
                    "voice_chat", 
                    "scheduling",
                    "vector_memory"
                ]
            }
        )
    
    @app.get("/health")
    async def health_check():
        return send_response(
            status_code=200,
            message="Service is healthy",
            data={"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}
        )
    
    # Initialize error handlers
    init_error_handlers(app)
    
    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
