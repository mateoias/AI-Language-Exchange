# services/prompt_loader.py
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Lock
from flask import current_app

logger = logging.getLogger(__name__)

class PromptFileHandler(FileSystemEventHandler):
    """Handle file changes in the prompts directory"""
    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader
        
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.yaml') or event.src_path.endswith('.yml'):
            logger.info(f"Prompt file modified: {event.src_path}")
            self.prompt_loader.reload_prompts()

class PromptLoader:
    """
    Loads and manages prompts from YAML files with hot-reload capability
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PromptLoader, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.prompts_dir = None
        self.prompts_cache = {}
        self.base_template = None
        self.observer = None
        self._cache_lock = Lock()
        self._initialized = True
    
    def initialize(self, app=None):
        """Initialize with Flask app context"""
        if app:
            prompts_dir = app.config.get('PROMPTS_DIR', 
                                        os.path.join(app.root_path, 'prompts'))
        else:
            prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
            
        self.prompts_dir = Path(prompts_dir)
        
        # Create directory structure if it doesn't exist
        self._ensure_directory_structure()
        
        # Load all prompts
        self.reload_prompts()
        
        # Start file watcher
        self._start_file_watcher()
    
    def _ensure_directory_structure(self):
        """Create the prompts directory structure if it doesn't exist"""
        (self.prompts_dir / 'levels').mkdir(parents=True, exist_ok=True)
        (self.prompts_dir / 'reminders').mkdir(parents=True, exist_ok=True)
    
    def _start_file_watcher(self):
        """Start watching for file changes"""
        if self.observer:
            self.observer.stop()
            
        self.observer = Observer()
        event_handler = PromptFileHandler(self)
        self.observer.schedule(event_handler, str(self.prompts_dir), recursive=True)
        self.observer.start()
        logger.info(f"Started watching prompts directory: {self.prompts_dir}")
    
    def reload_prompts(self):
        """Reload all prompts from disk"""
        with self._cache_lock:
            try:
                # Load base template
                base_template_path = self.prompts_dir / 'base_template.yaml'
                if base_template_path.exists():
                    with open(base_template_path, 'r', encoding='utf-8') as f:
                        base_data = yaml.safe_load(f)
                        self.base_template = base_data.get('template', '')
                
                # Clear cache
                self.prompts_cache = {
                    'levels': {},
                    'reminders': {}
                }
                
                # Load level prompts
                levels_dir = self.prompts_dir / 'levels'
                for level_file in levels_dir.glob('*.yaml'):
                    level_name = level_file.stem
                    try:
                        with open(level_file, 'r', encoding='utf-8') as f:
                            self.prompts_cache['levels'][level_name] = yaml.safe_load(f)
                        logger.info(f"Loaded level prompt: {level_name}")
                    except Exception as e:
                        logger.error(f"Error loading level {level_name}: {e}")
                
                # Load reminders
                reminders_dir = self.prompts_dir / 'reminders'
                for reminder_file in reminders_dir.glob('*.yaml'):
                    reminder_name = reminder_file.stem
                    try:
                        with open(reminder_file, 'r', encoding='utf-8') as f:
                            self.prompts_cache['reminders'][reminder_name] = yaml.safe_load(f)
                        logger.info(f"Loaded reminder: {reminder_name}")
                    except Exception as e:
                        logger.error(f"Error loading reminder {reminder_name}: {e}")
                        
                logger.info("Successfully reloaded all prompts")
                
            except Exception as e:
                logger.error(f"Error reloading prompts: {e}")
    
    def get_level_prompt(self, level: str) -> Optional[Dict[str, Any]]:
        """Get prompt configuration for a specific level"""
        with self._cache_lock:
            return self.prompts_cache.get('levels', {}).get(level)
    
    def get_reminder(self, reminder_id: str = 'default') -> str:
        """Get a specific reminder text"""
        with self._cache_lock:
            reminder_data = self.prompts_cache.get('reminders', {}).get(reminder_id, {})
            return reminder_data.get('reminder_text', '')
    
    def get_base_template(self) -> str:
        """Get the base template"""
        with self._cache_lock:
            return self.base_template or ''
    
    def stop(self):
        """Stop the file watcher"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

# Create global instance
prompt_loader = PromptLoader()