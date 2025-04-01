from supabase import create_client, Client
from neo4j import GraphDatabase
from typing import Optional
from .config import settings

class DatabaseManager:
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.neo4j_driver = None

    def init_supabase(self) -> Client:
        """Initialize Supabase client"""
        if not self.supabase:
            self.supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_KEY
            )
        return self.supabase

    def init_neo4j(self):
        """Initialize Neo4j driver"""
        if not self.neo4j_driver:
            self.neo4j_driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
        return self.neo4j_driver

    def close_neo4j(self):
        """Close Neo4j driver connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            self.neo4j_driver = None

    def verify_connections(self) -> bool:
        """Verify database connections"""
        try:
            # Test Supabase connection
            supabase = self.init_supabase()
            supabase.table('health_check').select('*').limit(1).execute()

            # Test Neo4j connection
            neo4j = self.init_neo4j()
            with neo4j.session() as session:
                session.run("MATCH (n) RETURN count(n) LIMIT 1")

            return True
        except Exception as e:
            print(f"Connection verification failed: {str(e)}")
            return False

# Create a global database manager instance
db_manager = DatabaseManager()

def get_supabase() -> Client:
    """Get Supabase client instance"""
    return db_manager.init_supabase()

def get_neo4j():
    """Get Neo4j driver instance"""
    return db_manager.init_neo4j()

def close_neo4j():
    """Close Neo4j connection"""
    db_manager.close_neo4j() 