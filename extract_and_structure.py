# extract_and_structure.py (Verzija 5.0 - sa "Kamenom iz Rozete" mapom)

import os
import re
import json
import argparse
import docx
from tqdm import tqdm
import logging
import ftfy
import config

logging.basicConfig(
    filename='extraction_log.txt',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def convert_yuscii_to_unicode(text: str) -> str:
    """
    Konvertuje tekst iz YUSCII (custom CP1250) rasporeda u ispravan Unicode (UTF-8).
    Mapa je zasnovana na vašim primerima i standardnim YUSCII rasporedima.
    """
    # Ovaj "kamen iz Rozete" je ključan.
    # Prilagodite ga ako primetite još neke specifične karaktere u vašim dokumentima.
    yuscii_map = {
        # Mala slova - na osnovu vašeg primera "Ne}emo li da vidimo ko `eli"
        '[': 'Š',
        ']': 'Ć',
        '\\': 'Đ',
        '@': 'Ž',
        '^': 'Č',
        
        # Velika slova - na osnovu primera "^okolom"

        '{': 'š', # Pretpostavka na osnovu standarda
        '}': 'ć', # Pretpostavka na osnovu standarda
        '|': 'đ', # Pretpostavka na osnovu standarda
        '~': 'č', # Pretpostavka na osnovu standarda
        '`': 'ž',
        
        # Dvoslovna slova
        'q': 'lj',
        'w': 'nj',
        'x': 'dž',
        'Q': 'Lj',
        'W': 'Nj',
        'X': 'Dž',
    }
    
    # Sortiramo ključeve po dužini, opadajuće.
    # Ovo osigurava da se "Lj" zameni pre nego što bi se zamenili "L" ili "j".
    # Iako trenutno nemamo takve slučajeve, pristup je robustan.
    sorted_keys = sorted(yuscii_map.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        text = text.replace(key, yuscii_map[key])
        
    return text

def fix_legacy_text(text: str) -> str:
    """
    Kompletan, dvostepeni proces čišćenja teksta koji kombinuje
    specifičnu popravku i generalno "peglanje".
    """
    # Korak 1: Hirurški precizna popravka za naš specifičan YU Swiss/YUSCII problem.
    text = convert_yuscii_to_unicode(text)
    
    # Korak 2: Generalno "peglanje" teksta koje popravlja sve ostale
    # potencijalne greške u kodiranju (poznate kao "mojibake").
    text = ftfy.fix_text(text)
    
    return text

# Ostatak koda je skoro isti, samo poziva novu, jednostavniju funkciju
def extract_and_clean_document(document: docx.Document) -> tuple[str, dict]:
    main_text = "\n".join([para.text for para in document.paragraphs if para.text])
    
    # Pozivamo našu finalnu, dvostepenu funkciju za popravku!
    main_text = fix_legacy_text(main_text)
    
    # Deo za čišćenje boilerplate teksta
    text_to_remove = set()
    for phrase in config.BOILERPLATE_PHRASES_TO_REMOVE:
        text_to_remove.add(phrase)
    if config.REMOVE_HEADERS_FOOTERS:
        for section in document.sections:
            for para in section.header.paragraphs:
                # Važno: I ovde primenite istu funkciju!
                if para.text: text_to_remove.add(fix_legacy_text(para.text.strip()))
            for para in section.footer.paragraphs:
                # I ovde takođe!
                if para.text: text_to_remove.add(fix_legacy_text(para.text.strip()))
    for phrase_to_remove in text_to_remove:
        if phrase_to_remove:
            main_text = main_text.replace(phrase_to_remove, "")
    main_text = re.sub(r'\n{2,}', '\n', main_text).strip()
    
    # Ekstrakcija metapodataka iz sada potpuno čistog teksta
    metadata = extract_metadata_from_text(main_text)
    
    return main_text, metadata

# Funkcije extract_metadata_from_text i process_docx_files ostaju ISTE
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