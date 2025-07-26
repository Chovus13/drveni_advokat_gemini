# index_corpus.py (FINALNA I ISPRAVLJENA VERZIJA)

import os
import json
import argparse
import uuid
from tqdm import tqdm
import logging
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
import config

# --- Konfiguracija ---
logging.basicConfig(filename='indexing_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
EMBEDDING_MODEL_NAME = config.DEFAULT_EMBEDDING_MODEL
VECTOR_DIMENSION = config.VECTOR_DIMENSION
DISTANCE_METRIC = getattr(models.Distance, config.DISTANCE_METRIC.upper())
BATCH_SIZE = config.BATCH_SIZE

def setup_qdrant_collection(client: QdrantClient, collection_name: str):
    """Proverava i kreira Qdrant kolekciju."""
    try:
        client.get_collection(collection_name=collection_name)
        print(f"Kolekcija '{collection_name}' već postoji.")
    except Exception:
        print(f"Kreiranje nove kolekcije: '{collection_name}'")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=VECTOR_DIMENSION, distance=DISTANCE_METRIC),
        )

def index_corpus(jsonl_path: str, qdrant_url: str = config.QDRANT_URL, collection_name: str = config.QDRANT_COLLECTION_NAME):
    """Glavna funkcija za indeksiranje JSONL korpusa u Qdrant."""
    
    # --- Inicijalizacija ---
    print("Inicijalizacija klijenata i modela...")
    qdrant_client = QdrantClient(url=qdrant_url)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    setup_qdrant_collection(qdrant_client, collection_name)
    
    # --- FAZA 1: Priprema Svih Tačaka (Points) ---
    print(f"Čitanje fajla '{jsonl_path}' i priprema podataka...")
    
    all_points = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Priprema dokumenata"):
            try:
                doc = json.loads(line)
                if not doc.get('full_text', '').strip():
                    continue
                
                chunks = text_splitter.split_text(doc['full_text'])
                for chunk_text in chunks:
                    point_id = str(uuid.uuid4())
                    payload = {
                        "page_content": chunk_text,
                        "metadata": doc.get("metadata", {}),
                        "source_file": doc.get("source_file", "")
                    }
                    # Dodajemo tačku bez vektora za sada
                    all_points.append(models.PointStruct(id=point_id, payload=payload, vector=[]))
            except json.JSONDecodeError:
                logging.warning(f"Greška pri parsiranju JSON reda. Red preskočen.")

    print(f"Priprema završena. Ukupno kreirano {len(all_points)} chunk-ova (tačaka) za unos.")

    if not all_points:
        print("Nema podataka za indeksiranje. Izlazim.")
        return

    # --- FAZA 2: Unos u Bazu u Serijama (Batches) ---
    print("Započinjanje unosa podataka u Qdrant u serijama...")
    
    # tqdm će nam sada pokazati napredak unosa serija
    for i in tqdm(range(0, len(all_points), BATCH_SIZE), desc="Unos u Qdrant"):
        # Uzimamo isečak (slice) liste za trenutnu seriju
        batch_points = all_points[i : i + BATCH_SIZE]
        
        # Ekstrahujemo tekstove iz serije za embedovanje
        texts_to_embed = [point.payload["page_content"] for point in batch_points]
        
        # Generišemo embedinge (OVO JE SPORI DEO)
        vectors = embedding_model.encode(texts_to_embed)
        
        # Dodajemo vektore u naše tačke
        for j, point in enumerate(batch_points):
            point.vector = vectors[j].tolist()
            
        # Unosimo celu seriju u Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=batch_points,
            wait=True
        )

    print(f"\nIndeksiranje uspešno završeno! Ukupno uneto {len(all_points)} tačaka.")
    # Provera finalnog broja
    count_result = qdrant_client.count(collection_name=collection_name, exact=True)
    print(f"Finalni broj tačaka u kolekciji '{collection_name}': {count_result.count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Indeksira strukturirani JSONL korpus u Qdrant.")
    parser.add_argument("jsonl_path", type=str, help="Putanja do structured_corpus.jsonl fajla.")
    parser.add_argument("--qdrant-url", type=str, default=config.QDRANT_URL, help="URL Qdrant instance.")
    parser.add_argument("--collection-name", type=str, default=config.QDRANT_COLLECTION_NAME, help="Ime Qdrant kolekcije.")
    args = parser.parse_args()
    index_corpus(args.jsonl_path, args.qdrant_url, args.collection_name)
