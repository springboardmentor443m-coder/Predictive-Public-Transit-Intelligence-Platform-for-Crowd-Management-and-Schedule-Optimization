import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "metroflow_db"

client = None
db = None

async def init_mongo_connection():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        # Server run avthundo ledo test cheyadaniki ping
        await client.admin.command('ping')
        db = client[DATABASE_NAME]
        print("\n" + "="*50)
        print(" [✓] MongoDB Connected Successfully!")
        print(f" [✓] Active Database : {DATABASE_NAME}")
        print(f" [✓] Connection URL : {MONGO_URL}")
        print("="*50 + "\n")
    except Exception as e:
        print("\n" + "="*50)
        print(" [✗] MongoDB Connection Failed!")
        print(f" [✗] Error: {e}")
        print("="*50 + "\n")

def get_database():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DATABASE_NAME]
    return db

async def close_mongo_connection():
    global client
    if client:
        client.close()
        client = None