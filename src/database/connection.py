"""
MongoDB Connection Handler for DCorp Backend
--------------------------------------------

• Creates a single global MongoClient (recommended by MongoDB)
• Pulls all credentials from settings.py (which loads .env)
• Enables connection pooling & safe timeouts
• Provides get_db() and get_collection() helpers
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from config.settings import settings

_client = None
_database = None


def get_db():
    """
    Returns a singleton MongoDB database connection.
    Automatically initializes on first call.
    """

    global _client, _database

    if _client is not None:
        return _database

    try:
        # Create MongoDB client with proper production defaults
        _client = MongoClient(
            settings.MONGO_URI,
            maxPoolSize=20,             # avoid connection explosion
            minPoolSize=2,              # keep warm connections
            serverSelectionTimeoutMS=5000,  # fail fast if unreachable
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
        )

        _database = _client[settings.MONGO_DB]

        # Force connection check
        _client.admin.command("ping")
        print(f"✅ MongoDB Connected: {settings.MONGO_DB}")

    except (ConnectionFailure, ConfigurationError) as e:
        print("\n❌ MongoDB Connection Failed")
        print(f"Error: {e}\n")
        raise RuntimeError("Unable to connect to MongoDB") from e

    return _database


def get_collection(name: str):
    """
    Returns a MongoDB collection from the active database.
    """

    db = get_db()
    return db[name]
