# server/database/services/llm_graph_service.py
"""
LLM-Driven Graph Building Service
Uses language models to analyze conversations and generate graph updates
"""

from .graph_service import GraphService
from ...services.llm_service import LLMService
import logging
import json

class LLMGraphService:
    def __init__(self):
        self.llm_service = LLMService()
    
    # ============ PROMPTS ============
    
    CONVERSATION_ANALYSIS_PROMPT = """You are a graph database analyst for a language learning app. Analyze this conversation between a user and language tutor to extract meaningful information about the user that should be stored in a knowledge graph.

FOCUS ON:
- Personal facts (family, pets, location, work, hobbies)
- Preferences (likes, dislikes, wants)
- Experiences (places visited, activities done)
- Relationships (knows people, has things)

EXTRACT ONLY information that is:
1. Explicitly stated by the USER (not the tutor)
2. Factual (not opinions about language learning)
3. Useful for future personalized conversations

USER ID: {user_id}
CONVERSATION:
{conversation_messages}

Return a JSON object with extracted information:
{{
  "entities": [
    {{"text": "entity_name", "type": "Person|Place|Animal|Activity|Thing", "context": "brief context"}}
  ],
  "relationships": [
    {{"subject": "user", "predicate": "HAS|LIKES|LIVES_IN|WORKS_AS|KNOWS|VISITED|WANTS", "object": "entity_name", "confidence": "high|medium|low"}}
  ],
  "reasoning": "Brief explanation of what you extracted and why"
}}

If no meaningful information found, return empty arrays."""

    CYPHER_GENERATION_PROMPT = """You are a Neo4j Cypher query generator for a language learning knowledge graph.

TASK: Generate Cypher queries to store the extracted user information.

GRAPH SCHEMA:
- User nodes: (:User {{id: string, username: string, ...}})
- Entity nodes: (:Person|:Place|:Animal|:Activity|:Thing {{text: string, type: string, ...}})
- Relationships: HAS, LIKES, LIVES_IN, WORKS_AS, KNOWS, VISITED, WANTS, etc.

USER INFO TO STORE:
{extracted_info}

REQUIREMENTS:
1. Use MERGE to avoid duplicates
2. Create entity nodes if they don't exist
3. Create relationships between user and entities
4. Set created_at timestamp
5. Only use CREATE, MERGE, MATCH, SET operations
6. Return valid JSON

Generate Cypher query as JSON:
{{
  "query": "MERGE (u:User {{id: $user_id}}) MERGE (e:Thing {{text: $entity_text}}) MERGE (u)-[:HAS {{created_at: $timestamp}}]->(e)",
  "parameters": {{
    "user_id": "user123",
    "entity_text": "dog",
    "timestamp": "2024-01-01T00:00:00Z"
  }}
}}

USER_ID: {user_id}"""

    CONTEXT_RETRIEVAL_PROMPT = """You are a conversation context generator for a language learning app.

TASK: Convert the user's graph data into natural language context for conversation prompts.

USER GRAPH DATA:
{graph_data}

Generate a brief, natural context summary that can be used in conversation prompts. Focus on:
- 2-3 most interesting/relevant facts
- Information that can drive engaging conversation
- Keep it conversational and personal

Return JSON:
{{
  "context_summary": "brief natural language summary",
  "conversation_starters": ["suggestion 1", "suggestion 2"],
  "relevant_vocabulary": ["word1", "word2", "word3"]
}}

If no meaningful data, return empty strings and arrays."""

    # ============ CORE FUNCTIONS ============
    
    def analyze_conversation(self, user_id, conversation_messages):
        """Analyze conversation messages and extract user information"""
        try:
            # Format conversation for analysis
            formatted_messages = "\n".join([
                f"{msg.get('sender', 'unknown')}: {msg.get('content', '')}"
                for msg in conversation_messages
            ])
            
            prompt = self.CONVERSATION_ANALYSIS_PROMPT.format(
                user_id=user_id,
                conversation_messages=formatted_messages
            )
            
            # Get LLM analysis
            response = self.llm_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=5000
            )
            
            result = response.choices[0].message.content.strip()
            print("reult of parsing the form: ", result)
            # Parse JSON response
            try:
                parsed_result = json.loads(result)
                logging.info(f"Conversation analysis completed for user {user_id}: "
                           f"{len(parsed_result.get('entities', []))} entities, "
                           f"{len(parsed_result.get('relationships', []))} relationships")
                return parsed_result
            except json.JSONDecodeError:
                logging.error(f"Failed to parse LLM analysis response: {result}")
                return {"entities": [], "relationships": [], "reasoning": "Parse error"}
                
        except Exception as e:
            logging.error(f"Conversation analysis failed: {e}")
            return {"entities": [], "relationships": [], "reasoning": f"Error: {e}"}
    
    def generate_graph_cypher(self, user_id, extracted_info):
        """Generate Cypher queries from extracted information"""
        try:
            prompt = self.CYPHER_GENERATION_PROMPT.format(
                user_id=user_id,
                extracted_info=json.dumps(extracted_info, indent=2)
            )
            
            response = self.llm_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Neo4j Cypher expert. Generate safe, valid queries only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # No creativity needed for Cypher
                max_tokens=400
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                cypher_json = json.loads(result)
                logging.info(f"Generated Cypher for user {user_id}: {cypher_json.get('query', '')[:50]}...")
                return cypher_json
            except json.JSONDecodeError:
                logging.error(f"Failed to parse Cypher response: {result}")
                return None
                
        except Exception as e:
            logging.error(f"Cypher generation failed: {e}")
            return None
    
    def get_conversation_context(self, user_id):
        """Get user's graph context as natural language for conversation prompts"""
        try:
            # Get user's graph data
            query = """
            MATCH (u:User {id: $user_id})-[r]->(entity)
            RETURN type(r) as relationship, entity.text as entity, 
                   labels(entity)[0] as entity_type, r.created_at as created_at
            ORDER BY r.created_at DESC
            LIMIT 20
            """
            
            graph_data = GraphService.execute_cypher(query, {"user_id": user_id})
            
            if not graph_data:
                return {
                    "context_summary": "",
                    "conversation_starters": [],
                    "relevant_vocabulary": []
                }
            
            # Format for LLM
            formatted_data = []
            for item in graph_data:
                formatted_data.append(f"User {item['relationship']} {item['entity']} ({item['entity_type']})")
            
            prompt = self.CONTEXT_RETRIEVAL_PROMPT.format(
                graph_data="\n".join(formatted_data)
            )
            
            response = self.llm_service.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a conversation context expert for language learning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                context_json = json.loads(result)
                logging.info(f"Generated conversation context for user {user_id}")
                return context_json
            except json.JSONDecodeError:
                logging.error(f"Failed to parse context response: {result}")
                return {
                    "context_summary": "",
                    "conversation_starters": [],
                    "relevant_vocabulary": []
                }
                
        except Exception as e:
            logging.error(f"Context retrieval failed: {e}")
            return {
                "context_summary": "",
                "conversation_starters": [],
                "relevant_vocabulary": []
            }
    
    # ============ HIGH-LEVEL FUNCTIONS ============
    
    def process_conversation_for_graph(self, user_id, conversation_messages):
        """Complete pipeline: analyze conversation → generate Cypher → execute"""
        try:
            # Step 1: Analyze conversation
            extracted_info = self.analyze_conversation(user_id, conversation_messages)
            
            if not extracted_info.get('entities') and not extracted_info.get('relationships'):
                logging.info(f"No meaningful information extracted from conversation for user {user_id}")
                return {"success": True, "updates": 0, "reasoning": "No new information found"}
            
            # Step 2: Generate Cypher
            cypher_json = self.generate_graph_cypher(user_id, extracted_info)
            
            if not cypher_json:
                return {"success": False, "error": "Failed to generate Cypher"}
            
            # Step 3: Execute Cypher
            result = GraphService.execute_llm_cypher(cypher_json)
            
            return {
                "success": True,
                "updates": len(result),
                "extracted_entities": len(extracted_info.get('entities', [])),
                "extracted_relationships": len(extracted_info.get('relationships', [])),
                "reasoning": extracted_info.get('reasoning', ''),
                "cypher_executed": cypher_json.get('query', '')[:100] + "..."
            }
            
        except Exception as e:
            logging.error(f"Conversation processing failed for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user_graph_from_personalization(self, user_id, personalization_data):
        """Process personalization form data through LLM for graph updates"""
        try:
            # Convert form data to conversation-like format for analysis
            fake_conversation = []
            for field, value in personalization_data.items():
                if value and value.strip():
                    fake_conversation.append({
                        "sender": "user",
                        "content": f"My {field.replace('_', ' ')} is {value}"
                    })
            
            if not fake_conversation:
                return {"success": True, "updates": 0, "reasoning": "No personalization data to process"}
            
            # Process through standard pipeline
            return self.process_conversation_for_graph(user_id, fake_conversation)
            
        except Exception as e:
            logging.error(f"Personalization processing failed for user {user_id}: {e}")
            return {"success": False, "error": str(e)}