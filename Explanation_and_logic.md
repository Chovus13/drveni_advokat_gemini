# Explanation and Logic for Drveni Advokat Project Files

This document provides a detailed explanation of each key file in the Drveni Advokat project, including what the file does, its inputs and outputs, and how it fits into the overall workflow pipeline. The project is a RAG (Retrieval-Augmented Generation) system for legal documents, using tools like Ollama for LLM inference, Qdrant for vector storage, and Streamlit for the UI.

## Overall Workflow Pipeline
1. **Corpus Conversion (convert_corpus.py)**: Convert legacy .doc files to .docx format.
2. **Text Extraction and Structuring (extract_and_structure.py)**: Extract and clean text from .docx files, structure into JSONL with metadata.
3. **Indexing (index_corpus.py)**: Embed the structured data and index into Qdrant vector store.
4. **Qdrant Management (manage_qdrant.py)**: Optional management of the Qdrant collection (delete or get info).
5. **RAG Agent (rag_agent.py)**: Core logic for retrieving relevant documents and generating responses using LLM.
6. **Configuration (config.py)**: Central configuration for paths, models, and settings.
7. **Application (app.py)**: Streamlit-based UI for interacting with the RAG agent, including dynamic model selection and system monitoring.

The pipeline prepares legal documents for semantic search and AI-assisted querying, enabling users to ask questions and receive context-aware responses.

## File Explanations

### app.py
- **What it does**: This is the main Streamlit application for the "Drveni Advokat" RAG system. It provides a user interface for selecting models, initializing the RAG agent, chatting with the AI, displaying conversation history, and monitoring system resources (CPU/RAM).
- **Inputs**: User queries via chat input; configuration from config.py; selected LLM model and device from sidebar.
- **Outputs**: AI responses streamed to the chat interface, including sources; chat history saved to JSON; system status metrics.
- **Workflow Integration**: Serves as the frontend entry point. It initializes the RAGAgent from rag_agent.py and handles interactive queries, displaying retrieved context in expanders.

### config.py
- **What it does**: Defines constants and default settings for the project, such as file paths, model names, device preferences, Qdrant configuration, and text cleaning options (e.g., boilerplate phrases to remove).
- **Inputs**: None (static file).
- **Outputs**: Exported variables used across other scripts (e.g., DEFAULT_LLM_MODEL, QDRANT_URL).
- **Workflow Integration**: Central hub for configuration. Imported by most scripts to ensure consistent settings, like paths for corpus processing or model selection in app.py.

### convert_corpus.py
- **What it does**: Recursively scans a directory for .doc files and converts them to .docx using the `soffice` command from LibreOffice/OpenOffice. Skips already converted files for resumability.
- **Inputs**: Source directory path; target directory path; optional path to soffice executable.
- **Outputs**: Converted .docx files in the target directory; logs conversion status to conversion_log.txt.
- **Workflow Integration**: First step in data preparation. Prepares legacy documents for text extraction in extract_and_structure.py.

### extract_and_structure.py
- **What it does**: Processes .docx files to extract and clean text (fixing encoding issues like YUSCII to Unicode, removing boilerplate), extracts metadata (e.g., case ID, judge), and structures data into JSONL format.
- **Inputs**: Source directory of .docx files; output JSONL file path.
- **Outputs**: A JSONL file with structured documents (full_text, metadata, source_file); logs errors to extraction_log.txt.
- **Workflow Integration**: Second step after conversion. Cleans and structures text for embedding and indexing in index_corpus.py.

### index_corpus.py
- **What it does**: Loads structured JSONL data, splits text into chunks, generates embeddings using SentenceTransformer, and upserts them into a Qdrant collection in batches.
- **Inputs**: Path to JSONL file; Qdrant URL; collection name.
- **Outputs**: Populated Qdrant collection with vector points; logs to indexing_log.txt.
- **Workflow Integration**: Third step. Indexes prepared data into the vector database for retrieval in rag_agent.py.

### rag_agent.py
- **What it does**: Defines the RAGAgent class, which initializes embeddings, connects to Qdrant, sets up an Ollama LLM, and creates a chain for retrieving documents and generating responses. Supports streaming.
- **Inputs**: LLM model name, embedding model, device (passed during initialization); user question for ask/stream_ask methods.
- **Outputs**: Generated response with sources; retrieved context documents; logs to rag_agent_log.txt.
- **Workflow Integration**: Core backend for queries. Used by app.py to handle user questions by retrieving from Qdrant and generating with LLM.

### manage_qdrant.py
- **What it does**: Provides CLI tools to manage Qdrant collections, including deleting a collection or getting detailed info (e.g., point count, config).
- **Inputs**: Action ('delete' or 'info'); collection name; optional Qdrant URL.
- **Outputs**: Console output with results or errors.
- **Workflow Integration**: Utility for maintenance. Used to reset or inspect the vector store before/after indexing.

## Additional Information on Ollama and Qdrant

### Ollama
Ollama is an open-source tool for running large language models (LLMs) locally. It simplifies deploying and managing models like Mistral or custom ones (e.g., YugoGPT).
- **Key Features**: Easy model pulling/running via CLI (e.g., `ollama run mistral`), API for integration, support for GPU acceleration.
- **Installation**: Download from ollama.ai; run `ollama serve` to start the server.
- **Usage in Project**: Used in rag_agent.py and app.py for LLM inference. Models are selected dynamically in the Streamlit sidebar.
- **Pros**: Local, private, no API costs. Cons: Requires sufficient hardware (e.g., GPU for large models).
- **More Info**: Visit https://ollama.ai for docs, model library, and troubleshooting.

### Qdrant (referred to as Quadrant in the query)
Qdrant is a vector database for storing and querying high-dimensional vectors efficiently, ideal for semantic search in RAG systems.
- **Key Features**: Supports cosine/Euclidean similarity, collections with configurable dimensions, batch operations, REST API.
- **Installation**: Run via Docker: `docker run -p 6333:6333 qdrant/qdrant`.
- **Usage in Project**: Stores embedded legal document chunks (in index_corpus.py), retrieved in rag_agent.py for context.
- **Pros**: Fast queries, scalable, open-source. Cons: Needs setup (e.g., Docker).
- **More Info**: Docs at https://qdrant.tech/documentation/. For this project, collection 'drveni_advokat' uses 768-dim vectors with Cosine distance.

## Suggestions for New Configuration Dashboard/UI
Currently, configuration is handled in config.py and the Streamlit sidebar in app.py. To make it more functional and advanced:
- **New UI Proposal**: Create a dedicated "Dashboard" page in Streamlit (using st.tabs or multi-page app) for editing config.py values dynamically (e.g., model selection, paths, cleaning options). Use st.form for inputs and save changes via file write.
- **Advanced Features**: Add buttons for running pipeline steps (e.g., convert, extract, index), real-time logs, Qdrant stats integration, and feedback mechanisms.
- **Implementation**: I can modify app.py to include this. If you'd like, toggle to Plan mode to discuss details, or confirm to proceed with changes.
