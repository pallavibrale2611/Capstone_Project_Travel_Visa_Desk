"""
Initialize Milvus vector store with required collections
Run this script before starting the application
"""

from src.vector_store.milvus_client import MilvusClient
from src.utils.logger import setup_logging, get_logger
import sys

setup_logging()
logger = get_logger(__name__)

def init_collections():
    """Initialize all Milvus collections."""
    try:
        logger.info("Connecting to Milvus...")
        client = MilvusClient()
        client.connect()
        
        logger.info("Creating collections...")
        
        collections = [
            "visa_requirements",
            "embassy_info",
            "regulations",
            "templates"
        ]
        
        for collection_key in collections:
            try:
                logger.info(f"Creating collection: {collection_key}")
                client.create_collection(collection_key)
                logger.info(f"✓ Collection '{collection_key}' created successfully")
            except Exception as e:
                logger.warning(f"Collection '{collection_key}' may already exist: {str(e)}")
        
        logger.info("✓ All collections initialized successfully")
        
        client.disconnect()
        logger.info("Disconnected from Milvus")
        
    except Exception as e:
        logger.error(f"Failed to initialize collections: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    init_collections()