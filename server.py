import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# Configuration
DB_PATH = "./chroma_db"
COLLECTION_NAME = "wiki_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLAME_SERVER_URL = "http://localhost:1234/v1"
API_KEY = "lm-studio"

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class ChatRequest(BaseModel):
    query: str
    history: list = []  # List of dicts: {"role": "user"|"assistant", "content": "..."}

class RAGService:
    def __init__(self):
        print("Initializing RAG Service...")
        self.collection = None
        self.emb_model = None
        self.llm_client = None

        # 1. Initialize LLM Client
        try:
            self.llm_client = OpenAI(base_url=LLAME_SERVER_URL, api_key=API_KEY)
            print(f"Connected to LLM Server at {LLAME_SERVER_URL}")
        except Exception as e:
            print(f"FAILED to connect to LLM Server: {e}")

        # 2. Initialize Vector DB
        try:
            self.emb_model = SentenceTransformer(EMBEDDING_MODEL)
            self.chroma_client = chromadb.PersistentClient(path=DB_PATH)
            try:
                self.collection = self.chroma_client.get_collection(name=COLLECTION_NAME)
                print("Vector Database loaded successfully.")
            except Exception:
                print("Vector collection not found. Running in LLM-only mode.")
        except Exception as e:
            print(f"Vector Database Unavailable: {e}")

    def query(self, user_query: str, history: list = []):
        context_text = ""
        
        # 1. Try to Retrieve Context for the LATEST query
        if self.collection:
            try:
                query_emb = self.emb_model.encode([user_query]).tolist()
                results = self.collection.query(
                    query_embeddings=query_emb,
                    n_results=3
                )
                documents = results['documents'][0]
                if documents:
                    context_text = "\n\n".join(documents)
            except Exception as e:
                print(f"Retrieval failed: {e}")

        # 2. Construct Messages with History
        messages = []
        
        if context_text:
            system_prompt = "You are a professional Wikipedia assistant. Use the provided Context to answer the user's question. If the context doesn't contain the answer, use your general knowledge but mention it's not in the specific source. Maintain a helpful, conversational tone."
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "system", "content": f"Relevant Wikipedia Context:\n{context_text}"})
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant."})

        # Add existing conversation history
        for msg in history:
            role = "assistant" if msg["role"] == "bot" else "user"
            messages.append({"role": role, "content": msg["content"]})
        
        # Add the current user query
        messages.append({"role": "user", "content": user_query})

        # 3. Stream Response from LLM
        try:
            stream = self.llm_client.chat.completions.create(
                model="local-model",
                messages=messages,
                stream=True,
                temperature=0.7
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"Error calling LLM: {str(e)}"

# Global Service Instance
rag_service = None

@app.on_event("startup")
async def startup_event():
    global rag_service
    rag_service = RAGService()

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return StreamingResponse(rag_service.query(request.query, request.history), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
