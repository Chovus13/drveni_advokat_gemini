# ==============================================================================
# FAJL: rag_agent.py (Ažurirana verzija 4.0 - Dodato robustno logovanje i formatiranje konteksta)
# ==============================================================================
import os
import config
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from qdrant_client import QdrantClient
import logging

# Podešavanje logovanja
logging.basicConfig(
    filename='rag_agent_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_docs(docs):
    """Formatira dokumente u string i loguje ih za debug."""
    if not docs:
        logging.warning("Nema pronađenih dokumenata za kontekst.")
        return ""
    formatted = "\n\n".join(doc.page_content for doc in docs)
    logging.debug("Formatirani kontekst:\n%s", formatted)
    return formatted

class RAGAgent:
    def __init__(self, llm_model: str, embedding_model: str, device: str):
        logging.info("Inicijalizacija RAG Agenta sa LLM: %s, Embedding: %s, Uređaj: %s", llm_model, embedding_model, device)
        print(f"Inicijalizacija RAG Agenta sa LLM: {llm_model}, Embedding: {embedding_model}, Uređaj: {device}")
        
        try:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': device}
            )
            logging.info("Embedding model uspešno inicijalizovan.")
        except Exception as e:
            logging.error("Greška pri inicijalizaciji embedding modela: %s", e)
            raise
        
        try:
            qdrant_client = QdrantClient(url=config.QDRANT_URL)
            logging.info("Qdrant klijent uspešno povezan.")
        except Exception as e:
            logging.error("Greška pri povezivanju sa Qdrant: %s", e)
            raise
        
        try:
            self.vector_store = QdrantVectorStore(
                client=qdrant_client,
                collection_name=config.QDRANT_COLLECTION_NAME,
                embedding=self.embedding_model,
            )
            logging.info("Vector store uspešno inicijalizovan.")
        except Exception as e:
            logging.error("Greška pri inicijalizaciji vector store: %s", e)
            raise
        
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        self.lora_path = "models/drveni_advokat_lora"
        try:
            if os.path.exists(self.lora_path):
                self.llm = AutoModelForSeq2SeqLM.from_pretrained(self.lora_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.lora_path)
                logging.info("LoRA fine-tuned model loaded successfully.")
            else:
                self.llm = OllamaLLM(model=llm_model, base_url=config.OLLAMA_HOST)
                test_response = self.llm.invoke("Test")
                logging.info("OllamaLLM uspešno inicijalizovan i testiran sa modelom %s. Test odgovor: %s", llm_model, test_response)
        except Exception as e:
            logging.error("Greška pri inicijalizaciji ili testiranju LLM: %s", e)
            raise
        
        template = """
Vi ste 'Drveni advokat', AI asistent specijalizovan za pravna pitanja u Srbiji. 
Odgovorite na pitanje ISKLJUČIVO na osnovu sledećeg konteksta iz lokalnih dokumenata. Ne koristite spoljašnje znanje ili linkove.
Budite precizni, koncizni i držite se samo pruženih informacija.
Ako informacije nisu u kontekstu, recite: 'Na osnovu dostupnih informacija, nemam odgovor na vaše pitanje.'
Navedite izvore na kraju.

Kontekst: {context}

Pitanje: {question}

Odgovor:
"""
        self.prompt = PromptTemplate.from_template(template)
        
        self.rag_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        logging.info("RAG lanac uspešno inicijalizovan.")
        print("RAG Agent je spreman.")

    def update_with_lora(self):
        if os.path.exists(self.lora_path):
            self.llm = AutoModelForSeq2SeqLM.from_pretrained(self.lora_path)
            self.tokenizer = AutoTokenizer.from_pretrained(self.lora_path)
            logging.info("Model updated with LoRA adapter.")
        else:
            logging.warning("LoRA model not found, skipping update.")

    def ask(self, question: str):
        logging.info("Postavljeno pitanje: %s", question)
        try:
            response = self.rag_chain.invoke(question)
            logging.info("Odgovor generisan: %s", response)
            return response
        except Exception as e:
            logging.error("Greška pri generisanju odgovora: %s", e)
            raise

    def stream_ask(self, question: str):
        logging.info("Stream pitanje: %s", question)
        try:
            retrieved_docs = self.retriever.invoke(question)
            formatted_context = format_docs(retrieved_docs)
            source_files = list({doc.metadata.get('source_file', 'Nepoznat') for doc in retrieved_docs})
            
            generation_chain = self.prompt | self.llm | StrOutputParser()
            
            logging.info("Kontekst dobijen za stream pitanje.")
            return generation_chain.stream({"context": formatted_context, "question": question}), source_files, retrieved_docs
        except Exception as e:
            logging.error("Greška pri stream_ask: %s", e)
            raise

#--- Blok za testiranje ---
if __name__ == '__main__':
    try:
        agent = RAGAgent(llm_model=config.DEFAULT_LLM_MODEL, embedding_model=config.DEFAULT_EMBEDDING_MODEL, device=config.DEFAULT_DEVICE)
        print("\n--- Testiranje RAG Agenta ---")
        while True:
            user_question = input("Pitanje (ili 'izlaz'): ")
            if user_question.lower() == 'izlaz':
                break
            stream, sources, docs = agent.stream_ask(user_question)
            print("\nOdgovor:")
            for chunk in stream:
                print(chunk, end='', flush=True)
            print("\n\nIzvori:", sources)
            print("\nChunks:", [doc.page_content for doc in docs])
    except Exception as e:
        logging.error("Greška u testiranju: %s", e)
        print(f"Greška: {e}")
