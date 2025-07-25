Drveni Advokat: Tehnički Plan Izvršenja
Svrha Dokumenta: Ovaj dokument je samostalna tehnička specifikacija i vodič za izvršenje projekta 'Drveni advokat'. Služi kao "master prompt" za AI asistenta, osiguravajući kontinuitet i potpuno razumevanje projekta u bilo kom trenutku.

Misija: Razviti lokalni, privatni AI sistem koji transformiše arhivu od 200 GB .doc pravnih predmeta u inteligentnu, pretraživu bazu znanja. Sistem mora omogućiti interaktivno učenje kroz petlju povratnih informacija sa mentorom (advokatom), garantujući apsolutnu privatnost podataka.

Osnovna Filozofija Sistema !!!:
!!! Koristimo snagu BERT-ove arhitekture (kroz specijalizovani model kao što je srpski BERTić ili sličan) za dubinsko RAZUMEVANJE i PRETRAGU, a snagu GPT arhitekture (YugoGPT) za finalno PISANJE i ODGOVARANJE. !!!

Pregled Modula i Logički Tok
Sledi detaljan pregled svakog programskog modula, njegove logike, ulaznih i izlaznih podataka, kao i neophodnih biblioteka.

1. config.py - Centralni Konfiguracioni Fajl
Logika: Ovo nije izvršni fajl, već centralno mesto za sve konfiguracione varijable. Sprečava "hardkodovanje" putanja i parametara unutar glavnih skripti, čineći sistem lakšim za održavanje i prenos na drugi računar.

Sadržaj (Primer):

# Putanje do foldera
SOURCE_DOC_DIR = "D:/Pravna_Arhiva/Izvorni_DOC"
CONVERTED_DOCX_DIR = "D:/Pravna_Arhiva/Konvertovani_DOCX"
STRUCTURED_JSONL_PATH = "data/structured_corpus.jsonl"
FEEDBACK_LOG_PATH = "data/feedback_log.jsonl"
FINETUNE_DATASET_PATH = "data/finetuning_dataset.jsonl"
LORA_ADAPTER_PATH = "models/drveni_advokat_lora_v1"

# Parametri modela
BASE_LLM_MODEL = "gordicaleksa/YugoGPT"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Qdrant Konfiguracija
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "drveni_advokat_predmeti"

Biblioteke: Nema (samo osnovni Python).

2. convert_corpus.py - Faza 1: Konverzija Korpusa
Logika: Robusna, industrijska konverzija .doc u .docx. Skripta rekurzivno skenira izvorni direktorijum. Za svaki .doc fajl, poziva LibreOffice (soffice) u headless (bez grafičkog interfejsa) režimu putem subprocess modula. Ključna je implementacija logovanja za svaku operaciju i provera da li konvertovani fajl već postoji, kako bi se proces mogao prekinuti i nastaviti bez ponavljanja posla.

Ulaz (Input): SOURCE_DOC_DIR (putanja do 200 GB .doc arhive).

Izlaz (Output): Popunjen CONVERTED_DOCX_DIR sa identičnom strukturom foldera kao izvorni, i detaljan conversion_log.txt.

Biblioteke: os, subprocess, logging, config.

3. extract_and_structure.py - Faza 1: Ekstrakcija i Strukturiranje
Logika: Čitanje konvertovanih .docx fajlova. Koristi python-docx za ekstrakciju kompletnog teksta. Paralelno, koristi regularne izraze (re) za pronalaženje i izvlačenje ključnih metapodataka (broj predmeta, sudija, datum, itd.) direktno iz teksta. Sav "boilerplate" tekst (zaglavlja, podnožja) se uklanja. Za svaki dokument, kreira se čist JSON objekat koji sadrži pun tekst i strukturirane metapodatke.

Ulaz (Input): CONVERTED_DOCX_DIR (putanja do konvertovanih .docx fajlova).

Izlaz (Output): Jedan fajl, STRUCTURED_JSONL_PATH, gde je svaki red jedan kompletan, strukturiran pravni predmet u JSON formatu.

Biblioteke: python-docx, re, json, os, config.

4. index_corpus.py - Faza 2: Indeksiranje u Vektorsku Bazu
Logika: Učitava structured_corpus.jsonl. Za svaki predmet, koristi RecursiveCharacterTextSplitter iz LangChain-a da podeli full_text na semantički smislene delove (chunks). Svaki "chunk" nasleđuje metapodatke od svog roditeljskog dokumenta. Zatim, sentence-transformer model (koji je baziran na BERT arhitekturi i optimizovan za ovaj zadatak) pretvara svaki 'chunk' u vektor. Ovaj korak je ključan za razumevanje semantike teksta. Na kraju, qdrant-client se koristi za unos (upsert) svakog "chunka" kao tačke u Qdrant bazu, koja sadrži vektor i "payload" (tekst i metapodatke).

Ulaz (Input): STRUCTURED_JSONL_PATH.

Izlaz (Output): Popunjena i indeksirana Qdrant kolekcija na QDRANT_URL.

Biblioteke: langchain, sentence_transformers, qdrant_client, json, config.

5. rag_agent.py - Faza 2: Definicija RAG Agenta
Logika: Ovo je mozak sistema. Definiše kompletan RAG (Retrieval-Augmented Generation) lanac. Ovaj modul jasno razdvaja dve ključne uloge:

Retrieval (Pretraga): Koristi konekciju ka Qdrant bazi i oslanja se na vektore koje je stvorio model baziran na BERT arhitekturi kako bi pronašao najrelevantnije delove teksta.

Generation (Generisanje): Pronađene delove teksta šalje, zajedno sa originalnim pitanjem, lokalnom YugoGPT modelu (koji je baziran na GPT arhitekturi) da sastavi konačan, smislen odgovor.". Sadrži:

Konekciju ka lokalnom LLM-u preko Ollama.

Konekciju ka Qdrant bazi kao retriever-u, konfigurisanom da podržava hibridnu pretragu (semantičku + filtriranje po metapodacima).

Pažljivo sastavljen Prompt Template koji instruiše LLM kako da se ponaša, da koristi samo dati kontekst i da citira izvore.
Ovaj modul je dizajniran kao funkcija ili klasa koja se lako može pozvati iz Streamlit aplikacije.

Ulaz (Input): Tekstualni upit korisnika (string) i opcioni filteri (rečnik).

Izlaz (Output): Generisan tekstualni odgovor (string).

Biblioteke: langchain, langchain_community, qdrant_client, ollama, config.

6. app.py - Faza 3: Glavna Streamlit Aplikacija
Logika: Kreira interaktivni chat interfejs. Koristi st.session_state za čuvanje istorije razgovora. Za svaku novu poruku korisnika, poziva rag_agent da dobije odgovor. Prikazuje konverzaciju koristeći st.chat_message. Pored svakog odgovora agenta, integriše streamlit-feedback komponentu za ocenu i st.text_area za unos detaljne ispravke. Povratne informacije (upit, istorija, odgovor, ocena, ispravka) se čuvaju u FEEDBACK_LOG_PATH (.jsonl format).

Ulaz (Input): Interakcija korisnika (unos teksta, klikovi).

Izlaz (Output): Grafički korisnički interfejs i popunjavanje feedback_log.jsonl fajla.

Biblioteke: streamlit, streamlit_feedback, rag_agent, config.

7. finetuning.py - Faza 4: Petlja Učenja
Logika: Automatizuje proces učenja iz povratnih informacija.

Priprema podataka: Čita feedback_log.jsonl, filtrira zapise sa negativnom ocenom i unetom ispravkom. Transformiše ove zapise u format pogodan za trening (npr. "Alpaca" format).

Trening: Koristi transformers, peft i trl biblioteke. Učitava osnovni LLM (YugoGPT) sa 4-bitnom kvantizacijom. Definiše LoRA konfiguraciju. Pokreće SFTTrainer da trenira samo male "adapter" slojeve.

Čuvanje: Čuva istrenirane težine LoRA adaptera na definisanu putanju.

Ulaz (Input): FEEDBACK_LOG_PATH.

Izlaz (Output): Novi ili ažurirani LoRA adapter u LORA_ADAPTER_PATH.

Biblioteke: transformers, peft, trl, bitsandbytes, datasets, json, config.