# app.py (Verzija 2.1 - Kontrolni Panel)

import streamlit as st
from rag_agent import RAGAgent
import config

# --- Podešavanje stranice ---
st.set_page_config(page_title="Drveni Advokat", layout="wide")

# --- Sidebar sa Konfiguracijom ---
with st.sidebar:
    st.header("👨‍⚖️ Drveni Advokat")
    st.markdown("---")
    st.subheader("Status Sistema")
    # Prikaz aktivnih modela iz config.py
    st.info(f"**Aktivni LLM:**\n`{config.BASE_LLM_MODEL}`")
    st.info(f"**Aktivni Embedding Model:**\n`{config.EMBEDDING_MODEL_NAME}`")
    st.info(f"**Uređaj za embedding:** `{config.DEVICE.upper()}`")
    st.markdown("---")
    # TODO: Dodati prikaz CPU/RAM zauzeća sa psutil

# --- Glavni Interfejs ---
st.title("Drveni Advokat - RAG Sistem")
st.markdown("Postavite pitanje vezano za pravne dokumente koji su indeksirani u bazi.")

# --- Inicijalizacija Agenta ---
if 'agent' not in st.session_state:
    with st.spinner("Inicijalizacija AI Agenta... Ovo može potrajati."):
        try:
            st.session_state.agent = RAGAgent()
            st.success("Agent je spreman!", icon="✅")
        except Exception as e:
            st.error(f"Greška pri inicijalizaciji agenta: {e}", icon="🔥")
            st.warning("Proverite da li su Qdrant i Ollama pokrenuti.")
            st.stop()

# --- Upravljanje Istorijom Razgovora ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Spreman sam za analizu vaših pravnih predmeta."}]

# Prikaz istorije
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Prikaz konteksta ako postoji
        if "context" in message:
            with st.expander("Prikaži Kontekst Korišćen za Odgovor"):
                st.info(message["context"])

# --- Polje za Unos ---
if prompt := st.chat_input("Postavite vaše pitanje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analiziram dokumente i sastavljam odgovor..."):
            try:
                # Modifikujemo RAG agenta da vraća i odgovor i kontekst
                # (Ovo zahteva malu izmenu u rag_agent.py)
                response = st.session_state.agent.ask(prompt)
                
                # Privremeno rešenje dok ne izmenimo rag_agent.py:
                # Kontekst ćemo izvući ponovnim pozivom retrievera
                retrieved_docs = st.session_state.agent.retriever.invoke(prompt)
                context_text = "\n\n---\n\n".join([doc.page_content for doc in retrieved_docs])
                
                st.markdown(response)
                
                # Čuvamo odgovor i kontekst u istoriji
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "context": context_text # Čuvamo kontekst
                })
                
            except Exception as e:
                st.error(f"Došlo je do greške: {e}", icon="🔥")