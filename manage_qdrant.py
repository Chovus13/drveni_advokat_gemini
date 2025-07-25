# manage_qdrant.py
import argparse
from qdrant_client import QdrantClient

def delete_collection(qdrant_url: str, collection_name: str):
    """Povezuje se na Qdrant i briše navedenu kolekciju."""
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"Pokušavam da obrišem kolekciju '{collection_name}'...")
        result = client.delete_collection(collection_name=collection_name)
        if result:
            print(f"Kolekcija '{collection_name}' je uspešno obrisana.")
        else:
            # Ovo se može desiti ako kolekcija nije ni postojala
            print(f"Brisanje kolekcije '{collection_name}' nije uspelo ili kolekcija nije postojala.")
    except Exception as e:
        print(f"Došlo je do greške: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pomoćni alat za upravljanje Qdrant kolekcijama.")
    parser.add_argument("action", type=str, choices=['delete'], help="Akcija koju treba izvršiti (trenutno samo 'delete').")
    parser.add_argument("collection_name", type=str, help="Ime kolekcije na koju se primenjuje akcija.")
    parser.add_argument("--qdrant-url", type=str, default="http://localhost:6333", help="URL Qdrant instance.")
    
    args = parser.parse_args()
    
    if args.action == 'delete':
        delete_collection(args.qdrant_url, args.collection_name)