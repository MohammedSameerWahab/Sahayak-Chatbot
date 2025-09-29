import os
import hashlib
from dotenv import load_dotenv

# Database imports
from sqlalchemy import create_engine, text

# LangChain imports for document processing
# IMPORT THE NEW LOADER HERE
from langchain_community.document_loaders import UnstructuredPowerPointLoader, UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
NOTES_DIR = "notes"
VECTOR_STORE_DIR = "vector_store"
DB_URL = os.getenv("DATABASE_URL")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- DATABASE SETUP ---
try:
    engine = create_engine(DB_URL)
    with engine.connect() as connection:
        print("✅ Successfully connected to PostgreSQL database.")
        
        # Create tables if they don't exist
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            );
        """))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                subject_id INTEGER REFERENCES subjects(id),
                status VARCHAR(50) DEFAULT 'pending'
            );
        """))
        connection.commit()
        print("🔑 Tables 'subjects' and 'documents' are ready.")

except Exception as e:
    print(f"❌ Error connecting to the database: {e}")
    exit()


# --- MAIN EXECUTION ---
def main():
    """Main function to scan directories and process all notes."""
    print("🚀 Starting the note processing script...")
    
    print(f"🧠 Loading embedding model '{EMBEDDING_MODEL}'...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    with engine.connect() as connection:
        for subject_name in os.listdir(NOTES_DIR):
            subject_path = os.path.join(NOTES_DIR, subject_name)
            if not os.path.isdir(subject_path):
                continue

            print(f"\n--- Processing Subject: {subject_name} ---")
            
            vector_store = Chroma(
                collection_name=subject_name,
                embedding_function=embeddings,
                persist_directory=VECTOR_STORE_DIR
            )

            res = connection.execute(text("SELECT id FROM subjects WHERE name = :name"), {"name": subject_name}).scalar_one_or_none()
            subject_id = res or connection.execute(text("INSERT INTO subjects (name) VALUES (:name) RETURNING id"), {"name": subject_name}).scalar_one()
            connection.commit()

            for filename in os.listdir(subject_path):
                filepath = os.path.join(subject_path, filename)
                doc_id = hashlib.sha256(filepath.encode()).hexdigest()

                status = connection.execute(text("SELECT status FROM documents WHERE id = :id"), {"id": doc_id}).scalar_one_or_none()
                if status == 'processed':
                    print(f"✅ '{filename}' already processed. Skipping.")
                    continue
                
                try:
                    print(f"  -> Processing file: {filename}...")
                    
                    # --- THIS IS THE KEY CHANGE ---
                    # Use UnstructuredPDFLoader for PDFs
                    if filepath.endswith(".pdf"):
                        loader = UnstructuredPDFLoader(filepath)
                    elif filepath.endswith(".pptx"):
                        loader = UnstructuredPowerPointLoader(filepath)
                    else:
                        print(f"     Unsupported file type: {filename}. Skipping.")
                        continue
                    # --------------------------------

                    documents = loader.load()
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    chunks = text_splitter.split_documents(documents)
                    print(f"     📄 Split into {len(chunks)} chunks.")

                    if chunks:
                        vector_store.add_documents(documents=chunks)
                        print(f"     💾 Added chunks to '{subject_name}' collection. Persistence is automatic.")
                    
                    if not status:
                        connection.execute(
                            text("INSERT INTO documents (id, name, subject_id, status) VALUES (:id, :name, :subject_id, 'processed')"),
                            {"id": doc_id, "name": filename, "subject_id": subject_id}
                        )
                    else:
                         connection.execute(text("UPDATE documents SET status = 'processed' WHERE id = :id"), {"id": doc_id})
                    connection.commit()

                except Exception as e:
                    print(f"     ❌ Error processing {filename}: {e}")
                    if not status:
                        connection.execute(
                            text("INSERT INTO documents (id, name, subject_id, status) VALUES (:id, :name, :subject_id, 'failed')"),
                            {"id": doc_id, "name": filename, "subject_id": subject_id}
                        )
                    else:
                        connection.execute(text("UPDATE documents SET status = 'failed' WHERE id = :id"),{"id": doc_id})
                    connection.commit()
    
    print("\n🎉 All notes have been processed!")


if __name__ == "__main__":
    main()