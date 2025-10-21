from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
import os
from beanie import init_beanie
from app.models.user import User, BloodQA, Product, Subscription

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")


# Global client and db
client: AsyncIOMotorClient = None
db = None

async def connect_to_mongo():
    """
    Initialize MongoDB client and test connection (async).
    """
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        # Test connection using ping command
        await client.admin.command("ping")

        # Get the default database from the URI
        db = client.get_database()
        print("✅ Pinged your deployment. Connected to MongoDB successfully!")

    except PyMongoError as e:
        print("❌ MongoDB connection failed:", str(e))
        raise e  # optional: stop FastAPI startup
async def init_db():
    await connect_to_mongo()  # initialize global `client` and `db`
    await init_beanie(
        database=db,  # use the db from your centralized database.py
        document_models=[User, BloodQA, Product, Subscription]
    )
async def close_mongo_connection():
    """
    Close the MongoDB client (async-safe).
    """
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed.")



