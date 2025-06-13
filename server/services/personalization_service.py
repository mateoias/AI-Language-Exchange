# This orchestrates the personalization process
from database.neo4j_service import Neo4jService
from services.personalization_extractor import PersonalizationExtractor

class PersonalizationService:
    """Business logic for handling personalization"""
    def __init__(self):
        self.extractor = PersonalizationExtractor()
        self.neo4j = Neo4jService()
    
    def process_personalization(self, user_id, form_data):
        # 1. Extract entities using LLM
        extracted_data = self.extractor.extract_from_form(user_id, form_data)
        
        # 2. Store in graph database
        if self.neo4j.is_connected() and extracted_data:
            self._store_in_graph(user_id, extracted_data)
        
        return extracted_data
    
    def _store_in_graph(self, user_id, extracted_data):
        # Orchestrate the database operations
        self.neo4j.create_user_node(user_id)
        
        for entity in extracted_data['entities']:
            self.neo4j.create_entity(
                entity['type'], 
                entity['text'], 
                entity['context']
            )
        
        for rel in extracted_data['relationships']:
            self.neo4j.create_relationship(
                user_id,
                rel['predicate'],
                rel['object'],
                rel['confidence']
            )