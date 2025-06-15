# server/database/services/graph_service.py
"""
Minimal Graph Service - LLM-Driven Graph Building
Core functions for LLM-generated Cypher execution
"""

from ..db_connection import db_connection
import logging
import json

class GraphService:
    @staticmethod
    def execute_cypher(query, parameters=None):
        """Execute any Cypher query (read or write)"""
        try:
            with db_connection.get_session() as session:
                def execute_txn(tx):
                    result = tx.run(query, parameters or {})
                    return [record.data() for record in result]
                
                return session.execute_write(execute_txn)
        except Exception as e:
            logging.error(f"Cypher execution failed: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Parameters: {parameters}")
            raise
    
    @staticmethod
    def validate_cypher_safety(query):
        """Basic safety check for LLM-generated Cypher"""
        query_upper = query.upper()
        
        # Block dangerous operations
        forbidden = ['DROP', 'DELETE ALL', 'DETACH DELETE ALL', 'REMOVE']
        if any(dangerous in query_upper for dangerous in forbidden):
            raise ValueError(f"Unsafe Cypher operation detected: {query}")
        
        # Must be CREATE, MERGE, MATCH, or SET operations
        allowed_starts = ['CREATE', 'MERGE', 'MATCH', 'SET', 'WITH']
        if not any(query_upper.strip().startswith(allowed) for allowed in allowed_starts):
            raise ValueError(f"Only CREATE, MERGE, MATCH, SET operations allowed: {query}")
        
        return True
    
    @staticmethod
    def execute_llm_cypher(cypher_response):
        """Execute LLM-generated Cypher with safety checks"""
        try:
            # Parse LLM response (expecting JSON with query and parameters)
            if isinstance(cypher_response, str):
                parsed = json.loads(cypher_response)
            else:
                parsed = cypher_response
            
            query = parsed.get('query', '')
            parameters = parsed.get('parameters', {})
            
            if not query:
                logging.warning("Empty query from LLM")
                return []
            
            # Safety validation
            GraphService.validate_cypher_safety(query)
            
            # Execute query
            logging.info(f"Executing LLM-generated Cypher: {query[:100]}...")
            result = GraphService.execute_cypher(query, parameters)
            
            logging.info(f"LLM Cypher executed successfully, {len(result)} results")
            return result
            
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM Cypher response: {e}")
            return []
        except ValueError as e:
            logging.error(f"Unsafe LLM Cypher blocked: {e}")
            return []
        except Exception as e:
            logging.error(f"LLM Cypher execution failed: {e}")
            return []