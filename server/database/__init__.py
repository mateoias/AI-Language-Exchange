# server/database/__init__.py
"""
Database package - LLM-driven graph building
Main interface for graph operations
"""

from .db_connection import db_connection
from .services import GraphService, LLMGraphService, InitService

# ============ MAIN INTERFACE ============

class GraphManager:
    """
    Simple interface for all graph operations
    This is what other services should import and use
    """
    
    def __init__(self):
        self.llm_graph = LLMGraphService()
    
    def initialize_database(self):
        """Initialize the graph with minimal setup"""
        return InitService.initialize_database()
    
    def setup_user(self, user_data):
        """Create user node in graph"""
        return InitService.create_user_node(user_data)
    
    def process_conversation(self, user_id, messages):
        """Analyze conversation and update graph"""
        return self.llm_graph.process_conversation_for_graph(user_id, messages)
    
    def process_personalization(self, user_id, personalization_data):
        """Process personalization form data through LLM"""
        return self.llm_graph.update_user_graph_from_personalization(user_id, personalization_data)
    
    def get_conversation_context(self, user_id):
        """Get user's graph context for conversation prompts"""
        return self.llm_graph.get_conversation_context(user_id)
    
    def get_stats(self):
        """Get graph statistics"""
        return InitService.get_graph_stats()
    
    def execute_raw_cypher(self, query, parameters=None):
        """Execute raw Cypher (for admin/debug use)"""
        return GraphService.execute_cypher(query, parameters)

# ============ SINGLETON INSTANCE ============

# Create a singleton instance for easy importing
graph_manager = GraphManager()

# ============ CONVENIENCE FUNCTIONS ============

def initialize_graph():
    """Initialize the graph database"""
    return graph_manager.initialize_database()

def setup_user_graph(user_data):
    """Setup user in graph"""
    return graph_manager.setup_user(user_data)

def analyze_conversation(user_id, messages):
    """Analyze conversation and update graph"""
    return graph_manager.process_conversation(user_id, messages)

def update_from_personalization(user_id, personalization_data):
    """Update graph from personalization form"""
    return graph_manager.process_personalization(user_id, personalization_data)

def get_user_context(user_id):
    """Get user context for conversations"""
    return graph_manager.get_conversation_context(user_id)

def get_graph_stats():
    """Get graph statistics"""
    return graph_manager.get_stats()

# ============ EXPORTS ============

__all__ = [
    'db_connection',
    'graph_manager',
    'initialize_graph',
    'setup_user_graph', 
    'analyze_conversation',
    'update_from_personalization',
    'get_user_context',
    'get_graph_stats'
]