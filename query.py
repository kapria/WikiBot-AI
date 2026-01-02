import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import sys

# Configuration
DB_PATH = "./chroma_db"
COLLECTION_NAME = "wiki_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Llama Server Configuration (LM Studio defaults to port 1234)
LLAME_SERVER_URL = "http://localhost:1234/v1"
API_KEY = "lm-studio" # LM Studio often requires a non-empty string, though it doesn't validate it

def main():
    # 1. Initialize Vector Store
    print("Loading Vector Store...")
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"Error loading collection: {e}")
        print("Did you run ingest.py first?")
        return

    # 2. Initialize Embedding Model
    print("Loading Embedding Model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # 3. Initialize OpenAI Client (for Llama Server)
    llm_client = OpenAI(
        base_url=LLAME_SERVER_URL,
        api_key=API_KEY
    )

    print("\n--- Local Wiki RAG (Type 'quit' to exit) ---")
    
    while True:
        query = input("\nQuery: ")
        if query.lower() in ['quit', 'exit']:
            break

        # Generate embedding for query
        query_emb = model.encode([query]).tolist()

        # Retrieve Documents
        results = collection.query(
            query_embeddings=query_emb,
            n_results=3  # Get top 3 chunks
        )

        documents = results['documents'][0]
        
        if not documents:
            print("No relevant info found.")
            continue

        context_text = "\n\n".join(documents)
        print(f"\n[Found {len(documents)} context chunks]")

        # Prepare Prompt
        system_prompt = "You are a helpful assistant. Use the provided Context to answer the user's question. If you don't know the answer based on the context, say so."
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}"

        # Call Llama Server
        try:
            print("Generating answer...", end="", flush=True)
            stream = llm_client.chat.completions.create(
                model="qwen-users-model", # Model name usually ignored by single-model llama-server
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
                temperature=0.7
            )

            print("\n")
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    print(chunk.choices[0].delta.content, end="")
            print("\n")
            
        except Exception as e:
            print(f"\nError connecting to Llama Server: {e}")
            print("Ensure server is running: ./llama-server -m your_model.gguf -c 2048 --port 8080")

if __name__ == "__main__":
    main()
