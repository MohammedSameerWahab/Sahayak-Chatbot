import os
# Add 'send_from_directory' to this import line
from flask import request, jsonify, render_template, send_from_directory
from sqlalchemy import create_engine, text
from app import app
from app.rag_core import get_rag_response

# Get the absolute path to the project's root directory
# This is more robust than relative paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
NOTES_DIR = os.path.join(ROOT_DIR, 'notes')


DB_URL = os.getenv("DATABASE_URL")
try:
    engine = create_engine(DB_URL)
except Exception as e:
    engine = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    # ... (This function remains unchanged) ...
    if not engine:
        return jsonify({"error": "Database connection not available"}), 500
    data = {}
    with engine.connect() as connection:
        query = text("""
            SELECT s.name AS subject_name, d.id AS doc_id, d.name AS doc_name
            FROM subjects s JOIN documents d ON s.id = d.subject_id
            WHERE d.status = 'processed' ORDER BY s.name, d.name;
        """)
        result = connection.execute(query)
        for row in result:
            subject_name = row.subject_name
            if subject_name not in data:
                data[subject_name] = []
            data[subject_name].append({"id": row.doc_id, "name": row.doc_name})
    return jsonify(data)


@app.route('/api/chat', methods=['POST'])
def chat():
    # ... (This function remains unchanged) ...
    data = request.get_json()
    if not data or 'subject_name' not in data or 'query' not in data:
        return jsonify({"error": "Missing 'subject_name' or 'query' in request"}), 400
    subject_name = data['subject_name']
    query = data['query']
    response = get_rag_response(subject_name, query)
    return jsonify({"answer": response})

# --- NEW ROUTE TO SERVE FILES ---
@app.route('/notes/<subject>/<filename>')
def serve_note(subject, filename):
    """
    Securely serves files from the notes directory.
    """
    # Use send_from_directory for security (prevents directory traversal attacks)
    return send_from_directory(os.path.join(NOTES_DIR, subject), filename)