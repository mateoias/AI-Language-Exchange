from neo4j import GraphDatabase
from ..config import Config
import logging

class Neo4jConnection:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
            cls._instance.driver = None
        return cls._instance
    
    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)            )
            self.driver.verify_connectivity()
            logging.info("Connected to Neo4j Aura successfully")
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j Aura: {e}")
            raise
    
    def get_session(self):
        if not self.driver:
            self.connect()
        return self.driver.session(database=Config.NEO4J_DATABASE)
    
    def close(self):
        if self.driver:
            self.driver.close()

db_connection = Neo4jConnection()