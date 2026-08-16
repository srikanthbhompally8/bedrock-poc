# Database Schema Documentation

**Version:** 1.0.0  
**Database:** PostgreSQL 14+  
**Last Updated:** 2026-08-14

---

## Table of Contents

1. [Overview](#overview)
2. [Entity-Relationship Diagram](#entity-relationship-diagram)
3. [Table Definitions](#table-definitions)
4. [Indexes](#indexes)
5. [Relationships](#relationships)
6. [Queries](#sample-queries)

---

## Overview

The Bedrock POC uses PostgreSQL for persistent storage with the following 6 core tables:

| Table | Purpose | Records |
|-------|---------|---------|
| `conversations` | Multi-turn chat history | Session-based |
| `documents` | Document storage + RAG embeddings | Per document |
| `document_embeddings` | Chunk-level vector embeddings | Per chunk |
| `resumes` | Parsed resume data | Per candidate |
| `questions` | Q&A audit trail | Per question |
| `job_listings` | Parsed job descriptions | Per job |

---

## Entity-Relationship Diagram

```
┌─────────────────────┐
│  conversations      │
├─────────────────────┤
│ PK: id              │
│ FK: session_id (UUID)
│ messages (JSONB)    │
│ model_id            │
│ created_at          │
│ updated_at          │
└─────────────────────┘
        ↓
        │ session_id
        ↓
┌─────────────────────┐
│  questions          │
├─────────────────────┤
│ PK: id              │
│ FK: session_id (UUID)
│ FK: document_id     │
│ question (TEXT)     │
│ answer (TEXT)       │
│ used_rag (BOOLEAN)  │
│ created_at          │
└─────────────────────┘
        ↑
        │ document_id
        │
┌─────────────────────────────────────┐
│  documents                          │
├─────────────────────────────────────┤
│ PK: id                              │
│ filename (VARCHAR 255)              │
│ content (TEXT)                      │
│ content_hash (VARCHAR 64) - INDEXED │
│ chunks (JSONB)                      │
│ embeddings (JSONB)                  │
│ chunk_count (INTEGER)               │
│ created_at (DATETIME)               │
└─────────────────────────────────────┘
        ↓
        │ document_id (FK)
        ↓
┌─────────────────────────────────────┐
│  document_embeddings                │
├─────────────────────────────────────┤
│ PK: id                              │
│ FK: document_id - INDEXED           │
│ chunk_index (INTEGER)               │
│ chunk_text (TEXT)                   │
│ embedding (ARRAY of FLOAT)          │
│ created_at (DATETIME)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  resumes                            │
├─────────────────────────────────────┤
│ PK: id                              │
│ filename (VARCHAR 255)              │
│ raw_text (TEXT)                     │
│ parsed_data (JSONB)                 │
│ full_name (VARCHAR 255) - INDEXED   │
│ email (VARCHAR 255) - INDEXED       │
│ phone (VARCHAR 20)                  │
│ skills (ARRAY of VARCHAR)           │
│ created_at (DATETIME)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  job_listings                       │
├─────────────────────────────────────┤
│ PK: id                              │
│ job_title (VARCHAR 255) - INDEXED   │
│ company (VARCHAR 255) - INDEXED     │
│ raw_description (TEXT)              │
│ parsed_data (JSONB)                 │
│ years_required (INTEGER)            │
│ embedding (ARRAY of FLOAT)          │
│ created_at (DATETIME)               │
└─────────────────────────────────────┘
```

---

## Table Definitions

### 1. conversations

**Purpose:** Store multi-turn chat conversations for audit and history.

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL UNIQUE,
    messages JSONB NOT NULL DEFAULT '[]',
    model_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB,
    INDEX idx_session_id (session_id)
);
```

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique conversation ID |
| session_id | UUID | NOT NULL, UNIQUE | Session identifier |
| messages | JSONB | NOT NULL | Array of message objects |
| model_id | VARCHAR(255) | NOT NULL | Claude model used |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| metadata_json | JSONB | | Additional metadata |

---

### 2. documents

**Purpose:** Store documents with content and embeddings for RAG.

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    chunks JSONB NOT NULL DEFAULT '[]',
    embeddings JSONB NOT NULL DEFAULT '[]',
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB,
    INDEX idx_filename (filename),
    INDEX idx_content_hash (content_hash)
);
```

**Fields:**
| Field | Type | Purpose |
|-------|------|---------|
| id | SERIAL | Document ID |
| filename | VARCHAR | Source filename |
| content | TEXT | Full document text |
| content_hash | VARCHAR | Hash for deduplication |
| chunks | JSONB | Split text chunks |
| embeddings | JSONB | Vector embeddings |
| chunk_count | INTEGER | Number of chunks |
| created_at | TIMESTAMP | Upload timestamp |

---

### 3. document_embeddings

**Purpose:** Store individual chunk embeddings for efficient vector search.

```sql
CREATE TABLE document_embeddings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding FLOAT[] NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_document_id (document_id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

---

### 4. resumes

**Purpose:** Store parsed candidate resume data.

```sql
CREATE TABLE resumes (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_data JSONB NOT NULL,
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    skills VARCHAR[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB,
    INDEX idx_full_name (full_name),
    INDEX idx_email (email)
);
```

---

### 5. questions

**Purpose:** Audit trail for Q&A interactions.

```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    document_id INTEGER,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    used_rag BOOLEAN DEFAULT 0,
    model_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB,
    INDEX idx_session_id (session_id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

---

### 6. job_listings

**Purpose:** Store parsed job descriptions with embeddings.

```sql
CREATE TABLE job_listings (
    id SERIAL PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    raw_description TEXT NOT NULL,
    parsed_data JSONB NOT NULL,
    years_required INTEGER,
    embedding FLOAT[],
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_json JSONB,
    INDEX idx_job_title (job_title),
    INDEX idx_company (company)
);
```

---

## Indexes

### Performance Indexes

| Table | Column | Type | Purpose |
|-------|--------|------|---------|
| conversations | session_id | UNIQUE | Quick session lookup |
| documents | content_hash | UNIQUE | Prevent duplicates |
| documents | filename | B-tree | Search by name |
| document_embeddings | document_id | B-tree | Chunk retrieval |
| resumes | full_name | B-tree | Candidate search |
| resumes | email | B-tree | Candidate lookup |
| questions | session_id | B-tree | Chat history |
| job_listings | job_title | B-tree | Job search |
| job_listings | company | B-tree | Filter by company |

### Vector Indexes (Future)

When upgrading to pgvector:
```sql
CREATE INDEX idx_document_embeddings_vector 
ON document_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

CREATE INDEX idx_job_embeddings_vector 
ON job_listings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

---

## Relationships

### One-to-Many Relationships

1. **documents → document_embeddings**
   - One document has many chunks
   - Foreign key: `document_embeddings.document_id`
   - Use: Retrieve all embeddings for a document

2. **documents → questions**
   - One document can have many Q&A interactions
   - Foreign key: `questions.document_id`
   - Use: Find all questions about a document

3. **conversations → questions** (via session_id)
   - One session has many questions
   - Link: `conversations.session_id` = `questions.session_id`
   - Use: Get conversation history

---

## Sample Queries

### Find candidate by email
```sql
SELECT * FROM resumes WHERE email = 'john@example.com';
```

### Get all documents for a user
```sql
SELECT d.* FROM documents d
JOIN questions q ON d.id = q.document_id
WHERE q.session_id = 'session-123'
GROUP BY d.id;
```

### Get Q&A history for a conversation
```sql
SELECT question, answer, model_id, created_at 
FROM questions 
WHERE session_id = 'session-123'
ORDER BY created_at DESC;
```

### Find job listings by company
```sql
SELECT job_title, parsed_data 
FROM job_listings 
WHERE company = 'TechCorp'
ORDER BY created_at DESC;
```

### Get embeddings for semantic search
```sql
SELECT chunk_text, embedding 
FROM document_embeddings 
WHERE document_id = 1
ORDER BY chunk_index;
```

---

## Backup & Maintenance

### Daily Backup
```bash
pg_dump -U postgres bedrock_poc > backup_$(date +%Y%m%d).sql
```

### Vacuum and Analyze (Weekly)
```sql
VACUUM ANALYZE;
```

### Check Index Health
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Growth Estimates

**Projected Storage (1 year):**
- Documents: ~500 records × 2MB avg = 1GB
- Embeddings: ~50K chunks × 0.5MB = 25GB
- Resumes: ~1K records × 100KB = 100MB
- Job listings: ~500 records × 50KB = 25MB
- **Total: ~26GB**

**Recommended Actions:**
- Enable partitioning after 1 year
- Archive old documents quarterly
- Use pgvector for semantic search at scale

---

**Database Version:** PostgreSQL 14+  
**Last Updated:** 2026-08-14  
**Status:** Production Ready ✅
