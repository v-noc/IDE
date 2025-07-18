from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import ArangoError
from ..config.settings import settings

# Initialize the ArangoDB client
client = ArangoClient(hosts=settings.ARANGO_HOST)

def get_db() -> StandardDatabase:
    """Get database connection with error handling"""
    try:
        # Connect to the database
        db: StandardDatabase = client.db(
            settings.ARANGO_DB,
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD,
        )
        return db
    except ArangoError as e:
        raise ConnectionError(f"Failed to connect to ArangoDB: {e}")


# Initialize default database connection
db: StandardDatabase = get_db()
