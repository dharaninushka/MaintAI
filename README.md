# MaintAI

A RAG-based assistant for querying equipment maintenance SOPs in natural language.

## Stack
Python, LangChain, Google Gemini API, FAISS, Streamlit, HuggingFace Instructor Embeddings

## Status
RAG retrieval pipeline working — ingests SOP PDFs, answers technician questions grounded in the actual documentation. Ticket-logging automation (REST API integration) in progress.

## Setup
1. `pip install -r requirements.txt`
2. Add `GOOGLE_API_KEY` to `.env`
3. `streamlit run app.py`
