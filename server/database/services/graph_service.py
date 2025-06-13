from neo4j import GraphDatabase
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GraphService:
    def __init__(self):
        self._driver = None
        self._connect()
    
    def _connect(self):
        """Initialize Neo4j connection"""
        try:
            uri = current_app.config.get('NEO4J_URI')
            username = current_app.config.get('NEO4J_USERNAME')
            password = current_app.config.get('NEO4J_PASSWORD')
            
            if uri and username and password:
                self._driver = GraphDatabase.driver(uri, auth=(username, password))
                # Test connection
                self._driver.verify_connectivity()
                logger.info("Neo4j connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")
            self._driver = None
    
    def is_connected(self):
        """Check if Neo4j is connected"""
        return self._driver is not None
    
    def update_user_graph(self, user_id, extracted_info):
        """Update user's graph with extracted entities and relationships"""
        if not self._driver:
            return {'success': False, 'error': 'Neo4j not connected'}
        
        try:
            with self._driver.session() as session:
                # Ensure user node exists
                session.run(
                    "MERGE (u:User {id: $user_id})",
                    user_id=user_id
                )
                
                # Add entities
                for entity in extracted_info.get('entities', []):
                    # Create entity node based on type
                    label = entity['type'] if entity['type'] in ['Person', 'Place', 'Animal', 'Activity'] else 'Entity'
                    session.run(
                        f"MERGE (e:{label} {{text: $text, context: $context}})",
                        text=entity['text'],
                        context=entity.get('context', '')
                    )
                
                # Add relationships
                for rel in extracted_info.get('relationships', []):
                    # Direct user relationships
                    if rel['subject'].lower() in ['user', 'john', user_id]:
                        query = f"""
                        MATCH (u:User {{id: $user_id}})
                        MATCH (e {{text: $object}})
                        MERGE (u)-[:{rel['predicate']} {{confidence: $confidence, created_at: timestamp()}}]->(e)
                        """
                        session.run(
                            query,
                            user_id=user_id,
                            object=rel['object'],
                            confidence=rel.get('confidence', 'medium')
                        )
                
                return {'success': True}
                
        except Exception as e:
            logger.error(f"Error updating graph: {str(e)}")
            return {'success': False, 'error': str(e)}
        
    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()