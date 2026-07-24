# Amazon Bedrock POC

A production-ready proof of concept demonstrating AI-powered features using **Amazon Bedrock**
with Claude 3.5 Sonnet. Includes five integrated use cases:

1. **Chat** — Multi-turn conversations with persistent context
2. **Document Summarization** — Condense documents into faithful summaries
3. **Document Q&A** — Answer questions grounded strictly in supplied documents
4. **Resume Parsing** — Extract structured data from resumes (JSON output)
5. **RAG (Retrieval-Augmented Generation)** — Semantic search over large documents

It ships with **two interfaces** over the same code:

- a **CLI** (`cli.py`) — Command-line interface for scripts and automation
- a **Streamlit web UI** (`app.py`) — Interactive web application

All Bedrock access goes through `boto3`'s `bedrock-runtime` client and the Bedrock
**Converse API**, so the app is model-agnostic — switch models with one env var.
The app is **deployed on EC2 with Nginx** and available as a live service.

## Project layout

```
bedrock-poc/
├── bedrock_poc/
│   ├── client.py          # boto3 bedrock-runtime client + converse() / converse_stream()
│   ├── use_cases.py       # chat_turn(), summarize_document(), answer_question(), 
│   │                      # parse_resume(), answer_question_with_rag()
│   ├── models.py          # Pydantic data models (ResumeParsed)
│   ├── vector_store.py    # DocumentStore for RAG (chunking, embedding, retrieval)
│   └── __init__.py
├── cli.py                 # Command-line interface (chat / summarize / ask / parse / RAG support)
├── app.py                 # Streamlit web UI (Chat / Summarize / Q&A / Parse Resume / RAG toggle)
├── tests/                 # Offline smoke tests (fake client — no AWS needed)
├── config/                # Deployment configuration
│   ├── bedrock-poc.service   # Systemd service for EC2
│   └── nginx.conf            # Nginx reverse proxy config
├── sample_document.txt    # Sample document for testing
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── README.md             # This file
├── ARCHITECTURE.md       # System design and components
├── AWS_SETUP.md         # Bedrock configuration and IAM setup
└── DEPLOYMENT.md        # EC2 and Nginx deployment guide
```

## Prerequisites

1. An AWS account with **Amazon Bedrock enabled** and **model access granted** for the
   model you intend to use (Bedrock console → *Model access*).
2. AWS credentials available via the standard chain: `aws configure`, SSO, environment
   variables, or an IAM role. The credentials need permission to call
   `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`.
3. Python 3.10+.

## Setup

```bash
cd bedrock-poc
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit BEDROCK_MODEL_ID / AWS_REGION as needed
```

Set the model and region (or put them in `.env` and export them):

```bash
export AWS_REGION=us-east-1
export BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

> **Model IDs vary by account/region.** If you get an access or "invalid model" error,
> open the Bedrock console, confirm the model is enabled, and copy its exact model ID
> (some models require a region-prefixed *inference profile* ID like `us.anthropic...`).

## Usage — CLI

```bash
# Interactive multi-turn chat (type 'exit' to quit)
python cli.py chat

# Summarize a document
python cli.py summarize --file sample_document.txt

# Ask a grounded question about a document (basic Q&A, up to 40k chars)
python cli.py ask --file sample_document.txt --question "Who is the executive sponsor?"

# Ask a question with RAG (semantic search for large documents)
python cli.py ask --file large_document.txt --question "What is the main topic?" --use-rag

# Parse a resume and extract structured data (JSON output)
python cli.py parse --file resume.pdf
```

Add `--verbose` for DEBUG logging.

## Usage — Web UI

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually <http://localhost:8501>). Use the **Chat**,
**Summarize**, and **Q&A** tabs. Chat replies stream in live.

## Tests

The smoke tests inject a fake Bedrock client, so they run offline with no AWS calls:

```bash
pip install pytest
python -m pytest tests/ -v
```

## Features in Detail

### Chat
- Multi-turn conversation with persistent context within a session
- Supports free-form questions and responses
- Real-time streaming via CLI and web UI

### Document Summarization
- Faithful, concise summaries that preserve key facts and numbers
- Supports text, markdown, and PDF input
- Works with documents up to 40k characters (or unlimited with RAG)

### Document Q&A
- Grounded answers using only supplied document content
- Basic mode: Documents up to 40k characters
- **RAG mode** (NEW): Unlimited document size via semantic search
  - Automatically chunks large documents
  - Retrieves only relevant sections (top-3 by default)
  - Provides context-aware, accurate answers

### Resume Parsing (NEW)
- Extracts structured data from resumes (PDF/text)
- Returns JSON with: name, email, phone, skills, experience, education
- Type-safe validation using Pydantic
- Reusable for HR automation and job matching

### RAG Implementation (NEW)
- Semantic search using AWS Bedrock Embeddings (Titan v2)
- In-memory document store with configurable chunking
- Efficiently handles documents of any size
- Cosine similarity ranking for relevance

## Architecture & Deployment

- **Backend**: Python 3.10+ with Pydantic for type safety
- **Web UI**: Streamlit (interactive, zero-config)
- **CLI**: Click-based command-line interface for automation
- **Cloud**: AWS Bedrock (Claude 3.5 Sonnet + Titan Embeddings)
- **Deployment**: EC2 instance with Nginx reverse proxy
- **Service Management**: Systemd for process monitoring and auto-restart

See **ARCHITECTURE.md**, **AWS_SETUP.md**, and **DEPLOYMENT.md** for complete details.

## Notes / Limitations

- **In-memory state**: Conversation history and document embeddings are kept in memory
  for the session only; nothing is persisted to a database. Production use would add
  persistent vector storage (e.g., Pinecone, Weaviate) and conversation history.
- **Stateless design**: Each instance is independent. Horizontal scaling requires
  external session/vector storage.
- **Batch processing**: The resume parser and RAG engine currently process one item at
  a time. Production might add batch APIs for bulk processing.

```
