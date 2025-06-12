# server/database/services/init_service.py
"""
Minimal Graph Initialization Service
Only creates super seven verbs and basic user structure
"""

from .graph_service import GraphService
import logging
from datetime import datetime

class InitService:
    
    # Only the super seven verbs - everything else comes from LLM analysis
    SUPER_SEVEN_VERBS = [
        "is", "has", "wants", "likes", "goes", "sees", "gives"
    ]
    
    @staticmethod
    def initialize_super_seven():
        """Initialize only the TPRS super seven verbs"""
        logging.info("Initializing TPRS Super Seven verbs...")
        
        query = """
        UNWIND $verbs as verb
        MERGE (w:Word {text: verb})
        SET w.pos = 'verb',
            w.category = 'super7',
            w.frequency = 'high',
            w.created_at = $timestamp
        RETURN count(w) as created
        """
        
        try:
            result = GraphService.execute_cypher(query, {
                "verbs": InitService.SUPER_SEVEN_VERBS,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            count = result[0]['created'] if result else 0
            logging.info(f"Initialized {count} super seven verbs")
            return count
            
        except Exception as e:
            logging.error(f"Failed to initialize super seven verbs: {e}")
            return 0
    
    @staticmethod
    def create_user_node(user_data):
        """Create a basic user node"""
        query = """
        MERGE (u:User {email: $email})
        SET u.id = $id,
            u.username = $username,
            u.native_language = $native_language,
            u.learning_language = $learning_language,
            u.created_at = $created_at,
            u.last_active = $last_active
        RETURN u.id as user_id
        """
        
        try:
            result = GraphService.execute_cypher(query, {
                "email": user_data["email"],
                "id": user_data.get("id", user_data["email"]),  # Use email as fallback ID
                "username": user_data["username"],
                "native_language": user_data["nativeLanguage"],
                "learning_language": user_data["learningLanguage"],
                "created_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat()
            })
            
            user_id = result[0]['user_id'] if result else None
            logging.info(f"Created/updated user node: {user_data['username']} ({user_id})")
            return user_id
            
        except Exception as e:
            logging.error(f"Failed to create user node for {user_data['username']}: {e}")
            return None
    
    @staticmethod
    def initialize_database():
        """Complete minimal database initialization"""
        logging.info("Starting minimal database initialization...")
        
        try:
            # Only initialize super seven verbs
            verb_count = InitService.initialize_super_seven()
            
            logging.info(f"Database initialization complete: {verb_count} verbs created")
            return {
                "success": True,
                "verbs_created": verb_count,
                "message": "Minimal graph initialized with super seven verbs"
            }
            
        except Exception as e:
            logging.error(f"Database initialization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_graph_stats():
        """Get basic graph statistics"""
        try:
            queries = [
                ("Users", "MATCH (u:User) RETURN count(u) as count"),
                ("Words", "MATCH (w:Word) RETURN count(w) as count"),
                ("Entities", "MATCH (n) WHERE NOT n:User AND NOT n:Word RETURN count(n) as count"),
                ("Relationships", "MATCH ()-[r]->() RETURN count(r) as count")
            ]
            
            stats = {}
            for name, query in queries:
                result = GraphService.execute_cypher(query)
                stats[name.lower()] = result[0]['count'] if result else 0
            
            return stats
            
        except Exception as e:
            logging.error(f"Failed to get graph stats: {e}")
            return {"error": str(e)}