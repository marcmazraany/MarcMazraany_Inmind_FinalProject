from langchain_community.document_loaders import DirectoryLoader
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from google import genai
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


with open('data/company_data/kpi_handbook.md', 'r', encoding="utf-8", errors="replace") as file:
  dataset = file.readlines()
  print(f'Loaded {len(dataset)} entries')

model = "gemma-3-270m-it"
OLLAMA_BASE_URL = "http://localhost:11434"
directories = "data/rag_documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 25
embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
db_dir = "data/rag_documents/faiss_index"

def load_markdown(root: str):
  loader = DirectoryLoader(
    root,
    glob="**/*.md",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8", "autodetect_encoding": True},
    show_progress=True,
    use_multithreading=True,
    max_concurrency=8,
  )
  return loader.load()

def load_index(db_dir: str = db_dir, embeddings: HuggingFaceEmbeddings = embeddings):
    db = FAISS.load_local(db_dir, embeddings, allow_dangerous_deserialization=True)
    return db

def run_rag_for_question(client, retriever, question, model):
    retrieved = retriever.get_relevant_documents(question)
    context = "\n\n".join([d.page_content for d in retrieved])
    if not context:
        return {"context": "", "answer": "I don't know."}
    prompt = (
        "You are a helpful assistant. Use ONLY the context to answer.\n"
        "If the answer isn't in the context, say you don't know.\n"
        "Cite sources as [#] with the source filename.\n"
        "Context:\n" + context + "\n"
        "Question: " + question + "\n"
        "Answer:"
    )
    resp = client.models.generate_content(
        model=model,
        contents=prompt
    )
    text = getattr(resp, "text", "")
    return {
        "context": context,
        "answer": text.strip()
    }

docs = load_markdown(directories)
text_splitter = RecursiveCharacterTextSplitter(
  chunk_size=CHUNK_SIZE,
  chunk_overlap=CHUNK_OVERLAP
  )

chunks = text_splitter.split_documents(docs)

db = FAISS.from_documents(chunks, embeddings)
db.save_local(db_dir)

retriever = db.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={'score_threshold': 0.5}
            )

query = "Define what cost to serve is?"
retrieved_docs = retriever.get_relevant_documents(query)

# for i, doc in enumerate(retrieved_docs):
#   print(f"\n\nDOC: [{i}] {doc.page_content[:100]}...")

context = "\n\n".join([doc.page_content for doc in retrieved_docs])

prompt = f"""You are a helpful assistant. Use ONLY the context to answer.
            If the answer isn't in the context, say you don't know.
            Cite sources as [#] with the source filename.
            Context:
            {context}
            Question: {query}
            Answer:"""

client = genai.Client(api_key=GOOGLE_API_KEY)
response = client.models.generate_content(
    model="gemini-2.0-flash", contents=prompt
)
print("gemini response: ",response.text)

# client_lm = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")
# resp = client_lm.chat.completions.create(
#     model="lmstudio-community/gemma-3-270m-it-GGUF",  
#     messages=[{"role":"user", "content":prompt}],
#     temperature=0.2
# )
# print("local llm response: ", resp.choices[0].message.content)

