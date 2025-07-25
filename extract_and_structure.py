# extract_and_structure.py (Verzija 3.0 - Finalna sa kompletnom mapom)

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
    Popravlja tekst sa specifičnim "slomljenim" karakterima iz starih YU/CP1250 fontova.
    Ovo je finalna, proširena mapa.
    """
    # Mapa za prevođenje karaktera
    correction_map = {
        # Mala slova
        '^': 'č',
        '|': 'đ',
        '[': 'š',
        ']': 'ž',
        '`': 'ć',
        # Neki fontovi su koristili i ove karaktere
        '{': 'š',
        '}': 'ž',
        '@': 'ž',
        
        # Velika slova
        '~': 'Č',
        '\\': 'Đ',
        '<': 'Š',
        '>': 'Ž',
        '=': 'Ć',
    }

    # Prolazimo kroz mapu i vršimo zamenu
    for bad_char, good_char in correction_map.items():
        text = text.replace(bad_char, good_char)
        
    return text

def extract_and_clean_document(document: docx.Document) -> tuple[str, dict]:
    """
    Prima ceo docx dokument objekat, popravlja enkodiranje, čisti ga i ekstrahuje metapodatke.
    """
    # Sastavljanje glavnog teksta iz paragrafa
    main_text = "\n".join([para.text for para in document.paragraphs if para.text])
    
    # KORAK 1: "Lečenje" teksta pre bilo kakve dalje obrade!
    main_text = fix_legacy_encoding(main_text)
    
    # KORAK 2: Prikupljanje teksta za uklanjanje (boilerplate)
    text_to_remove = set()
    for phrase in config.BOILERPLATE_PHRASES_TO_REMOVE:
        text_to_remove.add(phrase)

    if config.REMOVE_HEADERS_FOOTERS:
        for section in document.sections:
            # Zaglavlja
            for para in section.header.paragraphs:
                if para.text:
                    # Prvo "izlečimo" tekst iz headera/footera pa ga onda dodamo za brisanje
                    text_to_remove.add(fix_legacy_encoding(para.text.strip()))
            # Podnožja
            for para in section.footer.paragraphs:
                if para.text:
                    text_to_remove.add(fix_legacy_encoding(para.text.strip()))

    # KORAK 3: Uklanjanje boilerplate teksta
    for phrase_to_remove in text_to_remove:
        if phrase_to_remove:
            main_text = main_text.replace(phrase_to_remove, "")
            
    # KORAK 4: Finalno čišćenje (višestruki prazni redovi)
    main_text = re.sub(r'\n{2,}', '\n', main_text).strip()
    
    # KORAK 5: Ekstrakcija metapodataka iz sada potpuno čistog teksta
    metadata = extract_metadata_from_text(main_text)
    
    return main_text, metadata


# Funkcije extract_metadata_from_text, process_docx_files i __main__ blok ostaju POTPUNO ISTI
# Nema potrebe da ih menjate, ali ih ostavljam ovde radi kompletnosti
def extract_metadata_from_text(text: str) -> dict:
    metadata = {}
    patterns = {
        "case_id": r"Broj predmeta:?\s*([\w\d\s\/-]+)", "judge": r"Sudija:?\s*([A-ZŠĐČĆŽ][a-zšđčćž]+(?:\s+[A-ZŠĐČĆŽ][a-zšđčćž]+)+)",
        "plaintiff": r"Tužilac:?\s*(.*?)(?=\nTuženi:|Sudija:)", "defendant": r"Tuženi:?\s*(.*?)(?=\nSud:|Datum presude:)",
        "court": r"Sud:?\s*(.*?)(?=\n|$)", "decision_date": r"Datum presude:?\s*(\d{1,2}\.\d{1,2}\.\d{4}\.?|\d{4}-\d{2}-\d{2})",
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