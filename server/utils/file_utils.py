import json
import os
from threading import Lock
from flask import current_app

# File lock to handle concurrent access
file_lock = Lock()

def load_users():
    """Load users from JSON file"""
    users_file = current_app.config['USERS_FILE']
    
    if not os.path.exists(users_file):
        return {}
    
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users_data):
    """Save users to JSON file with thread safety"""
    users_file = current_app.config['USERS_FILE']
    
    with file_lock:
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False

def find_user_by_email(email):
    """Find a user by email address"""
    users_data = load_users()
    for user_id, user_data in users_data.items():
        if user_data.get('email') == email:
            return user_id, user_data
    return None, None

def find_user_by_id(user_id):
    """Find a user by ID"""
    users_data = load_users()
    return users_data.get(user_id)

def update_user(user_id, updated_data):
    """Update a user's data"""
    users_data = load_users()
    if user_id in users_data:
        users_data[user_id].update(updated_data)
        return save_users(users_data)
    return False

def delete_user(user_id):
    """Delete a user"""
    users_data = load_users()
    if user_id in users_data:
        del users_data[user_id]
        return save_users(users_data)
    return False