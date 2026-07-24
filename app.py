"""Streamlit web UI for the Amazon Bedrock POC.

Run it with:

    streamlit run app.py

Three tabs, one per use case (Chat, Summarize, Q&A), all sharing the same ``bedrock_poc``
core the CLI uses. This file is purely the presentation layer: it manages Streamlit
widgets and session state, and calls into ``bedrock_poc`` for anything Bedrock-related.
"""

from __future__ import annotations

import logging

import streamlit as st
from dotenv import load_dotenv

from bedrock_poc import client as bedrock
from bedrock_poc import use_cases

# Load variables from a local .env file (if present) into the environment before
# anything reads BEDROCK_MODEL_ID / AWS_REGION. No-op if .env doesn't exist.
load_dotenv()

# Basic logging so Bedrock warnings (e.g. document truncation) show up in the console
# where the operator launched Streamlit.
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Upper bound on uploaded document size we will read into memory (characters). Guards
# the demo against someone dropping in a huge file. The core also truncates for the
# model; this is the UI-layer read guard.
MAX_UPLOAD_CHARS = 200_000


@st.cache_resource
def get_client():
    """Build (and cache) a single Bedrock client for the whole Streamlit session.

    ``st.cache_resource`` ensures we create the client once rather than on every
    rerun (Streamlit re-executes the script top-to-bottom on each interaction).

    Returns:
        A ``bedrock-runtime`` client, or ``None`` if construction failed (the caller
        renders the error so the app does not crash on a bad AWS setup).
    """
    try:
        return bedrock.build_client()
    except RuntimeError as err:
        # Store the message on the exception so the UI can display it.
        st.session_state["client_error"] = str(err)
        return None


def _read_upload(uploaded_file) -> str:
    """Decode an uploaded text file into a (size-capped) string.

    Args:
        uploaded_file: A Streamlit ``UploadedFile`` (or None).

    Returns:
        The decoded text, or an empty string if nothing was uploaded.
    """
    if uploaded_file is None:
        return ""
    # Streamlit gives bytes; decode as UTF-8, replacing undecodable bytes so odd files
    # do not crash the demo, and cap the length.
    raw = uploaded_file.getvalue()
    text = raw.decode("utf-8", errors="replace")
    return text[:MAX_UPLOAD_CHARS]


def render_chat_tab(client) -> None:
    """Render the multi-turn chat tab with streaming replies.

    Conversation history lives in ``st.session_state`` so it survives Streamlit reruns.

    Args:
        client: A ``bedrock-runtime`` client.
    """
    st.subheader("Chat")
    st.caption("Multi-turn conversation. Context is kept for the session.")

    # Initialize the two parallel histories on first render:
    #  - "chat_display": simple {role, text} dicts for rendering the transcript.
    #  - "chat_history": Bedrock Converse-shaped turns sent back to the model.
    if "chat_display" not in st.session_state:
        st.session_state["chat_display"] = []
        st.session_state["chat_history"] = []

    # Redraw the full transcript each rerun so the conversation persists on screen.
    for turn in st.session_state["chat_display"]:
        with st.chat_message(turn["role"]):
            st.markdown(turn["text"])

    # The chat input box pinned to the bottom of the tab.
    user_message = st.chat_input("Type a message…")
    if not user_message:
        return

    # Show the user's message immediately.
    with st.chat_message("user"):
        st.markdown(user_message)

    # Stream the assistant reply so it "types" in real time.
    with st.chat_message("assistant"):
        try:
            # st.write_stream consumes the generator from the core and returns the full
            # concatenated text once streaming completes.
            chunks = use_cases.chat_turn(
                client, st.session_state["chat_history"], user_message, stream=True
            )
            reply = st.write_stream(chunks)
        except RuntimeError as err:
            st.error(str(err))
            return

    # Persist both sides to both histories for the next turn.
    st.session_state["chat_display"].append({"role": "user", "text": user_message})
    st.session_state["chat_display"].append({"role": "assistant", "text": reply})
    st.session_state["chat_history"].append(
        {"role": "user", "content": [{"text": user_message}]}
    )
    st.session_state["chat_history"].append(
        {"role": "assistant", "content": [{"text": reply}]}
    )


def render_summarize_tab(client) -> None:
    """Render the document summarization tab.

    Args:
        client: A ``bedrock-runtime`` client.
    """
    st.subheader("Summarize a document")
    st.caption("Upload or paste text, then generate a concise, faithful summary.")

    # Two ways to provide text: upload a file or paste directly.
    uploaded = st.file_uploader("Upload a .txt / .md file", type=["txt", "md"])
    pasted = st.text_area("…or paste text here", height=200)

    # Uploaded file takes precedence over pasted text when both are present.
    document = _read_upload(uploaded) or pasted

    if st.button("Summarize", type="primary"):
        if not document.strip():
            st.warning("Please provide some text to summarize.")
            return
        with st.spinner("Summarizing…"):
            try:
                summary = use_cases.summarize_document(client, document)
            except (ValueError, RuntimeError) as err:
                st.error(str(err))
                return
        st.markdown("### Summary")
        st.write(summary)


def render_qa_tab(client) -> None:
    """Render the document question-answering tab.

    Args:
        client: A ``bedrock-runtime`` client.
    """
    st.subheader("Ask a document")
    st.caption("Answers are grounded strictly in the document you provide.")

    uploaded = st.file_uploader(
        "Upload a .txt / .md file", type=["txt", "md"], key="qa_upload"
    )
    pasted = st.text_area("…or paste text here", height=200, key="qa_paste")
    document = _read_upload(uploaded) or pasted

    question = st.text_input("Your question")

    # Toggle for RAG mode
    use_rag = st.checkbox(
        "Use RAG (Retrieval-Augmented Generation)",
        value=False,
        help="Chunks large documents and retrieves relevant sections. Better for documents >5000 chars."
    )

    if st.button("Ask", type="primary"):
        if not document.strip():
            st.warning("Please provide a document.")
            return
        if not question.strip():
            st.warning("Please enter a question.")
            return
        with st.spinner("Thinking…"):
            try:
                if use_rag:
                    st.info("ℹ️ Using RAG mode: chunking document and retrieving relevant sections…")
                    answer = use_cases.answer_question_with_rag(client, document, question)
                else:
                    answer = use_cases.answer_question(client, document, question)
            except (ValueError, RuntimeError) as err:
                st.error(str(err))
                return
        st.markdown("### Answer")
        st.write(answer)


def render_parse_tab(client) -> None:
    """Render the resume parsing tab.

    Args:
        client: A ``bedrock-runtime`` client.
    """
    st.subheader("Parse a Resume")
    st.caption("Upload a resume to extract and structure key information.")

    uploaded = st.file_uploader(
        "Upload a resume (.txt / .pdf / .md)", type=["txt", "pdf", "md"], key="parse_upload"
    )
    pasted = st.text_area("…or paste resume text here", height=250, key="parse_paste")
    resume_text = _read_upload(uploaded) or pasted

    if st.button("Parse Resume", type="primary"):
        if not resume_text.strip():
            st.warning("Please provide a resume.")
            return
        with st.spinner("Parsing resume…"):
            try:
                parsed = use_cases.parse_resume(client, resume_text)
            except (ValueError, RuntimeError) as err:
                st.error(str(err))
                return

        st.markdown("### Parsed Resume")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Name:** {parsed.full_name}")
            st.markdown(f"**Email:** {parsed.email}")
            if parsed.phone:
                st.markdown(f"**Phone:** {parsed.phone}")
        with col2:
            if parsed.summary:
                st.markdown(f"**Summary:** {parsed.summary}")

        if parsed.skills:
            st.markdown("### Skills")
            st.write(", ".join(parsed.skills))

        if parsed.experience:
            st.markdown("### Experience")
            for exp in parsed.experience:
                st.markdown(f"**{exp.get('title', 'N/A')}** @ {exp.get('company', 'N/A')}")
                st.caption(f"{exp.get('dates', 'N/A')}")
                if exp.get('description'):
                    st.write(exp['description'])

        if parsed.education:
            st.markdown("### Education")
            for edu in parsed.education:
                st.markdown(f"**{edu.get('degree', 'N/A')}** in {edu.get('field', 'N/A')}")
                st.caption(f"{edu.get('school', 'N/A')} ({edu.get('year', 'N/A')})")

        # Show raw JSON in expandable section
        with st.expander("View Raw JSON"):
            st.json(parsed.model_dump())


def main() -> None:
    """Compose the page: header, client setup, and the three use-case tabs."""
    st.set_page_config(page_title="Amazon Bedrock POC", page_icon="🤖", layout="centered")
    st.title("🤖 Amazon Bedrock POC")
    st.caption(f"Model: `{bedrock.get_model_id()}`")

    # Build the shared client. If it failed, show the stored error and stop — every tab
    # needs the client, so there is nothing useful to render without it.
    client = get_client()
    if client is None:
        st.error(st.session_state.get("client_error", "Could not create the Bedrock client."))
        st.stop()

    # One tab per use case; each renders independently against the same client.
    chat_tab, summary_tab, qa_tab, parse_tab = st.tabs(["Chat", "Summarize", "Q&A", "Parse Resume"])
    with chat_tab:
        render_chat_tab(client)
    with summary_tab:
        render_summarize_tab(client)
    with qa_tab:
        render_qa_tab(client)
    with parse_tab:
        render_parse_tab(client)


if __name__ == "__main__":
    main()
