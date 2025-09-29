import os
from flask import request, jsonify, render_template
from sqlalchemy import create_engine, text
from app import app
from app.rag_core import get_rag_response

DB_URL = os.getenv("DATABASE_URL")
try:
    engine = create_engine(DB_URL)
except Exception as e:
    engine = None

@app.route('/')
def index():
    return render_template('index.html')
# ---------------------------------------------


# --- API ENDPOINTS ---

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    """
    Endpoint to get all subjects and their associated documents.
    This populates the navigation bar on the frontend.
    """
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
    data = request.get_json()
    # Expect 'subject_name' instead of 'doc_id'
    if not data or 'subject_name' not in data or 'query' not in data:
        return jsonify({"error": "Missing 'subject_name' or 'query' in request"}), 400

    subject_name = data['subject_name']
    query = data['query']
    
    # Pass subject_name to the RAG function
    response = get_rag_response(subject_name, query)
    
    return jsonify({"answer": response})