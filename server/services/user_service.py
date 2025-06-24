import json
import os
from datetime import datetime
from pathlib import Path

class UserService:
    def __init__(self):
        self.users_storage = {}
        self.user_states = {}
        # Add disk storage path
        self.storage_path = Path("data/users")
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _save_user_to_disk(self, user_id: str, user_data: Dict):
        """Save user data to disk"""
        file_path = self.storage_path / f"{user_id}.json"
        user_copy = user_data.copy()
        user_copy['last_updated'] = datetime.now().isoformat()
        
        with open(file_path, 'w') as f:
            json.dump(user_copy, f, indent=2)
    # After storing in memory
        self.users_storage[user_id] = user_data
        self._save_user_to_disk(user_id, user_data)  # ADD THIS LINE