# ==============================================================================
# FAJL: app.py (Ažurirana verzija 4.1 - Dodat toggle za chunks i poboljšano logovanje)
# ==============================================================================
import os
import time
import streamlit as st
import ollama
import psutil
import json
import logging
from rag_agent import RAGAgent
import config

# Podešavanje logovanja za app.py
logging.basicConfig(
    filename='app_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Pomoćne Funkcije ---

def get_ollama_models():
    """Pribavlja listu preuzetih modela iz Ollama na robustan način."""
    logging.info("Pokušaj dobijanja Ollama modela sa hosta: %s", config.OLLAMA_HOST)
    try:
        client = ollama.Client(host=config.OLLAMA_HOST)
        models_data = client.list().get('models', [])
        models = [model['name'] for model in models_data if 'name' in model]
        logging.info("Dostupni modeli: %s", models)
        return models
    except Exception as e:
        error_msg = f"Nije moguće povezati se sa Ollama: {e}"
        logging.error(error_msg)
        st.error(error_msg + " Proverite da li je Ollama pokrenuta i da je model učitan (npr. 'ollama run mistral:7b').")
        return []

def format_context(docs):
    """Formira tekstualni prikaz konteksta za prikaz u expanderu."""
    if not docs:
        return "Nije pronađen relevantan kontekst u bazi."
    
    context_str = ""
    for i, doc in enumerate(docs):
        if isinstance(doc, str):
            source = "Nepoznat"
            content_preview = doc[:250] + "..." if len(doc) > 250 else doc
        elif isinstance(doc, dict):
            source = doc.get('metadata', {}).get('source_file', 'Nepoznat')
            content = doc.get('page_content', str(doc))
            content_preview = content[:250] + "..." if len(content) > 250 else content
        else:
            source = doc.metadata.get('source_file', 'Nepoznat') if hasattr(doc, 'metadata') else 'Nepoznat'
            if hasattr(doc, 'page_content'):
                content_preview = doc.page_content[:250] + "..." if len(doc.page_content) > 250 else doc.page_content
            else:
                content_preview = str(doc)[:250] + "..." if len(str(doc)) > 250 else str(doc)
        context_str += f"#### Izvor {i+1}: `{source}`\n> {content_preview}\n\n"
    return context_str

def format_chunks(chunks):
    """Formira prikaz chunks za expander."""
    if not chunks:
        return "Nema chunks."
    chunks_str = ""
    for i, chunk in enumerate(chunks):
        chunks_str += f"#### Chunk {i+1}\n{chunk}\n\n"
    return chunks_str

def save_config(updated_config):
    """Čuva ažuriranu konfiguraciju u dynamic_config.json i reloaduje config."""
    logging.info("Čuvanje konfiguracije.")
    with open('dynamic_config.json', 'w', encoding='utf-8') as f:
        json.dump(updated_config, f, ensure_ascii=False, indent=4)
    import importlib
    importlib.reload(config)
    logging.info("Konfiguracija reloadovana.")

# --- Podešavanje Stranice i Session State ---
st.set_page_config(page_title="Drveni Advokat", layout="wide")

if 'agent' not in st.session_state:
    st.session_state.agent = None
if "messages" not in st.session_state:
    chat_history_file = "chat_history.json"
    if os.path.exists(chat_history_file):
        try:
            with open(chat_history_file, "r", encoding="utf-8") as f:
                st.session_state.messages = json.load(f)
        except Exception as e:
            logging.error("Greška pri učitavanju chat istorije: %s", e)
            st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Došlo je do greške pri učitavanju istorije. Počinjemo novi razgovor."}]
    else:
        st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Odaberite podešavanja i inicijalizujte agenta."}]
if "selected_llm" not in st.session_state:
    st.session_state.selected_llm = config.DEFAULT_LLM_MODEL
if "selected_device" not in st.session_state:
    st.session_state.selected_device = config.DEFAULT_DEVICE
if "config_data" not in st.session_state:
    st.session_state.config_data = {k: v for k, v in vars(config).items() if not k.startswith('__')}
if "show_chunks" not in st.session_state:
    st.session_state.show_chunks = False

# --- Glavni Interfejs sa Tabovima ---
tab1, tab2, tab3 = st.tabs(["Chat", "Podešavanja", "Metadata Editor"])

with tab1:
    st.title("Drveni Advokat - RAG Sistem")
    st.checkbox("Prikaži Chunks", value=st.session_state.show_chunks, key="show_chunks_toggle")
    st.session_state.show_chunks = st.session_state.show_chunks_toggle

    # Prikaz istorije razgovora
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "context" in message:
                with st.expander("Prikaži Kontekst"):
                    st.info(format_context(message["context"]))
            if st.session_state.show_chunks and "chunks" in message:
                with st.expander("Prikaži Chunks"):
                    st.info(format_chunks(message["chunks"]))

    # Polje za unos
    if prompt := st.chat_input("Postavite vaše pitanje..."):
        if not st.session_state.agent:
            st.warning("Prvo inicijalizujte agenta.")
            logging.warning("Pokušaj slanja pitanja bez inicijalizovanog agenta.")
        else:
            logging.info("Pitanje korisnika: %s", prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                with st.status("Pretražujem bazu...", expanded=True) as status:
                    try:
                        stream, source_files, retrieved_docs = st.session_state.agent.stream_ask(prompt)
                        logging.info("Dobijeni chunks: %s", len(retrieved_docs))
                        status.update(label="Generišem odgovor...", state="running")
                        
                        for chunk in stream:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")
                        
                        if source_files:
                            sources_text = "\n\n**Korišćeni izvori:**\n" + "\n".join([f"- `{file}`" for file in source_files])
                            full_response += sources_text
                        
                        message_placeholder.markdown(full_response)
                        status.update(label="Odgovor generisan!", state="complete", expanded=False)
                        
                        message_data = {
                            "role": "assistant",
                            "content": full_response,
                            "context": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in retrieved_docs]
                        }
                        if st.session_state.show_chunks:
                            message_data["chunks"] = [doc.page_content for doc in retrieved_docs]
                        
                        st.session_state.messages.append(message_data)
                        with open("chat_history.json", "w", encoding="utf-8") as f:
                            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
                        logging.info("Odgovor sačuvan u istoriji.")
                    except Exception as e:
                        error_msg = f"Greška pri generisanju odgovora: {e}"
                        logging.error(error_msg)
                        st.error(error_msg, icon="🔥")

with tab2:
    st.header("Podešavanja Agenta i Konfiguracije")
    
    available_models = get_ollama_models()
    if available_models:
        try:
            default_index = available_models.index(st.session_state.selected_llm)
        except ValueError:
            default_index = 0
        st.session_state.selected_llm = st.selectbox(
            "Izaberite LLM Model:",
            available_models,
            index=default_index
        )
    else:
        st.warning("Nema dostupnih Ollama modela. Proverite logove.")

    st.session_state.selected_device = st.selectbox(
        "Uređaj za Embedding:",
        ("cpu", "cuda"),
        index=0 if st.session_state.selected_device == "cpu" else 1
    )

    if st.button("Inicijalizuj Agenta", type="primary"):
        with st.spinner(f"Inicijalizacija sa modelom '{st.session_state.selected_llm}' na '{st.session_state.selected_device.upper()}'..."):
            logging.info("Pokušaj inicijalizacije agenta sa modelom %s na %s", st.session_state.selected_llm, st.session_state.selected_device)
            try:
                st.session_state.agent = RAGAgent(
                    llm_model=st.session_state.selected_llm,
                    embedding_model=config.DEFAULT_EMBEDDING_MODEL,
                    device=st.session_state.selected_device
                )
                st.success("Agent uspešno inicijalizovan!")
                logging.info("Agent uspešno inicijalizovan.")
                st.session_state.messages = [{"role": "assistant", "content": "Agent je spreman. Kako vam mogu pomoći?"}]
                st.rerun()
            except Exception as e:
                error_msg = f"Greška pri inicijalizaciji: {e}"
                logging.error(error_msg)
                st.error(error_msg)

    # Auto-start
    if st.session_state.agent is None and available_models:
        with st.spinner("Automatska inicijalizacija..."):
            logging.info("Automatska inicijalizacija agenta.")
            try:
                st.session_state.agent = RAGAgent(
                    llm_model=st.session_state.selected_llm,
                    embedding_model=config.DEFAULT_EMBEDDING_MODEL,
                    device=st.session_state.selected_device
                )
                st.success("Agent automatski inicijalizovan!")
                logging.info("Agent automatski inicijalizovan.")
                st.session_state.messages = [{"role": "assistant", "content": "Agent je spreman."}]
                st.rerun()
            except Exception as e:
                error_msg = f"Greška pri automatskoj inicijalizaciji: {e}"
                logging.error(error_msg)
                st.error(error_msg)
                st.session_state.agent = None

    st.subheader("Ostala Podešavanja")
    updated_config = st.session_state.config_data.copy()
    updated_config['SOURCE_DOC_DIR'] = st.text_input("Source Doc Dir", value=config.SOURCE_DOC_DIR)
    updated_config['CONVERTED_DOCX_DIR'] = st.text_input("Converted Docx Dir", value=config.CONVERTED_DOCX_DIR)
    updated_config['STRUCTURED_JSONL_PATH'] = st.text_input("Structured JSONL Path", value=config.STRUCTURED_JSONL_PATH)
    updated_config['FEEDBACK_LOG_PATH'] = st.text_input("Feedback Log Path", value=config.FEEDBACK_LOG_PATH)
    updated_config['DEFAULT_LLM_MODEL'] = st.text_input("Default LLM Model", value=config.DEFAULT_LLM_MODEL)
    updated_config['DEFAULT_EMBEDDING_MODEL'] = st.text_input("Default Embedding Model", value=config.DEFAULT_EMBEDDING_MODEL)
    updated_config['DEFAULT_DEVICE'] = st.text_input("Default Device", value=config.DEFAULT_DEVICE)
    updated_config['OLLAMA_HOST'] = st.text_input("Ollama Host", value=config.OLLAMA_HOST)
    updated_config['VECTOR_DIMENSION'] = st.number_input("Vector Dimension", value=config.VECTOR_DIMENSION)
    updated_config['DISTANCE_METRIC'] = st.text_input("Distance Metric", value=config.DISTANCE_METRIC)
    updated_config['BATCH_SIZE'] = st.number_input("Batch Size", value=config.BATCH_SIZE)
    updated_config['QDRANT_URL'] = st.text_input("Qdrant URL", value=config.QDRANT_URL)
    updated_config['QDRANT_COLLECTION_NAME'] = st.text_input("Qdrant Collection Name", value=config.QDRANT_COLLECTION_NAME)
    updated_config['REMOVE_HEADERS_FOOTERS'] = st.checkbox("Remove Headers/Footers", value=config.REMOVE_HEADERS_FOOTERS)
    updated_config['BOILERPLATE_PHRASES_TO_REMOVE'] = st.text_area("Boilerplate Phrases (one per line)", value="\n".join(config.BOILERPLATE_PHRASES_TO_REMOVE)).split("\n")

    if st.button("Sačuvaj Podešavanja"):
        save_config(updated_config)
        st.session_state.config_data = updated_config
        st.success("Podešavanja sačuvana i primenjena!")
        logging.info("Podešavanja sačuvana.")

with tab3:
    st.header("Metadata Editor")
    metadata = config.METADATA_CATEGORIES.copy()
    
    category = st.selectbox("Izaberite Kategoriju", list(metadata.keys()) + ["Dodaj Novu Kategoriju"])
    
    if category == "Dodaj Novu Kategoriju":
        new_category = st.text_input("Naziv Nove Kategorije")
        if st.button("Dodaj Kategoriju") and new_category:
            metadata[new_category] = {}
            save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
            st.success(f"Dodata kategorija: {new_category}")
            st.rerun()
    else:
        if st.button("Obriši Kategoriju"):
            del metadata[category]
            save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
            st.success(f"Obrisana kategorija: {category}")
            st.rerun()
        
        subcategory = st.selectbox("Izaberite Podkategoriju", list(metadata[category].keys()) + ["Dodaj Novu Podkategoriju"])
        
        if subcategory == "Dodaj Novu Podkategoriju":
            new_sub = st.text_input("Naziv Nove Podkategorije")
            if st.button("Dodaj Podkategoriju") and new_sub:
                metadata[category][new_sub] = []
                save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
                st.success(f"Dodata podkategorija: {new_sub}")
                st.rerun()
        else:
            if st.button("Obriši Podkategoriju"):
                del metadata[category][subcategory]
                save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
                st.success(f"Obrisana podkategorija: {subcategory}")
                st.rerun()
            
            st.subheader(f"Vrednosti za {subcategory}")
            values = metadata[category][subcategory]
            for i, val in enumerate(values):
                new_val = st.text_input(f"Vrednost {i+1}", value=val, key=f"val_{category}_{subcategory}_{i}")
                if new_val != val:
                    values[i] = new_val
            
            if st.button("Sačuvaj Promene Vrednosti"):
                metadata[category][subcategory] = [v for v in values if v]
                save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
                st.success("Vrednosti ažurirane!")
            
            new_value = st.text_input("Dodaj Novu Vrednost")
            if st.button("Dodaj Vrednost") and new_value:
                values.append(new_value)
                metadata[category][subcategory] = values
                save_config({**st.session_state.config_data, 'METADATA_CATEGORIES': metadata})
                st.success(f"Dodata vrednost: {new_value}")
                st.rerun()

# Status Sistema u Sidebaru
with st.sidebar:
    st.subheader("Status Sistema")
    cpu_usage = st.empty()
    ram_usage = st.empty()
    while True:
        cpu_usage.metric("CPU Zauzeće", f"{psutil.cpu_percent()}%")
        ram_usage.metric("RAM Zauzeće", f"{psutil.virtual_memory().percent}%")
        time.sleep(1)
