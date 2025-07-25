# app.py (Verzija 2.0 - Chat Interfejs)

import streamlit as st
from rag_agent import RAGAgent
import config

# Podešavanje stranice
st.set_page_config(page_title="Drveni Advokat", layout="centered")
st.title("👨‍⚖️ Drveni Advokat")
st.markdown("---")

# --- Inicijalizacija Agenta ---
# Koristimo st.session_state da se agent ne učitava ponovo pri svakoj interakciji
if 'agent' not in st.session_state:
    with st.spinner("Inicijalizacija AI Agenta... Ovo može potrajati minut-dva."):
        try:
            st.session_state.agent = RAGAgent()
            st.success("Agent je spreman!")
        except Exception as e:
            st.error(f"Greška pri inicijalizaciji agenta: {e}")
            st.warning("Proverite da li su Qdrant i Ollama pokrenuti.")
            st.stop()

# --- Upravljanje Istorijom Razgovora ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Dobar dan! Kako vam mogu pomoći sa vašim pravnim dokumentima?"}]

# Prikaz istorije razgovora
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Polje za Unos i Logika Slanja ---
if prompt := st.chat_input("Postavite vaše pitanje..."):
    # Dodajemo poruku korisnika u istoriju i prikazujemo je
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prikazujemo poruku asistenta i spinner dok čeka odgovor
    with st.chat_message("assistant"):
        with st.spinner("Agent razmišlja..."):
            try:
                # Pozivamo našeg RAG agenta
                response = st.session_state.agent.ask(prompt)
                st.markdown(response)
            except Exception as e:
                response = f"Došlo je do greške: {e}"
                st.error(response)
    
    # Dodajemo odgovor agenta u istoriju
    st.session_state.messages.append({"role": "assistant", "content": response})