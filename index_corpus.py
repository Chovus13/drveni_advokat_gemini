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
    """Proverava da li kolekcija postoji i kreira je ako ne postoji koristeći moderniji pristup."""
    try:
        # collection_exists ne postoji u starijim verzijama, pa koristimo get_collection
        client.get_collection(collection_name=collection_name)
        logging.info(f"Kolekcija '{collection_name}' već postoji.")
        print(f"Kolekcija '{collection_name}' već postoji, nastavlja se sa unosom.")
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
    """Generiše embedinge za batch i unosi ga u Qdrant."""
    texts_to_embed = [point.payload["page_content"] for point in points]
    
    # Generisanje embedinga za sve tekstove u batch-u odjednom (mnogo brže)
    vectors = model.encode(texts_to_embed, show_progress_bar=False)
    
    # Dodavanje vektora u odgovarajuće tačke
    for i, point in enumerate(points):
        point.vector = vectors[i].tolist()
        
    # Unos (upsert) celog batch-a u Qdrant
    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=False  # wait=False za brži unos, Qdrant obrađuje u pozadini
    )
    logging.info(f"Uspešno uneto {len(points)} tačaka u Qdrant.")

    
def index_corpus(jsonl_path: str, qdrant_url: str, collection_name: str):
    """Glavna funkcija za indeksiranje JSONL korpusa u Qdrant."""

    # 1. Inicijalizacija klijenata i modela
    print("Inicijalizacija klijenata i modela...")
    qdrant_client = QdrantClient(url=qdrant_url)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    logging.info("Klijenti i modeli uspešno inicijalizovani.")

    # 2. Postavljanje Qdrant kolekcije
    setup_qdrant_collection(qdrant_client, collection_name)

    # 3. Čitanje i obrada JSONL fajla
    print(f"Čitanje i obrada fajla: {jsonl_path}")
    
    points_batch = []

    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f, desc="Indeksiranje dokumenata"):
            try:
                doc = json.loads(line)
                
                # Preskačemo dokumente bez teksta
                if not doc.get('full_text'):
                    logging.warning(f"Preskočen dokument bez teksta: {doc.get('source_file')}")
                    continue

                # Deljenje teksta na manje delove (chunks)
                chunks = text_splitter.split_text(doc['full_text'])
                
                # Kreiranje tačaka (points) za svaki chunk
                for chunk_text in chunks:
                    # Svaka tačka dobija jedinstveni ID
                    point_id = str(uuid.uuid4())
                    
                    # Payload sadrži sam tekst i sve metapodatke od roditeljskog dokumenta
                    payload = {
                        "page_content": chunk_text,
                        "metadata": doc.get("metadata", {}),
                        "source_file": doc.get("source_file", "")
                    }
                    
                    # Pripremamo tačku bez vektora za sada
                    points_batch.append(models.PointStruct(id=point_id, payload=payload, vector=None))

                # Kada batch dostigne definisanu veličinu, obrađujemo ga
                if len(points_batch) >= BATCH_SIZE:
                    process_batch(qdrant_client, embedding_model, collection_name, points_batch)
                    points_batch = [] # Resetujemo batch

            except json.JSONDecodeError:
                logging.error(f"Greška pri parsiranju reda: {line.strip()}")
            except Exception as e:
                logging.error(f"Neočekivana greška: {e}")

    # Obrada preostalih tačaka u poslednjem batch-u
    if points_batch:
        process_batch(qdrant_client, embedding_model, collection_name, points_batch)

    print("\nIndeksiranje uspešno završeno.")




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Indeksira strukturirani JSONL korpus u Qdrant vektorsku bazu."
    )
    parser.add_argument("jsonl_path", type=str, help="Putanja do structured_corpus.jsonl fajla.")
    parser.add_argument("--qdrant-url", type=str, default="http://localhost:6333", help="URL Qdrant instance.")
    parser.add_argument("--collection-name", type=str, default="drveni_advokat", help="Ime Qdrant kolekcije.")

    args = parser.parse_args()
    
    index_corpus(args.jsonl_path, args.qdrant_url, args.collection_name)