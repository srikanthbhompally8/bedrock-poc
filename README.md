# Amazon Bedrock POC

A small, self-contained proof of concept that calls **Amazon Bedrock** to demonstrate
three common LLM use cases from one shared core:

1. **Chat** — a multi-turn conversation that keeps context across turns.
2. **Document summarization** — condense a document into a faithful summary.
3. **Document Q&A** — answer questions grounded strictly in a supplied document.

It ships with **two interfaces** over the same code:

- a **CLI** (`cli.py`)
- a **Streamlit web UI** (`app.py`)

All Bedrock access goes through `boto3`'s `bedrock-runtime` client and the Bedrock
**Converse API**, so the app is model-agnostic — switch models with one env var.

## Project layout

```
bedrock-poc/
├── bedrock_poc/
│   ├── client.py      # boto3 bedrock-runtime client + converse() / converse_stream()
│   └── use_cases.py   # chat_turn(), summarize_document(), answer_question()
├── cli.py             # command-line interface (chat / summarize / ask)
├── app.py             # Streamlit web UI (Chat / Summarize / Q&A tabs)
├── tests/             # offline smoke tests (fake client — no AWS needed)
├── sample_document.txt
├── requirements.txt
└── .env.example
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

# Ask a grounded question about a document
python cli.py ask --file sample_document.txt --question "Who is the executive sponsor?"
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

## Notes / limitations (it's a POC)

- **Document Q&A puts the whole document in the prompt** (in-context grounding). Large
  documents are truncated at ~40k characters. Production RAG would chunk the document
  and retrieve only the most relevant pieces (e.g. via a Bedrock Knowledge Base +
  vector store) instead of truncating.
- Only plain-text/markdown input is supported. PDFs/Word docs would need an extraction
  step first.
- Conversation history is kept in memory for the session only; nothing is persisted.
```
