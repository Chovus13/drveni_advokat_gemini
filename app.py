# ==============================================================================
# FAJL: app.py (Ažurirana verzija 3.1 - Ispravka za Ollama)
# ==============================================================================

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
        # Filtriramo samo modele koji imaju 'name' ključ da bismo izbegli greške
        return [model['name'] for model in models_data if 'name' in model]
    except Exception as e:
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



# # app.py (Verzija 2.1 - Kontrolni Panel)

# import streamlit as st
# from rag_agent import RAGAgent
# import config

# # --- Podešavanje stranice ---
# st.set_page_config(page_title="Drveni Advokat", layout="wide")

# # --- Sidebar sa Konfiguracijom ---
# with st.sidebar:
#     st.header("👨‍⚖️ Drveni Advokat")
#     st.markdown("---")
#     st.subheader("Status Sistema")
#     # Prikaz aktivnih modela iz config.py
#     st.info(f"**Aktivni LLM:**\n`{config.BASE_LLM_MODEL}`")
#     st.info(f"**Aktivni Embedding Model:**\n`{config.EMBEDDING_MODEL_NAME}`")
#     st.info(f"**Uređaj za embedding:** `{config.DEVICE.upper()}`")
#     st.markdown("---")
#     # TODO: Dodati prikaz CPU/RAM zauzeća sa psutil

# # --- Glavni Interfejs ---
# st.title("Drveni Advokat - RAG Sistem")
# st.markdown("Postavite pitanje vezano za pravne dokumente koji su indeksirani u bazi.")

# # --- Inicijalizacija Agenta ---
# if 'agent' not in st.session_state:
#     with st.spinner("Inicijalizacija AI Agenta... Ovo može potrajati."):
#         try:
#             st.session_state.agent = RAGAgent()
#             st.success("Agent je spreman!", icon="✅")
#         except Exception as e:
#             st.error(f"Greška pri inicijalizaciji agenta: {e}", icon="🔥")
#             st.warning("Proverite da li su Qdrant i Ollama pokrenuti.")
#             st.stop()

# # --- Upravljanje Istorijom Razgovora ---
# if "messages" not in st.session_state:
#     st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Spreman sam za analizu vaših pravnih predmeta."}]

# # Prikaz istorije
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])
#         # Prikaz konteksta ako postoji
#         if "context" in message:
#             with st.expander("Prikaži Kontekst Korišćen za Odgovor"):
#                 st.info(message["context"])

# # --- Polje za Unos ---
# if prompt := st.chat_input("Postavite vaše pitanje..."):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         with st.spinner("Analiziram dokumente i sastavljam odgovor..."):
#             try:
#                 # Modifikujemo RAG agenta da vraća i odgovor i kontekst
#                 # (Ovo zahteva malu izmenu u rag_agent.py)
#                 response = st.session_state.agent.ask(prompt)
                
#                 # Privremeno rešenje dok ne izmenimo rag_agent.py:
#                 # Kontekst ćemo izvući ponovnim pozivom retrievera
#                 retrieved_docs = st.session_state.agent.retriever.invoke(prompt)
#                 context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
                
#                 st.markdown(response)
                
#                 # Čuvamo odgovor i kontekst u istoriji
#                 st.session_state.messages.append({
#                     "role": "assistant",
#                     "content": response,
#                     "context": context_text # Čuvamo kontekst
#                 })
                
#             except Exception as e:
#                 st.error(f"Došlo je do greške: {e}", icon="🔥")