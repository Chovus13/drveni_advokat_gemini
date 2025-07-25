# rag_agent.py (Finalna verzija bez upozorenja)

import config
# IZMENA: Uvozimo QdrantVectorStore umesto Qdrant
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
# IZMENA: Uvozimo Ollama iz njenog novog, posebnog paketa
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient

def format_docs(docs):
    """Pomoćna funkcija za formatiranje konteksta i njegovo ispisivanje radi debugovanja."""
    print("\n--- KONTEKST PROSLEDJEN MODELU ---")
    if not docs:
        print("!!! NIJE PRONAĐEN NIJEDAN RELEVANTAN DOKUMENT !!!")
    for i, doc in enumerate(docs):
        print(f"--- CHUNK {i+1} [Izvor: {doc.metadata.get('source_file', 'Nepoznat')}] ---")
        print(doc.page_content)
        print("-" * 20)
    print("--- KRAJ KONTEKSTA ---\n")
    return "\n\n".join(doc.page_content for doc in docs)

class RAGAgent:
    """
    Klasa koja enkapsulira kompletnu RAG logiku.
    """
    def __init__(self):
        print("Inicijalizacija RAG Agenta...")
        
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': config.DEVICE}
        )
        
        qdrant_client = QdrantClient(url=config.QDRANT_URL)
        
        # IZMENA: Koristimo novo ime klase QdrantVectorStore
        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            embedding=self.embedding_model,
        )
        
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        # IZMENA: Inicijalizacija koristi Ollama klasu iz novog paketa
        self.llm = OllamaLLM(model=config.BASE_LLM_MODEL)
        
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
        
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        print("RAG Agent je spreman.")

    def ask(self, question: str):
        """
        Prima pitanje korisnika i vraća odgovor od RAG lanca.
        """
        print(f"Postavljeno pitanje: {question}")
        return self.rag_chain.invoke(question)

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
        print("\n--- GREŠKA ---")
        print(f"Došlo je do greške pri inicijalizaciji agenta: {e}")
        print("\nMolimo vas proverite sledeće:")
        print("1. Da li je Qdrant Docker kontejner pokrenut?")
        print("2. Da li je Ollama instalirana i pokrenuta?")
        print("3. Da li ste preuzeli YugoGPT model komandom: 'ollama run YugoGPT' ?")