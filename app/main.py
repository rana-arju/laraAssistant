from fastapi import FastAPI
from app.routers import user
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import close_mongo_connection,init_db
from app.core.error_handler import init_error_handlers
from app.core.logger import logger
import asyncio

app = FastAPI(
    title="Lara Assistant API",
    description="API for Lara Assistant Application",
    version="1.0.0"
    )


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)

app.include_router(user.router)

# MongoDB connection management
# Connect to MongoDB on startup and close connection on shutdown
@app.on_event("startup")
async def on_startup():
    await init_db()
    logger.info("Connected to MongoDB successfully!")


@app.on_event("shutdown")
async def on_shutdown():
    try:
        await close_mongo_connection()
        logger.info("MongoDB connection closed.")
    except asyncio.CancelledError:
        pass

@app.get("/")
def root():
    return {"message": "Server Runing...."}
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "API is running normally"}
# Global error handler
init_error_handlers(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
