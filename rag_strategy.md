# RAG Strategy: Enterprise Knowledge Assistant

## 1. Document Loading

### LangChain loaders used

- `PyPDFLoader` for PDF files
- `TextLoader` for text files
- `WebBaseLoader` for public web pages

### Supported source types

Sources are added by uploading files and URLs in the app, which saves them to the `Knowledge_base/` folder. All sources are read from there:

- **PDF:** every `.pdf` file. Multiple PDFs are supported.
- **Text:** every `.txt` file except `urls.txt`.
- **Web:** one public URL per line in `Knowledge_base/urls.txt`.

A page that cannot be loaded is skipped without stopping the rest. Only public pages are used.

### Metadata preservation

- **PDF:** file path, page number and printed page label. Content is loaded page by page. The sample set includes a four-page PDF, so citations show the actual page, such as `NIST_Cybersecurity_Framework_2_0_Enterprise_Guide_4_Pages.pdf — Page 2`.
- **Text:** file path.
- **Web:** URL, page title and description.

This metadata stays attached to every chunk and is used for citations.

---

## 2. Preprocessing

### Cleaning performed

- Line endings are normalised.
- Broken PDF line wraps are joined back into sentences.
- Headers and footers repeated across PDF pages are removed.
- Extra spaces and repeated blank lines are removed.
- Web pages are read from their main article only, so menus and sidebars are skipped.
- Web interface lines such as "skip to content", cookie buttons and "all rights reserved" are removed.
- Empty documents are dropped.

Phrases that can be real content, such as "log in" or "privacy policy", are kept, and so are URLs in the page text.

### Duplicate handling

Each chunk gets an ID made from its source and text. A chunk with an existing ID is skipped, so unchanged content is never stored or embedded twice.

### Source-specific processing

| Source | Processing |
|---|---|
| PDF | Page-wise loading, header and footer removal, line-wrap repair, whitespace cleanup |
| Text | Line-wrap repair, whitespace cleanup |
| Web | Main-article extraction, interface-line removal, whitespace cleanup |

---

## 3. Chunking

The text is split with `RecursiveCharacterTextSplitter`, which breaks at paragraphs first, then lines, then sentences.

### Chunk size

**500 characters.**

### Chunk overlap

**100 characters**, so a fact on a chunk boundary still appears whole in one chunk.

### Experimentation performed

Chunk sizes from 300 to 1500 characters, with matching overlaps, were compared on the knowledge base. Each setting was judged on how often the right chunk was retrieved first and how much text it sent to the LLM.

### Reason for selected configuration

- **It fits the embedding model.** The model reads about 1,000 characters at most. Larger chunks get cut off and their endings cannot be found.
- **It retrieved the right chunk first most reliably.**
- **It matches the documents.** One chunk usually holds one policy section.
- **It keeps the prompt short and focused.**

---

## 4. Embeddings

### Provider

Hugging Face, through `HuggingFaceEmbeddings`, running locally.

### Model name

`sentence-transformers/all-MiniLM-L6-v2`

### Reason for selection

- Free, with no API key needed.
- Runs locally, so documents never leave the machine.
- Small and fast on a normal CPU.


---

## 5. Vector Database

### FAISS or ChromaDB

**ChromaDB**, through `langchain_chroma`, using cosine similarity.

### Persistence approach

- The database is saved in the `Vector_store/` folder.
- On restart, the saved index is reopened and nothing is re-embedded.
- On a rebuild, only new chunks are embedded.
- Removing a source in the app also removes its chunks.

### Reason for selection

- Saves to disk automatically.
- Stores the metadata needed for citations with each vector.
- Lets chunks be added and deleted by ID.
- Needs no separate server.

---

## 6. Retrieval

### Top-k value

**5 chunks** per question.

### Search method

The LangChain retriever interface with `similarity_score_threshold`. It finds the closest chunks by cosine similarity and drops any below the threshold. Each remaining chunk gets a citation label, such as `Employee_Handbook.pdf — Page 1`, `IT_Security_Policy.txt` or the page URL.

### Similarity/relevance threshold

**0.30.** If no chunk reaches it, the assistant returns the fallback message without calling the LLM.

### Reason for selected values

- **k = 5** gives enough context for answers that need more than one source, without adding unrelated text.
- **0.30** sits between the scores of relevant chunks and unrelated ones. It keeps real matches and blocks loosely related text.

---

## 7. Prompt Design

### PromptTemplate / ChatPromptTemplate

`PromptTemplate` is used for three prompts in `rag_chain.py`:

- **Answer prompt:** rules from `rag_prompt.txt` plus the conversation summary, retrieved chunks and question.
- **Follow-up prompt:** rewrites a follow-up into a standalone question for search.
- **Chunk format:** shows each chunk with its source label.

`create_retrieval_chain` and `create_stuff_documents_chain` replace the deprecated `RetrievalQA`.

### Grounding behaviour

- Answer only from the retrieved chunks.
- Never invent facts, names, numbers or links.
- When sources disagree, show both versions with their sources.
- When a question is unclear, ask which topic the user means.
- Decline questions unrelated to the knowledge base.

### Fallback rules

If the chunks do not answer the question, the assistant replies:

> I could not find sufficient information in the indexed knowledge base to answer this question.

This also happens automatically, without the LLM, when no chunk passes the threshold. In that case the code returns the same `Answer:` / `Sources: None` layout the LLM uses, so every fallback looks the same.

### Citation rules

- Every answer ends with a `Sources:` list.
- Only sources that support the answer are listed, each once.
- Labels are copied exactly from the chunks and never invented.
- If the LLM repeats a source line, the code removes the repeat before the answer is shown, so each source appears once.

```
Answer:
Employees are eligible for 18 days of annual leave after completing the probation period.

Sources:
- Employee_Handbook.pdf — Page 1
```

---

## 8. Conversation Memory

### Memory mechanism

`ConversationSummaryMemory` from `langchain_classic`, using the same Groq LLM. Each browser session has its own memory.

### Conversation summarization

After every turn, the LLM updates a short running summary. The prompt gets this summary instead of the full chat history, so it stays small in long conversations.

### How memory and retrieval work together

1. The summary is used to rewrite a follow-up, such as "What about during probation?", into a full question.
2. That question is used to search the knowledge base.
3. The answer comes only from the retrieved chunks.

Memory helps understand the question. Retrieval supplies the facts. The summary is never used as evidence.
