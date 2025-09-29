import os
import hashlib
from dotenv import load_dotenv

# Database imports
from sqlalchemy import create_engine, text

# LangChain imports for document processing
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
NOTES_DIR = "notes"
VECTOR_STORE_DIR = "vector_store"
DB_URL = os.getenv("DATABASE_URL")
# Use a pre-trained, lightweight embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- DATABASE SETUP ---
try:
    engine = create_engine(DB_URL)
    with engine.connect() as connection:
        print("✅ Successfully connected to PostgreSQL database.")
        
        # Create subjects table if it doesn't exist
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL
            );
        """))

        # Create documents table if it doesn't exist
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                subject_id INTEGER REFERENCES subjects(id),
                status VARCHAR(50) DEFAULT 'pending'
            );
        """))
        # Commit the changes to create tables
        connection.commit()
        print("🔑 Tables 'subjects' and 'documents' are ready.")

except Exception as e:
    print(f"❌ Error connecting to the database: {e}")
    exit()


# --- CORE PROCESSING LOGIC ---
def process_file(filepath, doc_id, subject_id, connection):
    """Loads, chunks, embeds, and stores a single file in ChromaDB."""
    
    print(f"\nProcessing file: {os.path.basename(filepath)}...")

    try:
        # 1. Load the document based on its extension
        if filepath.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
        elif filepath.endswith(".pptx"):
            # Using UnstructuredPowerPointLoader as it's quite effective
            loader = UnstructuredPowerPointLoader(filepath)
        else:
            print(f"Unsupported file type: {filepath}. Skipping.")
            return

        documents = loader.load()

        # 2. Split the document into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)
        print(f"📄 Split into {len(chunks)} chunks.")

        # 3. Initialize the embedding model
        print(f"🧠 Loading embedding model '{EMBEDDING_MODEL}'...")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # 4. Create and persist the ChromaDB vector store
        # The collection will be named after the unique document ID
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTOR_STORE_DIR,
            collection_name=doc_id 
        )
        print(f"💾 Vector store created for doc_id: '{doc_id}'")

        # 5. Update the document status in PostgreSQL to 'processed'
        connection.execute(
            text("UPDATE documents SET status = 'processed' WHERE id = :id"),
            {"id": doc_id}
        )
        connection.commit()
        print("✅ Status updated to 'processed' in the database.")

    except Exception as e:
        print(f"❌ An error occurred while processing {filepath}: {e}")
        # Update status to 'failed'
        connection.execute(
            text("UPDATE documents SET status = 'failed' WHERE id = :id"),
            {"id": doc_id}
        )
        connection.commit()


# --- MAIN EXECUTION ---
def main():
    """Main function to scan directories and process all notes."""
    print("🚀 Starting the note processing script...")
    
    with engine.connect() as connection:
        # Iterate over each subject directory in the notes folder
        for subject_name in os.listdir(NOTES_DIR):
            subject_path = os.path.join(NOTES_DIR, subject_name)
            if os.path.isdir(subject_path):
                
                # Get or create subject_id from the database
                res = connection.execute(text("SELECT id FROM subjects WHERE name = :name"), {"name": subject_name}).scalar_one_or_none()
                if res:
                    subject_id = res
                else:
                    result = connection.execute(text("INSERT INTO subjects (name) VALUES (:name) RETURNING id"), {"name": subject_name})
                    subject_id = result.scalar_one()
                    connection.commit()
                
                print(f"\n--- Found Subject: {subject_name} (ID: {subject_id}) ---")

                # Iterate over each file in the subject directory
                for filename in os.listdir(subject_path):
                    filepath = os.path.join(subject_path, filename)
                    
                    # Generate a unique and deterministic ID for the document
                    # Using a hash of the path ensures it's unique and repeatable
                    doc_id = hashlib.sha256(filepath.encode()).hexdigest()

                    # Check if this document has already been processed successfully
                    status = connection.execute(text("SELECT status FROM documents WHERE id = :id"), {"id": doc_id}).scalar_one_or_none()
                    
                    if status == 'processed':
                        print(f"✅ '{filename}' already processed. Skipping.")
                        continue
                    elif not status:
                        # New file, insert its metadata into the database
                        connection.execute(
                            text("INSERT INTO documents (id, name, subject_id) VALUES (:id, :name, :subject_id)"),
                            {"id": doc_id, "name": filename, "subject_id": subject_id}
                        )
                        connection.commit()
                    
                    # Process the file
                    process_file(filepath, doc_id, subject_id, connection)

    print("\n🎉 All notes have been processed!")


if __name__ == "__main__":
    main()