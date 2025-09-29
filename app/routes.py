import os
# Add 'render_template' to this import line
from flask import request, jsonify, render_template
from sqlalchemy import create_engine, text
from app import app  # Import the app instance from __init__.py
from app.rag_core import get_rag_response

# --- DATABASE CONNECTION ---
DB_URL = os.getenv("DATABASE_URL")
try:
    engine = create_engine(DB_URL)
    print("✅ Database engine created for routes.")
except Exception as e:
    print(f"❌ Error creating database engine for routes: {e}")
    engine = None

# --- ADD THIS NEW ROUTE FOR THE HOMEPAGE ---
@app.route('/')
def index():
    """
    Serves the main HTML page of the chatbot.
    """
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
            FROM subjects s
            JOIN documents d ON s.id = d.subject_id
            WHERE d.status = 'processed'
            ORDER BY s.name, d.name;
        """)
        result = connection.execute(query)

        for row in result:
            subject_name = row.subject_name
            if subject_name not in data:
                data[subject_name] = []
            
            data[subject_name].append({
                "id": row.doc_id,
                "name": row.doc_name
            })
            
    return jsonify(data)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint to handle incoming chat messages.
    It expects a JSON payload with 'doc_id' and 'query'.
    """
    data = request.get_json()
    if not data or 'doc_id' not in data or 'query' not in data:
        return jsonify({"error": "Missing 'doc_id' or 'query' in request"}), 400

    doc_id = data['doc_id']
    query = data['query']
    
    response = get_rag_response(doc_id, query)
    
    return jsonify({"answer": response})