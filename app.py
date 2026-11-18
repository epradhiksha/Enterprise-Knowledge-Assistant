from urllib.parse import urlparse

import streamlit as st
from pathlib import Path
import hashlib
from rag_chain import create_memory, answer_query
from vector_store import build_index, remove_source
import json
import os

upload_dir=Path("Knowledge_base")

upload_dir.mkdir(exist_ok=True)

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# Changing the key empties the file uploader, so a removed file is not saved again
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

URL_FILE = upload_dir / "urls.txt"

for file in upload_dir.iterdir():
    # urls.txt holds the saved links, it is shown as links below, not as a file
    if file.is_file() and file.name != URL_FILE.name:
        file_bytes = file.read_bytes()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        if file_hash not in st.session_state.uploaded_files:
            st.session_state.uploaded_files[file_hash] = {
                "name": file.name,
                "path": file,
                "type": "application/pdf" if file.suffix.lower() == ".pdf" else "text/plain"
            }




HISTORY_FILE = "chat_history.json"
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def saved_urls():
    if not URL_FILE.exists():
        return []
    return [line.strip() for line in URL_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def index_sources(label):
    """Embed new sources so they are searchable straight away."""
    with st.spinner("Indexing..."):
        total = build_index()._collection.count()
    st.session_state.notice = f"Indexed {label}. {total} chunks stored."


def remove_pending_source(pending):
    """Delete one file or URL and its chunks from the vector store."""
    if pending["kind"] == "file":
        Path(pending["path"]).unlink(missing_ok=True)
        st.session_state.uploaded_files.pop(pending["hash"], None)
        st.session_state.uploader_key += 1
        removed = remove_source(pending["path"])
    else:
        kept = [u for u in saved_urls() if u != pending["url"]]
        URL_FILE.write_text("".join(u + "\n" for u in kept), encoding="utf-8")
        removed = remove_source(pending["url"])
    st.session_state.notice = f"Removed {pending['label']} and {removed} indexed chunks."





st.title("Enterprise Knowledge Assistant")
if "history" not in st.session_state:
    st.session_state.history = load_history()

# One summary memory per browser session, kept across Streamlit reruns
if "memory" not in st.session_state:
    st.session_state.memory = create_memory()

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        





with st.sidebar:
    st.header("Assistant")
   

    if notice := st.session_state.pop("notice", None):
        st.success(notice)

    # Ask before deleting anything
    if pending := st.session_state.get("pending_remove"):
        st.warning(f"Remove {pending['label']} and its indexed chunks?")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Remove", type="primary"):
            remove_pending_source(pending)
            del st.session_state.pending_remove
            st.rerun()
        if cancel_col.button("Cancel"):
            del st.session_state.pending_remove
            st.rerun()

    uploaded_files = st.file_uploader(
        "Upload a file",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )
    if uploaded_files:
        new_files = []
        for file in uploaded_files:
            file_bytes = file.getvalue()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            if file_hash not in st.session_state.uploaded_files:
                file_path = upload_dir /file.name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(file_bytes)
                new_files.append(file.name)

                st.session_state.uploaded_files[file_hash]={
                    "name": file.name,
                    "path": file_path,
                    "type": file.type
                }
        if new_files:
            index_sources(", ".join(new_files))
            st.rerun()
    

    if st.session_state.uploaded_files:
        for file_hash, file_info in list(st.session_state.uploaded_files.items()):
            if not Path(file_info["path"]).exists() or Path(file_info["path"]).name == URL_FILE.name:
                continue
            name_col, remove_col = st.columns([5, 1])
            name_col.download_button(
                label=file_info["name"],
                #open doesnt read the file
                data=Path(file_info["path"]).read_bytes(),
                file_name=file_info["name"],
                mime=file_info["type"],
                key=f"download_{file_hash}",
            )
            if remove_col.button("✕", key=f"remove_{file_hash}", help=f"Remove {file_info['name']}"):
                st.session_state.pending_remove = {
                    "kind": "file",
                    "path": str(file_info["path"]),
                    "hash": file_hash,
                    "label": file_info["name"],
                }
                st.rerun()

    for saved_url in saved_urls():
        url_hash = hashlib.sha256(saved_url.encode("utf-8")).hexdigest()
        link_col, remove_col = st.columns([5, 1])
        link_col.markdown(f"[{saved_url}]({saved_url})")
        if remove_col.button("✕", key=f"remove_url_{url_hash}", help=f"Remove {saved_url}"):
            st.session_state.pending_remove = {
                "kind": "url",
                "url": saved_url,
                "label": saved_url,
            }
            st.rerun()

    url=st.text_input("Enter URL", placeholder="https://example.com")
    if st.button("Save URL"):
        parsed=urlparse(url.strip())

        if parsed.scheme in("http","https"):
            if url.strip() in saved_urls():
                st.info("URL already saved.")
            else:
                with open(URL_FILE,"a",encoding="utf-8") as f:
                    f.write(url.strip()+"\n")
                index_sources(url.strip())
                st.rerun()
        else:
            st.error(" Please enter a valid URL")   





user = st.chat_input("Ask a question")
if user:
    with st.chat_message("user"):
        st.markdown(user)
    answer, sources = answer_query(user, st.session_state.memory)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.history.extend([
        {"role": "user", "content": user},
        {"role": "assistant", "content": answer, "sources": sources},
    ])
    save_history(st.session_state.history)



if st.button("Clear conversation"):
    st.session_state.history = []
    st.session_state.memory = create_memory()
    save_history([])
    st.rerun()
