#4

from pathlib import Path
from langchain_chroma import Chroma
from loaders import load_document
from preprocess import preprocess
from embeddings import embed, run as chunk_and_save
import json


vector_dir = Path("Vector_store")
input_data = Path("Processed_data/chunks.json")
COLLECTION = "knowledge_base"


def get_vector_store():
    # Opens the persisted collection (or creates it empty) - no re-embedding
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=embed(),
        persist_directory=str(vector_dir),
        collection_metadata={"hnsw:space": "cosine"},
    )


def create_vector_store():
    vector_store = get_vector_store()

    with open(input_data, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    ids = [chunk["id"] for chunk in chunks]
    existing_ids = set(vector_store.get(ids=ids, include=[])["ids"])

    new_chunks = [
        chunk for chunk in chunks
        if chunk["id"] not in existing_ids
    ]

    print("Existing chunks skipped:", len(existing_ids))
    print("New chunks to insert:", len(new_chunks))

    # Only unseen chunks are embedded, so restarts don't regenerate embeddings
    if new_chunks:
        vector_store.add_texts(
            texts=[chunk["text"] for chunk in new_chunks],
            metadatas=[chunk["metadata"] for chunk in new_chunks],
            ids=[chunk["id"] for chunk in new_chunks],
        )

    print("Total chunks stored:", vector_store._collection.count())

    return vector_store


def remove_source(source):
    """Delete every chunk of one source (file path or URL) from Chroma and chunks.json.

    Both must be cleaned: create_vector_store() re-adds anything still listed
    in chunks.json, so a removed file would otherwise come back on the next build.
    """
    vector_store = get_vector_store()
    ids = vector_store.get(where={"source": source}, include=[])["ids"]
    if ids:
        vector_store.delete(ids=ids)

    if input_data.exists():
        with open(input_data, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        kept = [c for c in chunks if c.get("metadata", {}).get("source") != source]
        if len(kept) != len(chunks):
            with open(input_data, "w", encoding="utf-8") as f:
                json.dump(kept, f, indent=4, ensure_ascii=False)

    return len(ids)


def build_index():
    data = load_document()
    processed = preprocess(data)
    chunk_and_save(processed)
    return create_vector_store()


if __name__=="__main__":
    build_index()
