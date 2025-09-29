import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# --- CONFIGURATION ---
VECTOR_STORE_DIR = "vector_store"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-2.5-flash"

# --- INITIALIZE MODELS ---
try:
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0,convert_system_message_to_human=True)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print("✅ Models initialized successfully.")
except Exception as e:
    print(f"❌ Error initializing models: {e}")
    llm = None
    embeddings = None

# --- RAG CHAIN LOGIC ---
# The function now accepts 'subject_name' instead of 'doc_id'
def get_rag_response(subject_name: str, query: str) -> str:
    if not llm or not embeddings:
        return "Models are not available. Please check the server logs."

    try:
        # Load the vector store collection for the given subject_name
        vector_store = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=embeddings,
            collection_name=subject_name # Use subject_name here
        )
        retriever = vector_store.as_retriever(search_kwargs={'k': 5}) # Retrieve more chunks for broader context

        template = """
        You are 'Sahayak', a helpful academic assistant.
        Answer the following question based only on the context provided from the subject notes.
        If the answer is not in the context, say 'The answer is not available in these notes.'

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
        prompt = PromptTemplate.from_template(template)

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        response = rag_chain.invoke(query)
        return response

    except Exception as e:
        print(f"❌ Error during RAG chain execution for subject '{subject_name}': {e}")
        return "An error occurred while processing your request. Please check the server logs."