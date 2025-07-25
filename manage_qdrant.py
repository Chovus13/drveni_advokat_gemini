# manage_qdrant.py (Ažurirana verzija sa 'info' komandom)
import argparse
from qdrant_client import QdrantClient

def get_collection_info(qdrant_url: str, collection_name: str):
    """Prikazuje informacije o navedenoj kolekciji."""
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"Pribavljam informacije za kolekciju '{collection_name}'...")
        collection_info = client.get_collection(collection_name=collection_name)
        print("\n--- Informacije o kolekciji ---")
        print(collection_info)

        # Hajde da prebrojimo i tačke
        count_result = client.count(collection_name=collection_name, exact=True)
        print("\n--- Broj tačaka (vektora) ---")
        print(count_result)
        
    except Exception as e:
        print(f"Došlo je do greške ili kolekcija ne postoji: {e}")

def delete_collection(qdrant_url: str, collection_name: str):
    """Briše navedenu kolekciju."""
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"Pokušavam da obrišem kolekciju '{collection_name}'...")
        result = client.delete_collection(collection_name=collection_name)
        if result:
            print(f"Kolekcija '{collection_name}' je uspešno obrisana.")
        else:
            print(f"Brisanje nije uspelo ili kolekcija nije postojala.")
    except Exception as e:
        print(f"Došlo je do greške: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pomoćni alat za upravljanje Qdrant kolekcijama.")
    parser.add_argument("action", type=str, choices=['delete', 'info'], help="Akcija koju treba izvršiti.")
    parser.add_argument("collection_name", type=str, help="Ime kolekcije.")
    parser.add_argument("--qdrant-url", type=str, default="http://localhost:6333", help="URL Qdrant instance.")
    
    args = parser.parse_args()
    
    if args.action == 'delete':
        delete_collection(args.qdrant_url, args.collection_name)
    elif args.action == 'info':
        get_collection_info(args.qdrant_url, args.collection_name)