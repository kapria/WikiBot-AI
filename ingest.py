import bz2
import xml.sax
import bz2
import xml.sax
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os
import re

# Configuration
WIKI_FILE = "simplewiki-latest-pages-articles.xml.bz2"
DB_PATH = "./chroma_db"
COLLECTION_NAME = "wiki_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 100

class WikiHandler(xml.sax.ContentHandler):
    def __init__(self, collection, model):
        self.CurrentData = ""
        self.title = ""
        self.text = ""
        self.page_count = 0
        self.collection = collection
        self.model = model
        self.in_page = False
        self.in_title = False
        self.in_text = False

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "page":
            self.in_page = True
            self.title = ""
            self.text = ""
        elif tag == "title":
            self.in_title = True
        elif tag == "text":
            self.in_text = True

    def endElement(self, tag):
        if tag == "page":
            self.in_page = False
            self.process_page()
            self.page_count += 1
            if self.page_count % 100 == 0:
                print(f"Processed {self.page_count} pages...", end="\r")
        elif tag == "title":
            self.in_title = False
        elif tag == "text":
            self.in_text = False

    def characters(self, content):
        if self.in_title:
            self.title += content
        elif self.in_text:
            self.text += content

    def process_page(self):
        # Skip redirects or empty pages
        if "#REDIRECT" in self.text or not self.text.strip():
            return

        # Clean text (basic cleanup)
        clean_text = self.clean_wiki_text(self.text)
        
        # Chunk text
        chunks = self.chunk_text(clean_text)
        
        if not chunks:
            return

        # Embed and Add to ChromaDB
        # Note: For better performance, batching should be done outside this method, 
        # but for simplicity we process per page or small batches here.
        # Ideally, we collect a few pages of chunks then upsert.
        
        ids = [f"{self.page_count}_{i}" for i in range(len(chunks))]
        metadatas = [{"title": self.title, "chunk_id": i} for i in range(len(chunks))]
        
        embeddings = self.model.encode(chunks)
        
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )

    def clean_wiki_text(self, text):
        # Very basic wiki markup stripping
        # Remove {{...}}
        text = re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)
        # Remove [[File:...]]
        text = re.sub(r'\[\[File:.*?\]\]', '', text)
        # Remove [[...]] links, keeping only text
        text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove multiple newlines
        return re.sub(r'\n\s*\n', '\n\n', text).strip()

    def chunk_text(self, text):
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunk = text[i:i + CHUNK_SIZE]
            if len(chunk) > 50: # Filter very small chunks
                chunks.append(chunk)
        return chunks

def main():
    if not os.path.exists(WIKI_FILE):
        print(f"Error: File {WIKI_FILE} not found in current directory.")
        return

    print("Initializing Embedding Model...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    # Delete if exists to start fresh, or get_or_create
    try:
        client.delete_collection(COLLECTION_NAME)
    except:
        pass
    collection = client.create_collection(name=COLLECTION_NAME)

    print(f"Parsing and indexing {WIKI_FILE}...")
    handler = WikiHandler(collection, model)
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    # Use bz2 to read the compressed file directly
    with bz2.open(WIKI_FILE, 'rt', encoding='utf-8') as f:
        parser.parse(f)

    print(f"\nFinished! Processed {handler.page_count} pages.")

if __name__ == "__main__":
    main()
