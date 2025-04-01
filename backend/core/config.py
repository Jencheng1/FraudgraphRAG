from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    # Neo4j settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # API settings
    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "")
    API_ALGORITHM: str = os.getenv("API_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Model settings
    MODEL_PATH: str = os.getenv("MODEL_PATH", "./models/fraud_detection_model.pt")
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    LEARNING_RATE: float = float(os.getenv("LEARNING_RATE", "0.001"))

    # Frontend settings
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))

    # Kafka settings
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "")
    KAFKA_API_KEY: str = os.getenv("KAFKA_API_KEY", "")
    KAFKA_API_SECRET: str = os.getenv("KAFKA_API_SECRET", "")
    KAFKA_SCHEMA_REGISTRY_URL: str = os.getenv("KAFKA_SCHEMA_REGISTRY_URL", "")
    KAFKA_SCHEMA_REGISTRY_API_KEY: str = os.getenv("KAFKA_SCHEMA_REGISTRY_API_KEY", "")
    KAFKA_SCHEMA_REGISTRY_API_SECRET: str = os.getenv("KAFKA_SCHEMA_REGISTRY_API_SECRET", "")
    KAFKA_TRANSACTIONS_TOPIC: str = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")
    KAFKA_ALERTS_TOPIC: str = os.getenv("KAFKA_ALERTS_TOPIC", "fraud_alerts")

    class Config:
        env_file = ".env"

settings = Settings() 