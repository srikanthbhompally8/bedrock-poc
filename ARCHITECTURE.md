# Architecture Documentation

## System Overview

The Bedrock POC is a production-ready application demonstrating AI-powered use cases
with Amazon Bedrock. It uses a modular, layered architecture that separates concerns
and maximizes code reuse.

```
┌─────────────────────────────────────────────┐
│           User Interfaces                   │
├─────────────────────────────────────────────┤
│   CLI (click)      │    Streamlit Web UI    │
│   ▼                │        ▼               │
└─────────────────────────────────────────────┘
            │                   │
            ▼                   ▼
┌─────────────────────────────────────────────┐
│        Use Cases Layer (bedrock_poc)        │
├─────────────────────────────────────────────┤
│ • chat_turn()                               │
│ • summarize_document()                      │
│ • answer_question()                         │
│ • answer_question_with_rag()     [NEW]      │
│ • parse_resume()                 [NEW]      │
└─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────┐
│    Core Service Layer                       │
├─────────────────────────────────────────────┤
│ • bedrock/client.py (Bedrock API)           │
│ • bedrock/vector_store.py (RAG) [NEW]       │
│ • bedrock/models.py (Pydantic) [NEW]        │
└─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────┐
│      AWS Bedrock (Cloud)                    │
├─────────────────────────────────────────────┤
│ • Claude 3.5 Sonnet (Chat/Q&A/Summarize)    │
│ • Titan Embeddings v2 (RAG semantic search) │
└─────────────────────────────────────────────┘
```

## Components

### 1. **Bedrock Client** (`bedrock_poc/client.py`)

Thin, model-agnostic wrapper around the AWS Bedrock Converse API.

**Key Functions:**
- `build_client()` - Creates and configures boto3 bedrock-runtime client
- `converse()` - Synchronous request-response with streaming support
- `converse_stream()` - Generator for streaming responses token-by-token
- `embed_text()` - Text embeddings for RAG (Titan Embeddings v2) [NEW]

**Benefits:**
- Single client instance handles all models
- Automatic retry logic and timeouts
- Clear error messages for AWS failures
- Environment-driven configuration

### 2. **Use Cases** (`bedrock_poc/use_cases.py`)

Business logic layer implementing each feature as a single-purpose function.

**Functions:**

| Function | Input | Output | Use Case |
|----------|-------|--------|----------|
| `chat_turn()` | Client, message history, user message | Assistant message | Multi-turn chat |
| `summarize_document()` | Client, document text | Summary string | Document condensation |
| `answer_question()` | Client, document, question | Answer string | Grounded Q&A |
| `answer_question_with_rag()` [NEW] | Client, store, document, question | Answer string | Large doc Q&A |
| `parse_resume()` [NEW] | Client, resume text | ResumeParsed JSON | Resume extraction |

**Design:**
- No state — all functions are pure and reusable
- Consistent error handling and logging
- Configurable parameters (temperature, top_p, etc.)
- Works identically from CLI and web UI

### 3. **Data Models** (`bedrock_poc/models.py`) [NEW]

Pydantic-based data validation for structured outputs.

**Models:**
- `ResumeParsed` - Structured resume data with validation

**Benefits:**
- Type safety (IDE autocomplete, runtime validation)
- JSON schema generation for API clients
- Example data for documentation
- Automatic serialization/deserialization

### 4. **Vector Store** (`bedrock_poc/vector_store.py`) [NEW]

In-memory semantic search engine for RAG.

**Key Class: `DocumentStore`**

```python
store = DocumentStore(model_id)
store.add_documents(text)           # Chunks & embeds text
results = store.search(query, k=3)  # Returns top-k results
```

**Process:**
1. **Chunking** - Split documents into ~1000 char pieces with overlap
2. **Embedding** - Generate vector embeddings using Titan API
3. **Indexing** - Store chunks + embeddings in memory
4. **Search** - Cosine similarity search for top-k relevant chunks
5. **Retrieval** - Pass chunks to Claude for grounded response

**Configuration:**
- `chunk_size` - Characters per chunk (default: 1000)
- `overlap` - Overlap between chunks (default: 100)
- `top_k` - Results to retrieve (default: 3)

### 5. **Web UI** (`app.py`)

Streamlit application with five tabs.

**Tabs:**

| Tab | Widget Type | Features |
|-----|-------------|----------|
| **Chat** | Text input + history | Multi-turn, streaming, context preservation |
| **Summarize** | File upload + textarea | Document input, word count, download |
| **Q&A** | File upload + question + RAG toggle | Basic + RAG modes, size detection |
| **Parse Resume** [NEW] | File upload + paste | PDF/text parsing, JSON display, export |
| **Q&A (RAG)** | Integrated in Q&A tab | Auto-enable for large docs, semantic search |

**Session State:**
- `chat_history` - Persistent conversation within a session
- `document_loaded` - Cache last uploaded document
- `rag_store` - Embeddings and chunks (cleared per document)

### 6. **CLI** (`cli.py`)

Click-based command-line interface for automation and testing.

**Commands:**

```bash
python cli.py chat                                    # Interactive chat
python cli.py summarize --file doc.txt               # Summarize
python cli.py ask --file doc.txt --question "Q?"    # Q&A
python cli.py ask --file doc.txt --question "Q?" --use-rag  # RAG Q&A
python cli.py parse --file resume.pdf                # Parse resume
```

**Features:**
- Exit codes for scripting (0=success, 1=error)
- `--verbose` flag for DEBUG logging
- JSON output for resume parsing
- Streaming responses for chat/Q&A

## Data Flow

### Resume Parsing

```
User Upload (PDF/text)
    ▼
Extract Text (pypdf or raw)
    ▼
Send to Claude with Pydantic schema
    ▼
Claude responds with JSON
    ▼
Validate with Pydantic ResumeParsed
    ▼
Return structured data
```

### RAG Q&A

```
User Question + Document
    ▼
DocumentStore.add_documents(text)
    ├─ Chunk into ~1000 char pieces
    ├─ Embed each chunk (Titan API)
    └─ Store vectors in memory
    ▼
DocumentStore.search(question)
    ├─ Embed question (Titan API)
    ├─ Cosine similarity to all chunks
    └─ Return top-3 chunks
    ▼
Build prompt: system + chunks + question
    ▼
Send to Claude
    ▼
Return answer
```

### Basic Q&A

```
User Question + Document
    ▼
Truncate to 40k chars
    ▼
Build prompt: system + document + question
    ▼
Send to Claude
    ▼
Return answer
```

## Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **LLM** | Claude 3.5 Sonnet | State-of-art, affordable, no jailbreaks |
| **Embeddings** | Titan Text Embeddings v2 | Free tier, native AWS integration |
| **Python Runtime** | Python 3.10+ | Modern type hints, performance |
| **API Framework** | boto3 | Official AWS SDK, battle-tested |
| **Web UI** | Streamlit | Zero-config, fast iteration, great for demos |
| **CLI** | Click | Simple, Pythonic argument parsing |
| **Data Validation** | Pydantic v2 | Type safety, JSON schema, performance |
| **PDF Parsing** | pypdf | Pure Python, no external dependencies |
| **Config** | python-dotenv | Environment-based secrets, no .gitignore risk |
| **Deployment** | Systemd + Nginx | Battle-tested, minimal overhead |

## Scalability & Limitations

### Current Design
- ✅ **Stateless functions** - Easy to parallelize
- ✅ **No external DB needed** - Single-file deployment
- ✅ **Model-agnostic** - Switch Bedrock models with env var
- ⚠️ **In-memory vector store** - Embeddings lost on restart
- ⚠️ **Single-threaded Streamlit** - One user at a time
- ⚠️ **No auth/RBAC** - Open access (add API gateway for production)

### To Scale to Production

1. **Persistent Vector Store**
   - Replace in-memory `DocumentStore` with Pinecone / Weaviate / Milvus
   - Add database versioning for document updates

2. **Session Persistence**
   - Add Redis for conversation history
   - Cache embeddings to avoid re-computing

3. **Multi-Instance**
   - Run app behind load balancer
   - Use shared vector DB + Redis
   - Add API tier (FastAPI/Flask) if needed

4. **Monitoring**
   - CloudWatch metrics for API calls
   - Cost alerts (Bedrock is pay-per-token)
   - Latency tracking per feature

5. **Security**
   - Add API key authentication
   - Rate limiting per user/API key
   - Input validation/sanitization

## Cost Estimation

| Component | Cost | Notes |
|-----------|------|-------|
| Claude 3.5 Sonnet | $0.003 / 1K input tokens | ~$0.02-0.05 per chat turn |
| Titan Embeddings | $0.02 / 1M tokens | ~$0.002 per document |
| EC2 Instance | $0.10 / hour | t3.micro on-demand |
| Data Transfer | $0.09 / GB | Minimal for POC |
| **Monthly (estimated)** | **$100-150** | Based on 1000 API calls/month |

## Deployment Architecture

```
Nginx (Port 80)
    ▼
Reverse Proxy (Port 8501)
    ▼
Streamlit App (Single Instance)
    ▼
boto3 Bedrock Client
    ▼
AWS Bedrock API (us-east-1)
```

See **DEPLOYMENT.md** for EC2 setup and monitoring.

## Testing

- **Unit Tests** - Offline smoke tests with fake client (no AWS)
- **Integration Tests** - Run against real Bedrock (requires AWS credentials)
- **Manual Testing** - CLI and web UI via browser

Run tests:
```bash
pip install pytest
pytest tests/ -v
```

## Future Enhancements

1. **Batch APIs** - Process multiple documents/resumes in one call
2. **Streaming RAG** - Stream chunks as they're retrieved (vs. all at once)
3. **Custom Embeddings** - Fine-tune Titan embeddings on domain data
4. **Reranking** - Two-stage retrieval (fast embedding search + LLM reranking)
5. **Knowledge Base** - Replace in-memory store with Bedrock Knowledge Base
6. **Multi-Model** - Support multiple Bedrock models (Haiku, Opus, Llama, etc.)
7. **API Gateway** - REST/GraphQL API for downstream clients
8. **Dashboard** - Real-time cost/usage monitoring
