# 📚 WikiBot AI: Professional Wikipedia RAG Assistant

WikiBot AI is a sophisticated **Retrieval-Augmented Generation (RAG)** system that allows users to chat with Wikipedia content through a premium, modern web interface. It combines the power of vector databases with local LLMs (Large Language Models) to provide accurate, context-aware answers.

![UI Design](https://img.shields.io/badge/Design-Glassmorphism-blueviolet)
![Tech](https://img.shields.io/badge/Tech-FastAPI%20%7C%20ChromaDB%20%7C%20OpenAI%20API-6366f1)

## ✨ Key Features

*   **🔍 Advanced RAG**: Intelligent retrieval from the Wikipedia database using ChromaDB and Sentence Transformers.
*   **🧠 Context-Aware Chat**: Remembers previous interactions for seamless multi-turn conversations.
*   **🛑 Real-time Control**: Stop generation mid-stream with a dedicated abort button.
*   **🖼️ Premium UI**: State-of-the-art glassmorphism design with responsive layouts and micro-animations.
*   **🖨️ Professional Print**: Export formatted chat histories directly to PDF or paper.
*   **⚡ Streaming Responses**: Watch the bot think and type in real-time.

## 🛠️ Technology Stack

-   **Backend**: Python, FastAPI, Uvicorn
-   **Vector Database**: ChromaDB
-   **Embeddings**: `all-MiniLM-L6-v2` (Sentence-Transformers)
-   **LLM Connection**: OpenAI-compatible API (designed for LM Studio/Llama.cpp)
-   **Frontend**: Vanilla HTML5, CSS3 (Glassmorphism), Modern JavaScript (ES6+)

## 🚀 Getting Started

### 1. Prerequisites
-   Python 3.9+
-   LM Studio or a local LLM server running at `http://localhost:1234`

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/wikipediarag.git
cd wikipediarag

# Install dependencies
pip install -r requirements.txt
```

### 3. Ingesting Knowledge
To populate the vector database with Wikipedia articles:
1.  Place your `simplewiki-latest-pages-articles.xml.bz2` in the root folder.
2.  Run the ingestion script:
```bash
python ingest.py
```

### 4. Running the Application
```bash
python server.py
```
Open your browser and navigate to `http://localhost:8000`.

## 📁 Project Structure

```text
├── static/
│   ├── index.html    # semantic UI structure
│   ├── index.css     # Premium glassmorphism styles
│   └── script.js    # Logic for streaming & history
├── ingest.py         # Wikipedia XML processor & embedder
├── query.py          # CLI testing tool for queries
├── server.py         # FastAPI backend with streaming
└── requirements.txt  # Python dependencies
```

## 📜 Documentation

### API Endpoints
-   `GET /`: Serves the frontend application.
-   `POST /chat`: Accepts `{query: string, history: Array}` and returns a text stream.

### Frontend Features
-   **Stop Button**: Uses `AbortController` to terminate server requests safely.
-   **Print Utility**: Uses `@media print` queries to strip UI elements and format text for documentation.
-   **History Management**: Local state tracking to ensure the LLM understands pronouns and follow-up context.

## 🤝 Contributing
Contributions are welcome! Pull requests, bug reports, and feature suggestions help make WikiBot AI better.

## 📄 License
MIT License - feel free to use this project for your own learning or internal tools!
