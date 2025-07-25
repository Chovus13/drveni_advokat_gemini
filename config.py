# ==============================================================================
# FAJL: config.py (Ažurirana verzija 3.0)
# ==============================================================================
# Ovde sada stoje samo podrazumevane vrednosti i konstante.
# Stvarna podešavanja se biraju dinamički u Streamlit aplikaciji.

# --- Putanje do foldera ---
SOURCE_DOC_DIR = r"I:\drveni_advokat_gemini\docs"
CONVERTED_DOCX_DIR = r"I:\drveni_advokat_gemini\converted_docs"
STRUCTURED_JSONL_PATH = r"data/structured_corpus.jsonl"
FEEDBACK_LOG_PATH = r"data/feedback_log.jsonl"

# --- Konfiguracija Modela i Uređaja ---
# Podrazumevane vrednosti koje će biti ponuđene u aplikaciji
DEFAULT_LLM_MODEL = "mistral:7b"  # Promenite na "YugoGPT" ako želite koristiti taj model
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
DEFAULT_DEVICE = "cuda" #####ili cuda za NVIDIA GPU
OLLAMA_HOST = "http://localhost:11434" # Eksplicitno definisanje Ollama hosta
LAST_USED_MODEL_FILE = "last_used_model.txt"


# Parametri za Indeksiranje (moraju odgovarati embedding modelu)
VECTOR_DIMENSION = 768 # Za paraphrase-multilingual-mpnet-base-v2
DISTANCE_METRIC = "Cosine"
BATCH_SIZE = 32

# --- Qdrant Konfiguracija ---
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "drveni_advokat"

FEEDBACK_LOG_PATH = r"data/feedback_log.jsonl" ############################################ ovo ne koristimo
FINETUNE_DATASET_PATH = r"data/finetuning_dataset.jsonl" ############################################ ovo ne koristimo
LORA_ADAPTER_PATH = r"models/drveni_advokat_lora_v1" ############################################ ovo ne koristimo
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


# ############ fali neki TXT - nadji na starijim verzijama
# # config.py (Verzija 2.0)

# # --- Putanje do foldera ---
# # Koristimo 'r' ispred stringa da izbegnemo probleme sa '\' na Windowsu
# SOURCE_DOC_DIR = r"I:\drveni_advokat_gemini\docs"
# CONVERTED_DOCX_DIR = r"I:\drveni_advokat_gemini\converted_docs"
# STRUCTURED_JSONL_PATH = r"data/structured_corpus.jsonl"
# FEEDBACK_LOG_PATH = r"data/feedback_log.jsonl"
# FINETUNE_DATASET_PATH = r"data/finetuning_dataset.jsonl" ############################################ ovo ne koristimo
# LORA_ADAPTER_PATH = r"models/drveni_advokat_lora_v1" ############################################ ovo ne koristimo

# # --- Konfiguracija Modela i Uređaja ---
# # Uređaj za izvršavanje embedding modela ('cpu' ili 'cuda' za NVIDIA GPU)
# DEVICE = "cuda" # Promenite u "cuda" ako koristite GTX 1080

# # Lista dostupnih LLM modela (koje ste preuzeli u Ollama)
# # AVAILABLE_LLMS = ["YugoGPT", "mistral:7b"]
# # Model koji se trenutno koristi
# BASE_LLM_MODEL = "mistral:7b"  # Promenite na "YugoGPT" ako želite koristiti taj model

# # Lista dostupnih embedding modela
# # AVAILABLE_EMBEDDING_MODELS = [
# #     "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
# #     "sentence-transformers/all-MiniLM-L6-v2"
# # ]
# # Model koji se trenutno koristi
# EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
# # EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
# # --- Parametri za Indeksiranje ---
# # Dimenzija vektora mora odgovarati odabranom embedding modelu!
# # paraphrase-multilingual-mpnet-base-v2 -> 768
# # all-MiniLM-L6-v2 -> 384
# VECTOR_DIMENSION = 768
# DISTANCE_METRIC = "Cosine" # Qdrant prihvata string "Cosine", "Euclid", ili "Dot"
# BATCH_SIZE = 32

# # --- Qdrant Konfiguracija ---
# QDRANT_URL = "http://localhost:6333"
# QDRANT_COLLECTION_NAME = "drveni_advokat"

