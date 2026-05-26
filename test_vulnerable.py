"""Sample file with intentional security vulnerabilities for testing."""

import os
import pickle
import yaml
import hashlib
from pathlib import Path

# Hardcoded secrets (vulnerability)
password = "super_secret_password123"
api_key = "sk-1234567890abcdef"
SECRET_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxx"

def get_user_data(user_id):
    """Fetch user data from database - SQL injection vulnerability."""
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # SQL Injection vulnerability - using string concatenation
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    
    return cursor.fetchone()


def process_command(user_input):
    """Process user command - command injection vulnerability."""
    # Command injection via os.system
    os.system("echo " + user_input)
    
    # Also dangerous: eval and exec
    eval(user_input)
    exec(user_input)


def load_config(config_path):
    """Load configuration file - path traversal vulnerability."""
    # Path traversal vulnerability
    full_path = "/etc/config/" + config_path
    with open(full_path, 'r') as f:
        return f.read()


def deserialize_data(data):
    """Deserialize data - insecure deserialization."""
    # Pickle is insecure - can execute arbitrary code
    return pickle.loads(data)


def load_yaml_config(yaml_string):
    """Load YAML configuration - unsafe YAML loading."""
    # yaml.load without safe Loader is vulnerable to RCE
    return yaml.load(yaml_string)


def hash_password(password):
    """Hash password - weak cryptography."""
    # MD5 and SHA1 are cryptographically weak
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    sha1_hash = hashlib.sha1(password.encode()).hexdigest()
    return md5_hash, sha1_hash


def fetch_external_data(url):
    """Fetch data from external URL - SSL verification disabled."""
    import requests
    
    # SSL verification disabled - vulnerable to MITM attacks
    response = requests.get(url, verify=False)
    return response.json()


class DebugApp:
    """Debug application with debug mode enabled."""
    
    def __init__(self):
        self.DEBUG = True
        self.debug = True
    
    def run(self):
        """Run the application with debug mode."""
        # Flask-style debug mode enabled
        print("Running in debug mode!")
        # Simulating app.run(debug=True)
        pass


if __name__ == "__main__":
    print("This file contains intentional security vulnerabilities for testing.")
    print("Use the /scan command to detect these issues.")
