# rag_agent.py (Verzija sa alatkama za debugovanje)

import config
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient

def format_docs(docs):
    """Pomoćna funkcija za formatiranje konteksta i njegovo ispisivanje radi debugovanja."""
    print("\n=== DEBUG: KONTEKST PROSLEDJEN MODELU ===")
    print(f"DEBUG: Broj pronađenih dokumenata: {len(docs)}")
    
    if not docs:
        print("!!! NIJE PRONAĐEN NIJEDAN RELEVANTAN DOKUMENT !!!")
        return ""
    
    for i, doc in enumerate(docs):
        source_file = doc.metadata.get('source_file', 'Nepoznat')
        print(f"--- CHUNK {i+1} [Izvor: {source_file}] ---")
        print(f"DEBUG: Metadata: {doc.metadata}")
        print(f"DEBUG: Content length: {len(doc.page_content)} characters")
        print(f"Content preview: {doc.page_content[:200]}...")
        print("-" * 50)
    
    print("=== KRAJ KONTEKSTA ===\n")
    return "\n\n".join(doc.page_content for doc in docs)

class RAGAgent:
    def __init__(self, llm_model=None, embedding_model=None, device=None):
        print("Inicijalizacija RAG Agenta...")
        
        # Use provided parameters or fall back to config defaults
        self.llm_model = llm_model or config.DEFAULT_LLM_MODEL
        self.embedding_model_name = embedding_model or config.DEFAULT_EMBEDDING_MODEL
        self.device = device or config.DEFAULT_DEVICE
        
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': self.device}
        )
        qdrant_client = QdrantClient(url=config.QDRANT_URL)
        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            embedding=self.embedding_model,
        )
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        self.llm = OllamaLLM(model=self.llm_model)
        template = """
Vi ste 'Drveni advokat', AI asistent specijalizovan za pravna pitanja u Srbiji. 
Vaš zadatak je da odgovorite na pitanje korisnika isključivo na osnovu sledećeg konteksta iz pravnih dokumenata.
Budite precizni i držite se informacija iz priloženog teksta.
Ako odgovor nije u datom kontekstu, recite tačno: 'Na osnovu dostupnih informacija, nemam odgovor na vaše pitanje.'
Nakon svakog dela odgovora, obavezno navedite izvor u formatu [Izvor: source_file].

Kontekst:
{context}

Pitanje:
{question}

Konačan odgovor na srpskom jeziku:
"""
        self.prompt = PromptTemplate.from_template(template)
        
        # RAG lanac sada uključuje našu funkciju za ispis konteksta
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        print("RAG Agent je spreman.")

    def ask(self, question: str):
        print(f"\n=== DEBUG: ASK POZVAN ===")
        print(f"DEBUG: Pitanje: {question}")
        print(f"DEBUG: LLM model: {self.llm_model}")
        
        try:
            # Test retriever directly first
            print("DEBUG: Testiram retriever direktno...")
            docs = self.retriever.invoke(question)
            print(f"DEBUG: Retriever vratio {len(docs)} dokumenata")
            
            if docs:
                for i, doc in enumerate(docs):
                    print(f"DEBUG: Doc {i+1} - Source: {doc.metadata.get('source_file', 'N/A')}")
                    print(f"DEBUG: Doc {i+1} - Content preview: {doc.page_content[:100]}...")
            
            print("DEBUG: Pozivam RAG chain...")
            result = self.rag_chain.invoke(question)
            print(f"DEBUG: RAG chain vratio odgovor dužine: {len(result)} karaktera")
            return result
            
        except Exception as e:
            print(f"DEBUG: Greška u ask metodi: {e}")
            import traceback
            traceback.print_exc()
            return f"Greška pri obradi pitanja: {e}"
    
    def stream_ask(self, question: str):
        """Stream response and return source documents for Streamlit app."""
        print(f"\n=== DEBUG: STREAM_ASK POZVAN ===")
        print(f"DEBUG: Pitanje: {question}")
        print(f"DEBUG: LLM model: {self.llm_model}")
        print(f"DEBUG: Embedding model: {self.embedding_model_name}")
        print(f"DEBUG: Device: {self.device}")
        
        try:
            # Get relevant documents
            print("DEBUG: Pozivam retriever...")
            docs = self.retriever.invoke(question)
            print(f"DEBUG: Retriever vratio {len(docs)} dokumenata")
            
            # Extract source files for display
            source_files = list(set([doc.metadata.get('source_file', 'Nepoznat') for doc in docs]))
            print(f"DEBUG: Source files: {source_files}")
            
            # Format context
            print("DEBUG: Formatiram kontekst...")
            context = format_docs(docs)
            print(f"DEBUG: Formatiran kontekst dužine: {len(context)} karaktera")
            
            # Create prompt
            prompt_text = self.prompt.format(context=context, question=question)
            print(f"DEBUG: Kreiran prompt dužine: {len(prompt_text)} karaktera")
            print(f"DEBUG: Prompt preview: {prompt_text[:300]}...")
            
            # Stream the response
            def response_generator():
                try:
                    print("DEBUG: Počinje streaming odgovora...")
                    # For OllamaLLM, we need to use the stream method
                    for chunk in self.llm.stream(prompt_text):
                        print(f"DEBUG: Chunk received: {chunk[:50]}...")
                        yield chunk
                    print("DEBUG: Streaming završen")
                except Exception as e:
                    error_msg = f"Greška pri generisanju odgovora: {e}"
                    print(f"DEBUG: {error_msg}")
                    yield error_msg
            
            return response_generator(), source_files
            
        except Exception as e:
            print(f"DEBUG: Greška u stream_ask: {e}")
            import traceback
            traceback.print_exc()
            
            def error_generator():
                yield f"Greška pri obradi pitanja: {e}"
            
            return error_generator(), []

# --- Blok za testiranje ---
if __name__ == '__main__':
    try:
        agent = RAGAgent()
        print("\n--- Testiranje RAG Agenta ---")
        print("Unesite vaše pitanje (ili 'izlaz' za prekid).")
        while True:
            user_question = input("Pitanje: ")
            if user_question.lower() == 'izlaz':
                break
            answer = agent.ask(user_question)
            print("\nOdgovor Agenta:")
            print(answer)
            print("-" * 50)
    except Exception as e:
        print(f"\n--- GREŠKA ---: {e}")


# # --- BLOK ZA TESTIRANJE IZ KOMANDNE LINIJE ---
# # Ovaj deo ti omogućava da pokreneš `python rag_agent.py` i testiraš ga.
# if __name__ == "__main__":
#     print("Pokrenut RAG agent u test modu (koristi se Ollama)...")
    
#     # Inicijalizacija za testiranje
#     # Ako želiš da testiraš Gemini, samo promeni "OllamaLLM" u "Gemini"
#     test_model = "OllamaLLM"
    
#     chat_history = []

#     while True:
#         query = input("\nPostavite pitanje (ili 'exit' za izlaz): ")
#         if query.lower() == 'exit':
#             break
        
#         # Simulacija istorije za testiranje
#         # U pravoj aplikaciji, ovo se upravlja preko session_state
#         formatted_history = []
#         for i, msg in enumerate(chat_history):
#             if i % 2 == 0:
#                 formatted_history.append({'role': 'user', 'content': msg.content})
#             else:
#                 formatted_history.append({'role': 'assistant', 'content': msg.content})

#         result = get_rag_response(query, formatted_history, test_model)
        
#         print("\nOdgovor:", result)
        
#         # Dodavanje u istoriju za sledeći krug
#         chat_history.append(HumanMessage(content=query))
#         chat_history.append(AIMessage(content=result))