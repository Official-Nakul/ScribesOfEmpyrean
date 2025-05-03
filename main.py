from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveJsonSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Empyrean Series QA API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# Initialize embeddings and LLM model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
model = ChatGroq(model='llama-3.3-70b-versatile', temperature=0.5)

# In-memory chat history storage
chat_history_store = {}

# Define request model
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None  # Optional session ID for tracking chat history

# Define response model
class QueryResponse(BaseModel):
    answer: str
    context_used: Optional[List[str]] = None  # Optional field to return the context used
    session_id: str  # Return the session ID for the client to use in subsequent requests

def load_json_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def build_vector_store(json_file_path, vector_dir="./empyrean_vectors"):
    json_data = load_json_data(json_file_path)
    json_splitter = RecursiveJsonSplitter()
    chunks = json_splitter.split_json(json_data)
    docs = [Document(page_content=str(chunk)) for chunk in chunks]
    vector_store = Chroma.from_documents(docs, embeddings, persist_directory=vector_dir)
    return vector_store

def get_top_n(query, vector_dir="./empyrean_vectors", json_file_path="./empyrean_characters_processed.json", n=3):
    if not os.path.exists(vector_dir):
        vector_store = build_vector_store(json_file_path, vector_dir)
    else:
        vector_store = Chroma(persist_directory=vector_dir, embedding_function=embeddings)
    return vector_store.similarity_search(query, k=n)

def get_response(query, session_id):
    # Retrieve or initialize chat history for the session
    if session_id not in chat_history_store:
        chat_history_store[session_id] = []
    chat_history = chat_history_store[session_id]

    # Get relevant context from vector store
    context_docs = get_top_n(query)
    context_text = "\n".join([doc.page_content for doc in context_docs])

    # Format chat history for the prompt
    history_text = "\n".join([f"User: {entry['query']}\nAssistant: {entry['answer']}" for entry in chat_history])

    # Define the prompt template with chat history
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an expert on The Empyrean Series.
             Answer the question based on the provided context and chat history.
             Provide a detailed answer with specific references to characters and events when possible.
             If you don't know the answer, say you don't know, don't make up an answer."""),
        ("human", """Chat History:
        {history}

        Context for this question: {context}

        Question: {query}""")
    ])

    # Format the prompt with history, context, and query
    formatted_prompt = prompt_template.format_messages(history=history_text, context=context_text, query=query)
    response = model.invoke(formatted_prompt)

    # Store the new interaction in chat history
    chat_history_store[session_id].append({"query": query, "answer": response.content})

    # Limit chat history to prevent excessive memory usage (e.g., last 10 interactions)
    if len(chat_history_store[session_id]) > 10:
        chat_history_store[session_id] = chat_history_store[session_id][-10:]

    return {
        "answer": response.content,
        "context_used": [doc.page_content for doc in context_docs],
        "session_id": session_id
    }

# Create the chat endpoint
@app.post("/api/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Generate a new session ID if none provided
        session_id = request.session_id or str(uuid.uuid4())

        result = get_response(request.query, session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

# Root path for simple health check
@app.get("/")
async def root():
    return {"status": "ok", "message": "Empyrean Series QA API is running"}

# Startup event to ensure vector store exists
@app.on_event("startup")
async def startup_event():
    # Check if vector store exists and create it if not
    if not os.path.exists("./empyrean_vectors"):
        try:
            print("Initializing vector store...")
            build_vector_store("./empyrean_characters_processed.json")
            print("Vector store initialized successfully!")
        except Exception as e:
            print(f"Failed to initialize vector store: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Fallback to 8000 for local dev
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")