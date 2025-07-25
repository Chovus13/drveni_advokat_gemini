# index_corpus.py

import os
import json
import argparse
import uuid
from tqdm import tqdm
import logging

# Važno: Instalirajte potrebne biblioteke pre pokretanja
# pip install qdrant-client sentence-transformers langchain
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Podešavanje za logovanje
logging.basicConfig(
    filename='indexing_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- KONFIGURACIJA ---
# U realnom projektu, ovi parametri bi bili u config.py
# Ime modela za embedovanje. 'all-MiniLM-L6-v2' je dobar i brz izbor.
# EMBEDDING_MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

EMBEDDING_MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
# # Dimenzionalnost vektora za odabrani model. Za 'all-MiniLM-L6-v2' je 384.
# VECTOR_DIMENSION = 384
VECTOR_DIMENSION = 768
# Metrika za poređenje vektora. Cosine je standard za tekstualne embedinge.
DISTANCE_METRIC = models.Distance.COSINE
# Veličina serije (batch) za unos u Qdrant.
BATCH_SIZE = 64 # Smanjujemo batch size za debugovanje - bilo 128

def setup_qdrant_collection(client: QdrantClient, collection_name: str):
    try:
        client.get_collection(collection_name=collection_name)
        logging.info(f"Kolekcija '{collection_name}' već postoji.")
        print(f"Kolekcija '{collection_name}' već postoji.")
    except Exception:
        logging.info(f"Kreiranje nove kolekcije: '{collection_name}'")
        print(f"Kreiranje nove kolekcije: '{collection_name}'")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=VECTOR_DIMENSION, distance=DISTANCE_METRIC),
        )
        # TODO: Dodati kreiranje indeksa za metapodatke ovde kada definišemo tačna polja za filtriranje
        # client.create_payload_index(collection_name=collection_name, field_name="metadata.court", field_schema="keyword")

def process_batch(client, model, collection_name, points):
    if not points:
        return 0
    print(f"--> PROCESIRAM BATCH OD {len(points)} TAČAKA...")
    texts_to_embed = [point.payload["page_content"] for point in points]
    vectors = model.encode(texts_to_embed, show_progress_bar=True, batch_size=32)
    for i, point in enumerate(points):
        point.vector = vectors[i].tolist()
    client.upsert(collection_name=collection_name, points=points, wait=True)
    logging.info(f"Uspešno uneto {len(points)} tačaka u Qdrant.")
    print(f"--> BATCH USPEŠNO UNET.")
    return len(points)

    
def index_corpus(jsonl_path: str, qdrant_url: str, collection_name: str):
    print("Inicijalizacija klijenata i modela...")
    qdrant_client = QdrantClient(url=qdrant_url)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    setup_qdrant_collection(qdrant_client, collection_name)

    print(f"Čitanje i obrada fajla: {jsonl_path}")
    
    points_batch = []
    total_points_processed = 0

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Pronađeno ukupno {len(lines)} dokumenata (linija) u fajlu.")

        for i, line in enumerate(tqdm(lines, desc="Indeksiranje dokumenata")):
            try:
                doc = json.loads(line)
                if not doc.get('full_text', '').strip():
                    if i < 5: print(f"  - Preskačem dokument {i} jer nema tekst.")
                    continue
                
                # Debug ispis za prvih 5 dokumenata
                if i < 5: print(f"Obradjujem dokument {i}: {doc.get('source_file')}")
                
                chunks = text_splitter.split_text(doc['full_text'])
                if i < 5: print(f"  - Broj chunk-ova: {len(chunks)}")

                for chunk_text in chunks:
                    point_id = str(uuid.uuid4())
                    payload = {
                        "page_content": chunk_text,
                        "metadata": doc.get("metadata", {}),
                        "source_file": doc.get("source_file", "")
                    }
                    points_batch.append(models.PointStruct(id=point_id, payload=payload))
                
                if len(points_batch) >= BATCH_SIZE:
                    processed_count = process_batch(qdrant_client, embedding_model, collection_name, points_batch)
                    total_points_processed += processed_count
                    points_batch = []

            except Exception as e:
                logging.error(f"Greška pri obradi linije {i}: {line.strip()} - Greška: {e}")

    if points_batch:
        processed_count = process_batch(qdrant_client, embedding_model, collection_name, points_batch)
        total_points_processed += processed_count
    
    print(f"\nIndeksiranje (trebalo bi da je) završeno.")
    print(f"Ukupno obrađeno i uneto tačaka (chunk-ova): {total_points_processed}")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Indeksira strukturirani JSONL korpus u Qdrant vektorsku bazu."
    )
    parser.add_argument("jsonl_path", type=str, help="Putanja do structured_corpus.jsonl fajla.")
    parser.add_argument("--qdrant-url", type=str, default="http://localhost:6333", help="URL Qdrant instance.")
    parser.add_argument("--collection-name", type=str, default="drveni_advokat", help="Ime Qdrant kolekcije.")

    args = parser.parse_args()
    
    index_corpus(args.jsonl_path, args.qdrant_url, args.collection_name)