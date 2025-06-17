# services/personalization_service.py
from ..database import update_from_personalization
from .personalization_extractor import PersonalizationExtractor
import logging

class PersonalizationService:
    """Business logic for handling personalization"""
    def __init__(self):
        self.extractor = PersonalizationExtractor()
    
    def process_personalization(self, user_id, form_data):
        """
        Process personalization data using PersonalizationExtractor
        """
        try:
            logging.info(f"Starting personalization processing for user {user_id}")
            
            # Use PersonalizationExtractor directly
            extracted_data = self.extractor.extract_from_form(user_id, form_data)
            
            if extracted_data and (extracted_data.get('entities') or extracted_data.get('relationships')):
                # Store the extracted data directly using existing Neo4j functions
                success = self._store_extracted_data_directly(user_id, extracted_data)
                if success:
                    logging.info(f"Successfully stored personalization data for user {user_id}")
                    return extracted_data
                else:
                    logging.error(f"Failed to store personalization data for user {user_id}")
            
            return extracted_data
            
        except Exception as e:
            logging.error(f"Personalization processing failed for user {user_id}: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _store_extracted_data_directly(self, user_id, extracted_data):
        """
        Store extracted entities and relationships directly in Neo4j
        """
        try:
            from ..database.services.graph_service import GraphService
            from datetime import datetime
            
            # Create user node if it doesn't exist
            user_query = """
            MERGE (u:User {id: $user_id})
            SET u.last_updated = $timestamp
            """
            GraphService.execute_cypher(user_query, {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Store entities
            entities_stored = 0
            for entity in extracted_data.get('entities', []):
                entity_query = """
                MERGE (u:User {id: $user_id})
                MERGE (e:Entity {text: $text, type: $type})
                SET e.context = $context,
                    e.created_at = $timestamp
                """
                GraphService.execute_cypher(entity_query, {
                    "user_id": user_id,
                    "text": entity.get('text', ''),
                    "type": entity.get('type', 'Unknown'),
                    "context": entity.get('context', ''),
                    "timestamp": datetime.utcnow().isoformat()
                })
                entities_stored += 1
            
            # Store relationships
            relationships_stored = 0
            for rel in extracted_data.get('relationships', []):
                rel_query = """
                MERGE (u:User {id: $user_id})
                MERGE (e:Entity {text: $object})
                MERGE (u)-[r:RELATIONSHIP {type: $predicate}]->(e)
                SET r.confidence = $confidence,
                    r.created_at = $timestamp
                """
                GraphService.execute_cypher(rel_query, {
                    "user_id": user_id,
                    "object": rel.get('object', ''),
                    "predicate": rel.get('predicate', 'RELATED_TO'),
                    "confidence": rel.get('confidence', 'medium'),
                    "timestamp": datetime.utcnow().isoformat()
                })
                relationships_stored += 1
            
            logging.info(f"Stored {entities_stored} entities and {relationships_stored} relationships for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store extracted data for user {user_id}: {e}")
            return False
    
    def clear_user_personalization(self, user_id):
        """
        Clear personalization data from graph database
        """
        try:
            from ..database.services.graph_service import GraphService
            
            # Delete all relationships and entities connected to the user
            clear_query = """
            MATCH (u:User {id: $user_id})-[r]->(e:Entity)
            DELETE r
            """
            GraphService.execute_cypher(clear_query, {"user_id": user_id})
            
            logging.info(f"Cleared personalization data for user {user_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to clear personalization for user {user_id}: {e}")
            return False