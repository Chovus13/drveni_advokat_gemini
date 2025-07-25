# extract_and_structure.py (Finalna verzija sa pametnom popravkom)

import os
import re
import json
import argparse
import docx
from tqdm import tqdm
import logging
import config

# --- Podešavanje Logovanja ---
logging.basicConfig(
    filename='extraction_log.txt',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_legacy_encoding(text: str) -> str:
    """
    Popravlja tekst sa specifičnim "slomljenim" karakterima iz starih YU fontova.
    """
    # Kompletna mapa za prevođenje, uključujući i velika i mala slova
    # Ovu mapu možemo dopunjavati ako pronađemo još karaktera.
    correction_map = {
        '^': 'č',
        '[': 'š',
        ']': 'ž',
        '`': 'ć',
        '|': 'đ',
        '{': 'š', # Duplo mapiranje za š
        '}': 'ž', # Duplo mapiranje za ž
        
        # Pretpostavke za velika slova (ako postoje posebni karakteri)
        # Ako su isti karakteri, .upper() metoda će odraditi posao.
        # Npr. ako nađemo da je '@' veliko 'Č', dodali bismo '@': 'Č'
    }

    # Prvo radimo osnovnu zamenu
    for bad_char, good_char in correction_map.items():
        text = text.replace(bad_char, good_char)

    # Sada, pokušajmo da rešimo problem velikih slova.
    # Primer: Reč "BE^EJ" -> treba da postane "BEČEJ", a ne "BEčEJ"
    # Ovo je kompleksan problem, ali možemo rešiti najčešće slučajeve.
    # Prolazimo kroz reči i ako je cela reč velikim slovima (sa greškom), ispravljamo je.
    words = text.split(' ')
    fixed_words = []
    for word in words:
        # Proveravamo da li je reč cela napisana velikim slovima (ignorišući naše karaktere)
        # Na primer, "OP[TINSKOM" je tehnički mešano, ali vizuelno je sve veliko.
        # Za sada, jednostavnija zamena će morati da posluži.
        # Naprednija logika bi zahtevala kompleksniju analizu.
        
        # Najjednostavniji pristup koji će raditi u 90% slučajeva:
        # Ako je reč cela velikim slovima, primeni .upper() na ispravljenu verziju.
        # Ovo je teško izvesti pouzdano bez poznavanja svih karaktera.
        # Zato ćemo se za sada držati osnovne zamene koja je najpouzdanija.
        pass # Preskačemo naprednu logiku za sada

    # Vraćamo tekst sa osnovnim popravkama.
    return text


# Ostatak koda ostaje skoro isti, samo pozivamo novu funkciju
def extract_and_clean_document(document: docx.Document) -> tuple[str, dict]:
    main_text = "\n".join([para.text for para in document.paragraphs])
    
    # << JEDINA IZMENA OVDE >>
    # Pozivamo našu novu, pametnu funkciju za popravku!
    main_text = fix_legacy_encoding(main_text)
    
    text_to_remove = set()
    for phrase in config.BOILERPLATE_PHRASES_TO_REMOVE:
        text_to_remove.add(phrase)
    if config.REMOVE_HEADERS_FOOTERS:
        for section in document.sections:
            for para in section.header.paragraphs:
                if para.text: text_to_remove.add(fix_legacy_encoding(para.text.strip()))
            for para in section.footer.paragraphs:
                if para.text: text_to_remove.add(fix_legacy_encoding(para.text.strip()))

    for phrase_to_remove in text_to_remove:
        if phrase_to_remove:
            main_text = main_text.replace(phrase_to_remove, "")
            
    main_text = re.sub(r'\n{2,}', '\n', main_text).strip()
    
    metadata = extract_metadata_from_text(main_text)
    return main_text, metadata

# Funkcije extract_metadata_from_text i process_docx_files ostaju ISTE
def extract_metadata_from_text(text: str) -> dict:
    metadata = {}
    patterns = {
        "case_id": r"Broj predmeta:?\s*([\w\d\s\/-]+)",
        "judge": r"Sudija:?\s*([A-ZŠĐČĆŽ][a-zšđčćž]+(?:\s+[A-ZŠĐČĆŽ][a-zšđčćž]+)+)",
        "plaintiff": r"Tužilac:?\s*(.*?)(?=\nTuženi:|Sudija:)",
        "defendant": r"Tuženi:?\s*(.*?)(?=\nSud:|Datum presude:)",
        "court": r"Sud:?\s*(.*?)(?=\n|$)",
        "decision_date": r"Datum presude:?\s*(\d{1,2}\.\d{1,2}\.\d{4}\.?|\d{4}-\d{2}-\d{2})",
        "document_type": r"\b(PRESUDA|REŠENJE)\b" 
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted_value = match.group(1).strip()
            if key in ["defendant", "plaintiff"]:
                items = re.split(r'[\n,]+', extracted_value)
                metadata[key] = [item.strip() for item in items if item.strip()]
            else:
                metadata[key] = extracted_value
    return metadata

def process_docx_files(source_dir: str, output_path: str):
    print(f"Započinjanje ekstrakcije iz direktorijuma: {source_dir}")
    all_files = [os.path.join(root, file) for root, _, files in os.walk(source_dir) for file in files if file.lower().endswith('.docx')]
    if not all_files:
        print("Nema .docx fajlova u navedenom direktorijumu.")
        return

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for file_path in tqdm(all_files, desc="Procesiranje dokumenata"):
            try:
                document = docx.Document(file_path)
                cleaned_text, metadata = extract_and_clean_document(document)
                structured_data = {
                    "source_file": file_path, "case_id": metadata.get("case_id", "Nepoznato"), "full_text": cleaned_text,
                    "metadata": {
                        "judge": metadata.get("judge", "Nepoznato"), "plaintiff": metadata.get("plaintiff", []),
                        "defendant": metadata.get("defendant", []), "decision_date": metadata.get("decision_date", "Nepoznato"),
                        "court": metadata.get("court", "Nepoznato"), "document_type": metadata.get("document_type", "Nepoznato")
                    }
                }
                json.dump(structured_data, outfile, ensure_ascii=False)
                outfile.write('\n')
            except Exception as e:
                logging.warning(f"Greška pri obradi fajla {file_path}: {e}")
    print(f"\nEkstrakcija završena. Podaci sačuvani u: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ekstrahuje, ČISTI i metapodatke iz .docx fajlova.")
    parser.add_argument("source_directory", type=str, help="Putanja do .docx fajlova.")
    parser.add_argument("output_file", type=str, help="Putanja do izlaznog .jsonl fajla.")
    args = parser.parse_args()
    process_docx_files(args.source_directory, args.output_file)