# config.py

# --- Putanje do foldera ---
SOURCE_DOC_DIR = r"I:\drveni_advokat_gemini\docs"
CONVERTED_DOCX_DIR = r"I:\drveni_advokat_gemini\converted_docs"
STRUCTURED_JSONL_PATH = "data/structured_corpus.jsonl"
FEEDBACK_LOG_PATH = "data/feedback_log.jsonl"
# ... ostale putanje ...

# --- Parametri modela ---
BASE_LLM_MODEL = "mistral:7b"
# EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# NOVA, POBOLJŠANA LINIJA:
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# --- Qdrant Konfiguracija ---
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "drveni_advokat"

# --- Čišćenje teksta (Text Cleaning) ---
# Da li da se automatski ukloni tekst iz zaglavlja (header) i podnožja (footer)?
REMOVE_HEADERS_FOOTERS = True

# Lista specifičnih fraza koje treba ukloniti iz teksta.
# Svaka fraza će biti uklonjena ako se pronađe u tekstu.
BOILERPLATE_PHRASES_TO_REMOVE = [
    "Telefon/faks:   +381 21 816 772",
    "E-mail address:   nikkosan@EUnet.yu",
    "      -      ",
    "     -      ",
    "Sva prava zadržana.",
    "Mobtel:   +381 21 063 509 885",
    "063 509 885",
    # Ovde možete dodati bilo koje druge repetitivne rečenice.
    # Na primer, ako znate tačan format email-a ili broja telefona:
    "Kontakt telefon:",
    "E-mail address:   nikkosan@EUnet.yu"
]