"""Kafka utilities for logging and messaging."""

import os
import json
import logging
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaLogger:
    """Kafka logger for sending structured logs."""
    
    def __init__(self, 
                 bootstrap_servers: str = None,
                 topic: str = None,
                 **producer_config):
        """Initialize Kafka logger."""
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = topic or os.getenv('KAFKA_LOG_TOPIC', 'llm-usage-logs')
        
        self.producer_config = {
            'bootstrap_servers': self.bootstrap_servers.split(','),
            'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
            'key_serializer': lambda k: k.encode('utf-8') if k else None,
            **producer_config
        }
        
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer."""
        try:
            self.producer = KafkaProducer(**self.producer_config)
            logger.info(f"Kafka producer initialized for topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None
    
    def log(self, message: Dict[str, Any], key: Optional[str] = None):
        """Send log message to Kafka."""
        if not self.producer:
            logger.warning("Kafka producer not available, skipping log")
            return
        
        try:
            future = self.producer.send(self.topic, value=message, key=key)
            # Don't wait for the result to avoid blocking
            logger.debug(f"Sent message to Kafka topic {self.topic}")
        except KafkaError as e:
            logger.error(f"Failed to send message to Kafka: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending to Kafka: {e}")
    
    def flush(self):
        """Flush pending messages."""
        if self.producer:
            self.producer.flush()
    
    def close(self):
        """Close the Kafka producer."""
        if self.producer:
            self.producer.close()
            self.producer = None


# Global Kafka logger instance
kafka_logger = KafkaLogger()