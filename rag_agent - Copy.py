# rag_agent.py

import config
# from langchain_community.vectorstores import Qdrant
# IZMENA: Uvozimo Qdrant iz novog paketa
from langchain_qdrant import Qdrant
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
# IZMENA: Uvozimo HuggingFaceEmbeddings iz novog paketa
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# IZMENA: Uvozimo QdrantClient da ga prosledimo direktno
from qdrant_client import QdrantClient

class RAGAgent:
    """
    Klasa koja enkapsulira kompletnu RAG logiku.
    """
    def __init__(self):
        print("Inicijalizacija RAG Agenta...")
        
        # 1. Inicijalizacija modela za embedovanje (BERT-oliki model)
        # Ovaj model se izvršava lokalno i pretvara pitanja u vektore.
        # self.embedding_model = HuggingFaceEmbeddings(
        #     model_name=config.EMBEDDING_MODEL,
        #     model_kwargs={'device': 'cpu'} # Možete promeniti u 'cuda' ako imate NVIDIA GPU
        # )
                # IZMENA: Koristimo HuggingFaceEmbeddings iz novog paketa
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': 'cpu'}
        )
        
        # 2. Povezivanje na Qdrant bazu
        # Koristimo postojeći Qdrant klijent i našu kolekciju.
        # LangChain će koristiti embedding model da pretražuje bazu.
        # IZMENA: Prvo kreiramo Qdrant klijenta...
        qdrant_client = QdrantClient(url=config.QDRANT_URL)


        # self.vector_store = Qdrant.from_existing_collection(
        #     embedding=self.embedding_model,
        #     collection_name=config.QDRANT_COLLECTION_NAME,
        #     url=config.QDRANT_URL,
        # )
        # IZMENA: ...a zatim ga prosleđujemo LangChain Qdrant konstruktoru.
        # Ovo je novi, ispravan način za povezivanje na Qdrant server.
        self.vector_store = Qdrant(
            client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            embeddings=self.embedding_model,
        )

        # 3. Konfiguracija retriever-a
        # Retriever je komponenta koja vrši pretragu u bazi.
        # `k=5` znači da će vratiti 5 najrelevantnijih dokumenata (chunk-ova).
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        # 4. Inicijalizacija LLM-a (YugoGPT) preko Ollama
        self.llm = Ollama(model=config.BASE_LLM_MODEL)
        
        # 5. Kreiranje Prompt Template-a
        # Ovo je ključno za kontrolu ponašanja LLM-a.
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
        
        # 6. Sklapanje RAG lanca (chain)
        # Ovo je sekvenca operacija koja definiše naš RAG proces.
        self.rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
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
# Ovo vam omogućava da testirate logiku direktno iz terminala
# pre nego što napravimo Streamlit aplikaciju.
if __name__ == '__main__':
    # Provera da li je Ollama pokrenuta i da li YugoGPT postoji
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
        print("3. Da li ste preuzeli YugoGPT model komandom: 'ollama run gordicaleksa/YugoGPT' ?")