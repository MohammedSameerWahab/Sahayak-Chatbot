# Sahayak: The Interactive Academic Chatbot 🤖

Sahayak is a full-stack RAG (Retrieval-Augmented Generation) web application that transforms static university course notes into a dynamic and interactive learning tool. Students can select a subject, view their course materials (PDFs) directly in the app, and ask questions in a conversational chat interface to get instant, context-aware answers.

**(Add a screenshot or GIF of the application in action here\!)**

-----

## 🚀 Key Features

  * **Subject-wise RAG:** Chat with an entire subject's knowledge base. Sahayak combines all notes from a subject (both PDFs and PPTXs) into a single vector store for comprehensive, cross-document answers.
  * **Split-Screen Interface:** A modern UI that displays the source PDF document on the left and the chat interface on the right, allowing students to reference their notes while asking questions.
  * **Interactive PDF Viewer:** A built-in PDF viewer powered by PDF.js, complete with pagination controls (Previous/Next) for easy document navigation.
  * **Collapsible Navigation:** A sleek, responsive sidebar to browse subjects and files. It's fully collapsible (with a dedicated open/close button) to maximize screen real-estate.
  * **Versatile Document Ingestion:** Uses the `unstructured` library to intelligently parse both `.pdf` and `.pptx` files, ensuring accurate text extraction from complex layouts.
  * **Scalable Backend:** Built with a robust Flask backend, using PostgreSQL to manage document and subject metadata, and ChromaDB for efficient vector storage.

-----

## 🛠️ Tech Stack

| Area | Technology |
| :--- | :--- |
| **Backend** | Python, Flask, SQLAlchemy |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+) |
| **AI & RAG** | LangChain, Google Gemini (LLM), Hugging Face (Embeddings) |
| **Databases** | PostgreSQL (Metadata), ChromaDB (Vector Store) |
| **Document Parsing** | `unstructured` (for PDF & PPTX) |
| **PDF Viewing** | PDF.js |

-----

## 🏛️ System Architecture

The application operates in two main phases:

1.  **Data Ingestion (Offline Script)**

      * A faculty member (or admin) places notes (`.pdf`, `.pptx`) into the `notes/` directory, organized by subject.
      * The `process_notes.py` script is run.
      * **Parsing:** `unstructured` reads the content of each file.
      * **Chunking:** `LangChain` splits the text into smaller, overlapping chunks.
      * **Storage:**
          * **PostgreSQL:** The file's metadata (e.g., `OS-Basics.pptx`, subject: `Operating_Systems`) is saved in a SQL database.
          * **ChromaDB:** The text chunks are vectorized using a Hugging Face model and stored in a subject-specific collection (e.g., a collection named `Operating_Systems` contains vectors from all its files).

2.  **Application (Live Server)**

      * **Frontend (JS)** loads and calls the backend `/api/subjects` endpoint.
      * **Backend (Flask)** queries the PostgreSQL DB to build the sidebar navigation.
      * When a user clicks a file:
          * If it's a PDF, the frontend calls the `/notes/<subject>/<file>` endpoint. The Flask backend securely serves the PDF file, which is then rendered by PDF.js in the viewer.
          * The chat interface is activated for that file's subject.
      * When a user sends a message:
          * The frontend sends the query and `subject_name` to the `/api/chat` endpoint.
          * The **Flask** backend performs a RAG query:
            1.  Retrieves relevant text chunks from that subject's ChromaDB collection.
            2.  Builds a prompt with the context and the user's query.
            3.  Sends the prompt to the **Google Gemini LLM** via LangChain.
            4.  Receives the *full response* and returns it as a single JSON object.
          * The **JavaScript** frontend displays a "Thinking..." message, then updates the chat bubble with the final answer once it's received.

-----

## ⚙️ Getting Started

Follow these steps to get Sahayak running on your local machine.

### 1\. Prerequisites

  * Python 3.9+
  * PostgreSQL
  * Git

### 2\. Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/MohammedSameerWahab/sahayak-chatbot.git
    cd sahayak-chatbot
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # For macOS/Linux
    python3 -m venv myvenv
    source myvenv/bin/activate

    # For Windows
    python -m venv myvenv
    myvenv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the PostgreSQL Database:**

      * Start your PostgreSQL server.
      * Create a new database (e.g., `sahayak_db`).

    <!-- end list -->

    ```sql
    CREATE DATABASE sahayak_db;
    ```

5.  **Configure Environment Variables:**

      * Create a `.env` file in the root of the project.
      * Add your database URL and Google API key.

    <!-- end list -->

    ```.env
    # .env
    DATABASE_URL="postgresql://YOUR_POSTGRES_USER:YOUR_PASSWORD@localhost:5432/sahayak_db"
    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
    ```

### 3\. Running the Application

1.  **Add Your Notes:**

      * Place your course files inside the `notes/` directory. Create a new folder for each subject.
      * Example structure:
        ```
        notes/
        ├── Computer_Networks/
        │   ├── module1.pdf
        │   └── module2.pdf
        └── Operating_Systems/
            └── os_basics.pdf
        ```

2.  **Run the Ingestion Script:**

      * This only needs to be done once, or whenever you add new files.
      * **Important:** Before your first run, make sure to delete the `vector_store/` directory if it exists, and clear your database tables:
        ```sql
        -- Connect to sahayak_db in psql
        \c sahayak_db
        -- Truncate tables to ensure a fresh start
        TRUNCATE TABLE documents, subjects RESTART IDENTITY;
        ```
      * Now, run the script:
        ```bash
        python process_notes.py
        ```
      * This will parse your files, populate PostgreSQL, and create the ChromaDB vector stores.

3.  **Start the Flask Server:**

    ```bash
    python run.py
    ```

4.  **Open Sahayak\!**

      * Open your browser and navigate to **`http://127.0.0.1:5000`**.

-----

## 🔮 Future Work

  * **Live PPTX Viewing:** Implement a backend conversion step (e.g., using `unoconv` or a similar tool) to convert `.pptx` files to PDF on the fly, allowing them to be rendered in the PDF.js viewer.
  * **Dynamic File Management:** Build a secure admin/faculty portal for uploading, deleting, and re-indexing notes directly from the web interface, removing the need for manual script execution.
  * **Chat History:** Store conversation history in the database so users can continue their chats later.

-----

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
