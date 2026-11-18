
from pathlib import Path
from langchain_core.documents import Document
from vector_store import get_vector_store


TOP_K = 5
# Chroma uses cosine distance, LangChain converts it to relevance = 1 - distance
SCORE_THRESHOLD = 0.30


def validate_query(query):
    query = (query or "").strip()
    if not query:
        return False, "Please enter a question."

    if len(query) < 3:
        return False, "Please enter a more detailed question."
    return True, query


def get_retriever(k=TOP_K, score_threshold=SCORE_THRESHOLD):
    return get_vector_store().as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": score_threshold},
    )


def citation_label(metadata):
    source = metadata.get("source", "Unknown")

    if source.startswith(("http://", "https://")):
        return source

    name = Path(source).name
    if str(source).lower().endswith(".pdf"):
        # PyPDFLoader's "page" is 0-based, "page_label" is the printed page
        page = metadata.get("page_label") or int(metadata.get("page", 0)) + 1
        return f"{name} — Page {page}"
    return name


def add_citations(documents):
    return [
        Document(
            page_content=doc.page_content,
            metadata={**doc.metadata, "citation": citation_label(doc.metadata)},
        )
        for doc in documents
    ]
