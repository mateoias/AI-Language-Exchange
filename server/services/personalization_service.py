# This orchestrates the personalization process
from ..database.neo4j_service import Neo4jService
from ..database import update_from_personalization  # Use existing database functions
from .personalization_extractor import PersonalizationExtractor
import logging

class PersonalizationService:
    """Business logic for handling personalization"""
    def __init__(self):
        self.extractor = PersonalizationExtractor()
        try:
            self.neo4j = Neo4jService()
        except Exception as e:
            logging.warning(f"Neo4j service initialization failed: {e}")
            self.neo4j = None
    
    def process_personalization(self, user_id, form_data):
        """
        Process personalization data - TWO OPTIONS:
        Option 1: Use your existing PersonalizationExtractor (more direct)
        Option 2: Use LLMGraphService (goes through conversation analysis)
        """
        try:
            logging.info(f"Starting personalization processing for user {user_id}")
            
            # OPTION 1: Use PersonalizationExtractor directly (recommended)
            extracted_data = self.extractor.extract_from_form(user_id, form_data)
            
            if extracted_data and (extracted_data.get('entities') or extracted_data.get('relationships')):
                # Store the extracted data directly using existing Neo4j functions
                success = self._store_extracted_data_directly(user_id, extracted_data)
                if success:
                    logging.info(f"Successfully stored personalization data for user {user_id}")
                    return extracted_data
                else:
                    logging.error(f"Failed to store personalization data for user {user_id}")
            
            # OPTION 2: Use LLMGraphService (if you prefer the conversation-style analysis)
            # success = update_from_personalization(user_id, form_data)  # Pass RAW form data, not extracted
            
            return extracted_data
            
        except Exception as e:
            logging.error(f"Personalization processing failed for user {user_id}: {e}")
            import traceback
            logging.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def _store_extracted_data_directly(self, user_id, extracted_data):
        """
        Store extracted entities and relationships directly in Neo4j
        This bypasses the LLMGraphService double-processing
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
    
    def process_personalization_via_llm_service(self, user_id, form_data):
        """
        Alternative: Use LLMGraphService (pass RAW form data, not extracted data)
        """
        try:
            # Pass the RAW form data to LLMGraphService for processing
            success = update_from_personalization(user_id, form_data)  # RAW form data
            return success
        except Exception as e:
            logging.error(f"LLM service personalization failed for user {user_id}: {e}")
            return False
    
    def clear_user_personalization(self, user_id):
        """
        Clear personalization data from graph database
        """
        try:
            if self.neo4j and self.neo4j.is_connected():
                return self.neo4j.clear_user_personalization(user_id)
            return False
        except Exception as e:
            logging.error(f"Failed to clear personalization for user {user_id}: {e}")
            return False