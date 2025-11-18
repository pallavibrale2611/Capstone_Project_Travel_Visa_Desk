# """
# Milvus Vector Store Client
# Compliant with Section 7: Vector Database Integration Standards
# """

# import yaml
# from typing import List, Dict, Any, Optional
# from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
# from pathlib import Path
# import os

# class MilvusClient:
#     def __init__(self, config_path: str = "config/milvus_config.yaml"):
#         """Initialize Milvus client with configuration."""
#         self.config_path = Path(config_path)
#         self.config = self._load_config()
#         self.connection = None
#         self.collections = {}
        
#     def _load_config(self) -> Dict[str, Any]:
#         """Load Milvus configuration from YAML."""
#         with open(self.config_path, 'r') as f:
#             config = yaml.safe_load(f)
        
#         # Substitute environment variables
#         conn_config = config['connection']
#         for key in conn_config:
#             if isinstance(conn_config[key], str) and conn_config[key].startswith('${'):
#                 env_var = conn_config[key][2:-1]
#                 conn_config[key] = os.getenv(env_var, '')
        
#         return config
    
#     def connect(self):
#         """Establish connection to Milvus."""
#         conn_config = self.config['connection']
#         connections.connect(
#             alias="default",
#             host=conn_config['host'],
#             # port=conn_config['port'],
#             user=conn_config.get('key', ''),
#             # password=conn_config.get('password', ''),
#             timeout=conn_config.get('timeout', 30)
#         )
#         self.connection = connections
        
#     def disconnect(self):
#         """Close connection to Milvus."""
#         if self.connection:
#             connections.disconnect("default")
    
#     def create_collection(self, collection_key: str):
#         """
#         Create a collection based on configuration.
        
#         Args:
#             collection_key: Key from config (e.g., 'visa_requirements')
#         """
#         if collection_key not in self.config['collections']:
#             raise ValueError(f"Collection {collection_key} not found in config")
        
#         coll_config = self.config['collections'][collection_key]
        
#         # Define schema
#         fields = [
#             FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
#             FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=coll_config['dimension']),
#             FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
#             FieldSchema(name="metadata", dtype=DataType.JSON)
#         ]
        
#         schema = CollectionSchema(
#             fields=fields,
#             description=coll_config['description']
#         )
        
#         # Create collection
#         collection = Collection(
#             name=coll_config['name'],
#             schema=schema
#         )
        
#         # Create index
#         index_params = {
#             "index_type": coll_config['index_type'],
#             "metric_type": coll_config['metric_type'],
#             "params": {"nlist": coll_config.get('nlist', 128)}
#         }
        
#         collection.create_index(
#             field_name="embedding",
#             index_params=index_params
#         )
        
#         self.collections[collection_key] = collection
#         return collection
    
#     def get_collection(self, collection_key: str) -> Collection:
#         """Get or create collection."""
#         if collection_key in self.collections:
#             return self.collections[collection_key]
        
#         coll_config = self.config['collections'][collection_key]
#         collection_name = coll_config['name']
        
#         if utility.has_collection(collection_name):
#             collection = Collection(collection_name)
#             self.collections[collection_key] = collection
#             return collection
#         else:
#             return self.create_collection(collection_key)
    
#     def insert(
#         self,
#         collection_key: str,
#         embeddings: List[List[float]],
#         texts: List[str],
#         metadata: List[Dict[str, Any]]
#     ):
#         """
#         Insert vectors into collection.
        
#         Args:
#             collection_key: Collection identifier
#             embeddings: List of embedding vectors
#             texts: List of text content
#             metadata: List of metadata dicts
#         """
#         collection = self.get_collection(collection_key)
        
#         data = [
#             embeddings,
#             texts,
#             metadata
#         ]
        
#         collection.insert(data)
#         collection.flush()
#         collection.load()
    
#     def search(
#         self,
#         collection_key: str,
#         query_embedding: List[float],
#         top_k: Optional[int] = None,
#         filter_expr: Optional[str] = None
#     ) -> List[Dict[str, Any]]:
#         """
#         Search for similar vectors.
        
#         Args:
#             collection_key: Collection identifier
#             query_embedding: Query vector
#             top_k: Number of results to return
#             filter_expr: Optional filter expression
        
#         Returns:
#             List of search results with text and metadata
#         """
#         collection = self.get_collection(collection_key)
#         collection.load()
        
#         search_params = self.config['search_params']
#         if top_k is None:
#             top_k = search_params['top_k']
        
#         results = collection.search(
#             data=[query_embedding],
#             anns_field="embedding",
#             param={"metric_type": "L2", "params": {"nprobe": search_params['nprobe']}},
#             limit=top_k,
#             expr=filter_expr,
#             output_fields=["text", "metadata"]
#         )
        
#         formatted_results = []
#         for hits in results:
#             for hit in hits:
#                 formatted_results.append({
#                     "id": hit.id,
#                     "distance": hit.distance,
#                     "text": hit.entity.get("text"),
#                     "metadata": hit.entity.get("metadata")
#                 })
        
#         return formatted_results
    
#     def delete(self, collection_key: str, expr: str):
#         """Delete entities matching expression."""
#         collection = self.get_collection(collection_key)
#         collection.delete(expr)
    
#     def drop_collection(self, collection_key: str):
#         """Drop a collection."""
#         coll_config = self.config['collections'][collection_key]
#         utility.drop_collection(coll_config['name'])
#         if collection_key in self.collections:
#             del self.collections[collection_key]

"""
Milvus Vector Store Client with Graceful Fallback
"""

import yaml
import logging
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from pymilvus.exceptions import MilvusException
from pathlib import Path
import os
from pymilvus import MilvusClient as mv

class MilvusClient:
    def __init__(self, config_path: str = "config/milvus_config.yaml"):
        """Initialize Milvus client with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.connection = None
        self.collections = {}
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Milvus configuration from YAML."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            conn_config = config['connection']
            for key in conn_config:
                if isinstance(conn_config[key], str) and conn_config[key].startswith('${'):
                    env_var = conn_config[key][2:-1]
                    conn_config[key] = os.getenv(env_var, '')
            
            return config
        except Exception as e:
            self.logger.warning(f"Failed to load Milvus config: {e}")
            return {'connection': {'host': 'localhost'}, 'collections': {}, 'search_params': {}}
    
    def connect(self):
        """Establish connection to Milvus with graceful failure."""
        try:
            conn_config = self.config['connection']
            host = conn_config.get('host', 'localhost')
            milvus_uri = "https://in03-95569f3f2c4d2b1.serverless.aws-eu-central-1.cloud.zilliz.com"
            print(f"Milvus URI: {milvus_uri}")

            token = "21263d114e66c224140a0b61ff0ad6daf69676bc897ce24cb025515248f06fb48b90ffe993e44aaa0620cb7f771d9691c8dd861c"
            self.logger.info(f"Attempting to connect to Milvus at {host}")
            milvus_client = mv(uri=milvus_uri, token=token)
            print(f"Connected to DB: {milvus_uri} successfully")
            collection_name = "visa_kb"
            check_collection = milvus_client.has_collection(collection_name)

            if check_collection:
                self.logger.info(f"Collection {collection_name} exists in Milvus")
            else:
                self.logger.info(f"Collection {collection_name} does not exist in Milvus")

            # connections.connect(
            #     alias="default",
            #     host=host,
            #     port=19530,  # Add explicit port
            #     timeout=10   # Shorter timeout for faster failure
            # )
            

            # # Test connection
            # utility.list_collections()
            self.connected = True
            self.connection = milvus_client
            # self.logger.info("Successfully connected to Milvus")
            
        except MilvusException as e:
            self.connected = False
            self.logger.warning(f"Milvus connection failed: {e}")
            self.logger.warning("Application will run in limited mode without vector search")
            # Don't raise exception - allow application to continue
        except Exception as e:
            self.connected = False
            self.logger.warning(f"Unexpected error connecting to Milvus: {e}")
    
    def is_connected(self):
        """Check if Milvus connection is active."""
        return self.connected
    
    def get_collection(self, collection_key: str) -> Optional[Collection]:
        """Get or create collection with graceful failure."""
        if not self.connected:
            self.logger.warning(f"Cannot get collection {collection_key} - Milvus not connected")
            return None
        
        try:
            if collection_key in self.collections:
                return self.collections[collection_key]
            
            coll_config = self.config['collections'].get(collection_key, {})
            collection_name = coll_config.get('name', collection_key)
            
            if utility.has_collection(collection_name):
                collection = Collection(collection_name)
                self.collections[collection_key] = collection
                return collection
            else:
                return self.create_collection(collection_key)
        except Exception as e:
            self.logger.warning(f"Failed to get collection {collection_key}: {e}")
            return None
    
    def create_collection(self, collection_key: str) -> Optional[Collection]:
        """Create collection with graceful failure."""
        if not self.connected:
            return None
            
        try:
            if collection_key not in self.config['collections']:
                self.logger.warning(f"Collection {collection_key} not found in config")
                return None
            
            coll_config = self.config['collections'][collection_key]
            
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=coll_config['dimension']),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="metadata", dtype=DataType.JSON)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description=coll_config['description']
            )
            
            # Create collection
            collection = Collection(
                name=coll_config['name'],
                schema=schema
            )
            
            # Create index
            index_params = {
                "index_type": coll_config['index_type'],
                "metric_type": coll_config['metric_type'],
                "params": {"nlist": coll_config.get('nlist', 128)}
            }
            
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            self.collections[collection_key] = collection
            return collection
            
        except Exception as e:
            self.logger.warning(f"Failed to create collection {collection_key}: {e}")
            return None
    
    def search(
        self,
        collection_key: str,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors with graceful fallback.
        """
        if not self.connected:
            self.logger.warning(f"Milvus not connected - returning empty results for {collection_key}")
            return []
        
        try:
            collection = self.get_collection(collection_key)
            if collection is None:
                return []
                
            collection.load()
            
            search_params = self.config.get('search_params', {})
            if top_k is None:
                top_k = search_params.get('top_k', 5)
            
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param={"metric_type": "L2", "params": {"nprobe": search_params.get('nprobe', 10)}},
                limit=top_k,
                expr=filter_expr,
                output_fields=["text", "metadata"]
            )
            
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "text": hit.entity.get("text"),
                        "metadata": hit.entity.get("metadata")
                    })
            
            return formatted_results
            
        except Exception as e:
            self.logger.warning(f"Search failed for {collection_key}: {e}")
            return []
    
    def insert(
        self,
        collection_key: str,
        embeddings: List[List[float]],
        texts: List[str],
        metadata: List[Dict[str, Any]]
    ):
        """Insert vectors with graceful failure."""
        if not self.connected:
            self.logger.warning(f"Cannot insert - Milvus not connected")
            return
        
        try:
            collection = self.get_collection(collection_key)
            if collection is None:
                return
                
            data = [
                embeddings,
                texts,
                metadata
            ]
            
            collection.insert(data)
            collection.flush()
            collection.load()
            
        except Exception as e:
            self.logger.warning(f"Insert failed for {collection_key}: {e}")