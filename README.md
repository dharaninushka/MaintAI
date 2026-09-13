# MaintAI — LangChain RAG Assistant for Equipment Maintenance SOPs

An AI assistant for factory floor technicians. Instead of digging through
PDF manuals mid-repair, a technician asks a question in plain English and
gets an answer grounded in the actual equipment SOPs — and if their message
signals an unresolved issue, the system automatically logs a maintenance
ticket without any manual form-filling.

## How it works

```
                     ┌─────────────────────────┐
  Equipment SOPs ───▶│   Ingestion (one-time)   │
   (PDF / text)       │  chunk → embed → FAISS   │
                     └─────────────────────────┘
                                  │
                                  ▼
User question ──▶ Conversational RAG chain ──▶ Grounded answer
     │              (LangChain + Gemini +            (cited from
     │                FAISS retriever)                 the SOPs)
     ▼
LLM-based intent classifier
  "does this need escalation?"
     │
     ▼ (if YES)
REST API call ──▶ ticket_api.py ──▶ tickets.json
 (Flask)            (logs ticket: issue + urgency)
```

1. **Ingestion** — equipment manuals/SOPs are split into chunks, embedded
   with Google's Gemini embedding model, and stored in a local FAISS vector
   index.
2. **Retrieval-augmented answering** — a `ConversationalRetrievalChain`
   retrieves the most relevant SOP chunks for each question and passes them
   to Gemini to generate a grounded answer, with chat memory across turns.
3. **Escalation detection** — rather than brittle keyword matching, a
   separate Gemini call classifies whether the technician's message
   indicates an unresolved issue (e.g. "I already tried the reset twice and
   it's still not working").
4. **Automated ticket logging** — if escalation is detected, the app calls
   a small Flask REST API that logs a ticket (issue + urgency) to
   `tickets.json`, no manual step required.

## Stack

Python · LangChain · Google Gemini API (chat + embeddings) · FAISS ·
Streamlit · Flask · PyPDF2

## Status

**Complete.** The RAG pipeline answers technician questions from real SOP
documentation, and the LLM-based escalation classifier automatically
triggers ticket logging via a REST API when needed.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Run the ticket API in one terminal (leave it running):
```bash
python ticket_api.py
```

Run the app in a second terminal:
```bash
streamlit run app.py
```

1. Upload equipment manual(s)/SOP PDFs in the sidebar.
2. Click **Process**.
3. Ask a question, e.g.:
   - *"The coolant pump on line 3 threw an E01 fault, what do I do?"*
   - *"I've tried resetting the robotic arm calibration twice and the drift
     isn't going away, what now?"* — this one should also log a ticket.

Check `tickets.json` to see logged tickets.

## Known limitations

- Conversational memory can occasionally carry over specifics (like a line
  or machine number) from an earlier question into an unrelated new one —
  a known trade-off of conversational RAG that would need explicit prompt
  guardrails to fully resolve.
- Escalation detection runs a live LLM call per message; for high-volume
  production use this would benefit from caching or a lighter classifier.

## Possible next steps

- Swap the JSON file for a real database (SQLite/Postgres) for ticket storage.
- Add ticket status tracking (open/in-progress/resolved).
- Support multi-file manuals with per-document source citation in answers.
