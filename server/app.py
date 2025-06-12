from flask import Flask
from flask_cors import CORS
from .config import Config
from .database import db_connection
import atexit

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS for all routes - ESSENTIAL for production!
    CORS(app, origins=["http://localhost:5173"])  # Vite default port
    
    # Initialize database connection
    try:
        db_connection.connect()
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
    
    # Register cleanup function
    atexit.register(lambda: db_connection.close())
    
    # Register blueprints with URL prefixes
    from .routes.auth import auth_bp
    from .routes.user import user_bp  
    from .routes.chat import chat_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Language Exchange API is running'}
    
    return app