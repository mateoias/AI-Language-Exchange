import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("FLASK_SECRET_KEY must be set in .env file")
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in .env file")
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # File storage configuration (MVP)
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    USERS_FILE = os.path.join(DATA_DIR, 'users.json')
    
    # OpenAI configuration (for future chat functionality)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Azure configuration (for future deployment)
    AZURE_API_KEY = os.environ.get('AZURE_API_KEY')
    AZURE_ENDPOINT = os.environ.get('AZURE_ENDPOINT')
    AZURE_SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
    AZURE_SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION')
    
    # Neo4j configuration (for future graph database)
    NEO4J_URI = os.environ.get('NEO4J_URI')
    NEO4J_USERNAME = os.environ.get('NEO4J_USERNAME')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # In production, all secrets should be set
    @classmethod
    def validate_production_config(cls):
        required_vars = [
            'FLASK_SECRET_KEY',
            'JWT_SECRET_KEY',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Use in-memory or temporary files for testing
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}