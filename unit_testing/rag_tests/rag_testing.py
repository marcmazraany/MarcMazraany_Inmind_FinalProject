import os, json, time, datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from google import genai
from rag import run_rag_for_question, load_index

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

log_path = "unit_testing/rag_logs.txt"
model = "gemini-2.0-flash"
DB_DIR = "data/rag_documents/faiss_index"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
client = genai.Client(api_key=GOOGLE_API_KEY)

questions = [
    "What were the key results and decision for EX-2025-03-01 — Chatbot Intent Expansion?",
    "What was the outcome of the Ads Landing Page Headline test (A1 LP v5)?",
    "Summarize the Pro Plan +5% Price Test (D1): ARPU, conversion, churn, and decision.",
    "How is Contribution Margin % (CM%) defined and calculated?",
    "What is Cost to Serve (CtS) and its formula?",
    "Define 'active customer', 'new customer', and 'churned customer' at monthly granularity."
]

test_answers = {
    questions[0]: "Tickets per 1k active: -7.1% (95% CI -11.8% to -2.5%); CtS: -$0.22; NPS: +0.1 (neutral). Decision: Ship.",
    questions[1]: "CVR +9.3% (p=0.01); CPC flat; cost per new customer -$11. Decision: Scale.",
    questions[2]: "ARPU +3.2%; conversion -1.1 pp (not significant); churn neutral (30-day). Decision: Hold (+5% kept in EU/NA; monitor cohorts).",
    questions[3]: "CM% = (MRR - VariableCosts) / MRR, where VariableCosts = payment_fees + infra_cost + support_cost (payment fees baseline 2.5% of MRR).",
    questions[4]: "CtS is the monthly variable cost per active customer: CtS = total_variable_cost / active_customers.",
    questions[5]: "Active: paying subscriber counted at end of month. New: first active month is the given month. Churned: subscription ends in the month (non-reactivated)."
}

def write_log_row(path, row_dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row_dict, ensure_ascii=False) + "\n")

db = load_index(db_dir=DB_DIR, embeddings=HuggingFaceEmbeddings(model_name=EMBED_MODEL))
retriever = db.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": 0.5}
    )


for question in questions:
    result = run_rag_for_question(client, retriever, question, model)
    log_row = {
        "question": question,
        "context": result["context"],
        "rag answer": result["answer"],
        "gpt5 answer": test_answers[question]
    }
    write_log_row(log_path, log_row)