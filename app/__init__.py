from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

# Import routes after the app is created to avoid circular imports
from app import routes