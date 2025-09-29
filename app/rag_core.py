import os
from dotenv import load_dotenv

# RAG-specific imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
VECTOR_STORE_DIR = "vector_store"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-2.5-flash"

# --- INITIALIZE MODELS ---
try:
    # Initialize the LLM (Gemini)
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0,
                             convert_system_message_to_human=True)

    # Initialize the embedding model
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("✅ Models initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing models: {e}")
    llm = None
    embeddings = None

# --- RAG CHAIN LOGIC ---
def get_rag_response(doc_id: str, query: str) -> str:
    """
    Finds the relevant ChromaDB collection, retrieves context, and generates a response.
    """
    if not llm or not embeddings:
        return "Models are not available. Please check the server logs."

    try:
        # 1. Load the specific vector store collection for the given document ID
        vector_store = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=embeddings,
            collection_name=doc_id
        )
        retriever = vector_store.as_retriever(search_kwargs={'k': 3}) # Retrieve top 3 chunks

        # 2. Define the prompt template
        template = """
        You are 'Sahayak', a helpful academic assistant.
        Answer the following question based only on the context provided.
        If the answer is not in the context, say 'The answer is not available in these notes.'

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        prompt = PromptTemplate.from_template(template)

        # 3. Create the RAG chain using LangChain Expression Language (LCEL)
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        # 4. Invoke the chain with the user's query and return the response
        response = rag_chain.invoke(query)
        return response

    except Exception as e:
        print(f"❌ Error during RAG chain execution for doc_id '{doc_id}': {e}")
        return "An error occurred while processing your request. Please check the server logs."