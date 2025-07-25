# ==============================================================================
# FAJL: app.py (Ažurirana verzija 3.1 - Ispravka za Ollama)
# ==============================================================================

import os
import streamlit as st
import ollama
import psutil
import time
from rag_agent import RAGAgent
import config

# --- Pomoćne Funkcije ---

def get_ollama_models():
    """Pribavlja listu preuzetih modela iz Ollama na robustan način."""
    try:
        models_data = ollama.list().get('models', [])
        print(f"DEBUG: Raw Ollama models data: {models_data}")  # Debug output
        # Filtriramo samo modele koji imaju 'name' ključ da bismo izbegli greške
        models = [model['name'] for model in models_data if 'name' in model]
        print(f"DEBUG: Extracted model names: {models}")  # Debug output
        return models
    except Exception as e:
        print(f"DEBUG: Error getting Ollama models: {e}")  # Debug output
        st.error(f"Nije moguće povezati se sa Ollama: {e}")
        return []

def format_context(docs):
    """Formira tekstualni prikaz konteksta za prikaz u expanderu."""
    if not docs:
        return "Nije pronađen relevantan kontekst u bazi."
    
    context_str = ""
    for i, doc in enumerate(docs):
        source = doc.metadata.get('source_file', 'Nepoznat')
        content_preview = doc.page_content[:250] + "..."
        context_str += f"#### Izvor {i+1}: `{source}`\n"
        context_str += f"> {content_preview}\n\n"
    return context_str

# --- Podešavanje Stranice i Session State ---
st.set_page_config(page_title="Drveni Advokat", layout="wide")

if 'agent' not in st.session_state:
    st.session_state.agent = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Molim vas odaberite podešavanja u meniju sa leve strane i kliknite na 'Inicijalizuj Agenta'."}]
if "selected_llm" not in st.session_state:
    st.session_state.selected_llm = config.DEFAULT_LLM_MODEL
if "selected_device" not in st.session_state:
    st.session_state.selected_device = config.DEFAULT_DEVICE

# --- Sidebar (Meni sa strane) ---
with st.sidebar:
    st.header("👨‍⚖️ Drveni Advokat")
    st.markdown("---")
    
    st.subheader("Podešavanja Agenta")
    
    # Dinamički izbor LLM modela
    available_models = get_ollama_models()
    if available_models:
        # Pokušavamo da nađemo podrazumevani model u listi, ako ne postoji, uzimamo prvi
        try:
            default_index = available_models.index(st.session_state.selected_llm)
        except ValueError:
            default_index = 0
        
        selected_llm = st.selectbox(
            "Izaberite LLM Model:",
            available_models,
            index=default_index
        )
        st.session_state.selected_llm = selected_llm
    else:
        st.warning("Nema dostupnih Ollama modela. Proverite da li je Ollama pokrenuta.")

    # Izbor uređaja
    selected_device = st.selectbox(
        "Uređaj za Embedding:",
        ("cpu", "cuda"),
        index=0 if st.session_state.selected_device == "cpu" else 1
    )
    st.session_state.selected_device = selected_device

    # Dugme za inicijalizaciju/re-inicijalizaciju agenta
    if st.button("Inicijalizuj Agenta", type="primary"):
        with st.spinner(f"Inicijalizacija sa modelom '{st.session_state.selected_llm}' na '{st.session_state.selected_device.upper()}'..."):
            try:
                st.session_state.agent = RAGAgent(
                    llm_model=st.session_state.selected_llm,
                    embedding_model=config.DEFAULT_EMBEDDING_MODEL,
                    device=st.session_state.selected_device
                )
                st.success("Agent je uspešno inicijalizovan!", icon="✅")
                # Resetujemo chat pri promeni agenta
                st.session_state.messages = [{"role": "assistant", "content": "Agent je spreman. Kako vam mogu pomoći?"}]
                st.rerun() # Ponovo pokrećemo skriptu da se osveži interfejs
            except Exception as e:
                st.error(f"Greška pri inicijalizaciji: {e}", icon="🔥")

    st.markdown("---")
    st.subheader("Status Sistema")
    
    # Prikaz sistemskih resursa
    cpu_usage = st.empty()
    ram_usage = st.empty()
    
# --- Glavni Interfejs ---
st.title("Drveni Advokat - RAG Sistem")

# Prikaz istorije razgovora
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "context" in message:
            with st.expander("Prikaži Kontekst Korišćen za Odgovor"):
                st.info(format_context(message["context"]))

# Polje za unos
if prompt := st.chat_input("Postavite vaše pitanje..."):
    if not st.session_state.agent:
        st.warning("Molimo vas da prvo inicijalizujete agenta u meniju sa leve strane.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Prikaz "Thinking" koraka
            with st.status("Pretražujem bazu znanja...", expanded=True) as status:
                try:
                    # Strimujemo odgovor
                    stream, source_docs = st.session_state.agent.stream_ask(prompt)
                    status.update(label="Pronađen kontekst. Generišem odgovor...", state="running")
                    
                    for chunk in stream:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌") # Kursor efekat
                    message_placeholder.markdown(full_response)
                    
                    # Dodajemo izvore na kraj
                    if source_docs:
                        sources_text = "\n\n**Korišćeni izvori:**\n" + "\n".join([f"- `{file}`" for file in source_docs])
                        full_response += sources_text
                        message_placeholder.markdown(full_response)
                        
                    status.update(label="Odgovor generisan!", state="complete", expanded=False)
                    
                    # Čuvamo odgovor i kontekst u istoriji
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "context": source_docs
                    })

                except Exception as e:
                    st.error(f"Došlo je do greške: {e}", icon="🔥")

# Petlja za osvežavanje statusa sistema
while True:
    cpu_usage.metric(label="CPU Zauzeće", value=f"{psutil.cpu_percent()}%")
    ram_usage.metric(label="RAM Zauzeće", value=f"{psutil.virtual_memory().percent}%")
    time.sleep(1) # Osvežava se svake sekunde