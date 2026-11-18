from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from functools import lru_cache
from pathlib import Path
import hashlib
import json

INPUT = Path("Processed_data/chunks.json")


def chunking(processed_data):
    documents = []

    for docs in processed_data["pdf"].values():
        documents.extend(docs)

    for docs in processed_data["txt"].values():
        documents.extend(docs)

    documents.extend(processed_data["url"])

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )

    return text_splitter.split_documents(documents)


def chunk_id(text, metadata):
    """Create a repeatable ID using chunk text and source."""
    source = metadata.get("source", "")
    content = f"{source}|{text}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def save_chunks(chunks):
    INPUT.parent.mkdir(parents=True, exist_ok=True)

    # Load existing JSON, if present
    if INPUT.exists():
        try:
            with INPUT.open("r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            print("Existing JSON is invalid or unreadable. Fix it before continuing.")
            return
    else:
        existing = []

    # Index existing chunks by ID
    existing_by_id = {
        item["id"]: item
        for item in existing
        if isinstance(item, dict) and "id" in item
    }

    added = 0
    duplicates = 0

    for chunk in chunks:
        text = chunk.page_content.strip()

        if not text:
            continue

        metadata = {
            key: value
            for key, value in chunk.metadata.items()
            if value is not None
        }

        # JSON metadata must be serializable
        metadata = {
            key: str(value) if not isinstance(
                value, (str, int, float, bool, list, dict)
            ) else value
            for key, value in metadata.items()
        }

        identifier = chunk_id(text, metadata)

        if identifier in existing_by_id:
            duplicates += 1
            continue

        existing_by_id[identifier] = {
            "id": identifier,
            "text": text,
            "metadata": metadata,
        }
        added += 1

    # Save only if new chunks were found
    if added:
        with INPUT.open("w", encoding="utf-8") as f:
            json.dump(
                list(existing_by_id.values()),
                f,
                indent=4,
                ensure_ascii=False,
            )

    print(f"Existing chunks: {len(existing)}")
    print(f"Duplicate chunks skipped: {duplicates}")
    print(f"New chunks added: {added}")
    print(f"Total unique chunks: {len(existing_by_id)}")
    print(f"JSON file: {INPUT.resolve()}")


# Cached so the model is loaded once per process, not on every query
@lru_cache(maxsize=1)
def embed():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def run(processed_data):
    chunks = chunking(processed_data)
    save_chunks(chunks)

    return chunks
