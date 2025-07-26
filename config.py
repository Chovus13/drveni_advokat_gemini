# ==============================================================================
# FAJL: config.py (Ažurirana verzija 4.0 - Dinamičko učitavanje iz JSON)
# ==============================================================================
import json

# Učitavanje konfiguracije iz dynamic_config.json
try:
    with open('dynamic_config.json', 'r', encoding='utf-8') as f:
        config_data = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError("dynamic_config.json nije pronađen. Molimo kreirajte ga na osnovu podrazumevanih vrednosti.")

# Dodela vrednosti iz JSON-a
SOURCE_DOC_DIR = config_data.get('SOURCE_DOC_DIR', '/docs')
CONVERTED_DOCX_DIR = config_data.get('CONVERTED_DOCX_DIR', '/converted_docs')
STRUCTURED_JSONL_PATH = config_data.get('STRUCTURED_JSONL_PATH', 'data/structured_corpus.jsonl')
FEEDBACK_LOG_PATH = config_data.get('FEEDBACK_LOG_PATH', 'data/feedback_log.jsonl')
DEFAULT_LLM_MODEL = config_data.get('DEFAULT_LLM_MODEL', 'mistral:7b')
DEFAULT_EMBEDDING_MODEL = config_data.get('DEFAULT_EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
DEFAULT_DEVICE = config_data.get('DEFAULT_DEVICE', 'cuda')
OLLAMA_HOST = config_data.get('OLLAMA_HOST', 'http://localhost:11434')
VECTOR_DIMENSION = config_data.get('VECTOR_DIMENSION', 768)
DISTANCE_METRIC = config_data.get('DISTANCE_METRIC', 'Cosine')
BATCH_SIZE = config_data.get('BATCH_SIZE', 32)
QDRANT_URL = config_data.get('QDRANT_URL', 'http://localhost:6333')
QDRANT_COLLECTION_NAME = config_data.get('QDRANT_COLLECTION_NAME', 'drveni_advokat')
REMOVE_HEADERS_FOOTERS = config_data.get('REMOVE_HEADERS_FOOTERS', True)
BOILERPLATE_PHRASES_TO_REMOVE = config_data.get('BOILERPLATE_PHRASES_TO_REMOVE', [])
METADATA_CATEGORIES = config_data.get('METADATA_CATEGORIES', {})
