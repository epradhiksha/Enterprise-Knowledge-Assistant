# Assignment 1 — Enterprise Knowledge Assistant using Python & LangChain (Advanced RAG)


## Project Overview

A chat assistant that answers questions from company documents. It reads PDFs, text files and web pages, finds the parts that match a question, and answers only from them, with sources. If the answer is not in the documents, it says so instead of guessing. It also remembers the conversation, so follow-up questions work.

The sample knowledge base is for TechNova Solutions, a fictional company:

| Document | Type | Content |
|---|---|---|
| Employee_Handbook.pdf | PDF | Working hours, leave, probation, conduct |
| HR_Policies.pdf | PDF | Recruitment, pay, probation, performance reviews |
| Leave_Policy_2026.pdf | PDF | Updated leave policy. Gives 20 days of annual leave, while the handbook gives 18, to show conflicting sources |
| NIST_Cybersecurity_Framework_2_0_Enterprise_Guide_4_Pages.pdf | PDF (4 pages) | Summary of the NIST Cybersecurity Framework 2.0: governance, risk, protection, detection, response, recovery. Shows page numbers in citations |
| IT_Security_Policy.txt | Text | Passwords, devices, phishing, incident reporting |
| OWASP Authentication Cheat Sheet | Web page | Password and login security guidance |

## Python Version

Python 3.13.9

## LangChain Version

| Package | Version |
|---|---|
| langchain | 1.4.6 |
| langchain-core | 1.6.12 |
| langchain-classic | 1.0.8 |
| langchain-community | 0.4.2 |
| langchain-text-splitters | 1.1.3 |
| langchain-groq | 1.1.3 |
| langchain-huggingface | 1.2.3 |
| langchain-chroma | 1.1.0 |

Deprecated components in LangChain 1.4.6:

- `RetrievalQA` is deprecated, so `create_retrieval_chain` with `create_stuff_documents_chain` is used instead.
- `ConversationSummaryMemory` is deprecated but still available in `langchain-classic` 1.0.8, so it is used from there. It prints a deprecation warning when the app starts.
- `langchain-community` is no longer actively maintained. The document loaders still work from version 0.4.2 and print a warning when the app starts.

## LangChain Concepts Used

- **Document loaders:** `PyPDFLoader`, `TextLoader`, `WebBaseLoader`
- **Text splitting:** `RecursiveCharacterTextSplitter`
- **Embeddings:** `HuggingFaceEmbeddings`
- **Vector store:** `Chroma`
- **Retriever:** `as_retriever()` with a similarity score threshold
- **Prompts:** `PromptTemplate`
- **RAG chain:** `create_retrieval_chain`, `create_stuff_documents_chain`
- **Memory:** `ConversationSummaryMemory`
- **LLM:** `ChatGroq`

## RAG Architecture

```
PDFs / Text files / Web pages
            ↓
     LangChain loaders
            ↓
       Preprocessing
            ↓
  RecursiveCharacterTextSplitter
            ↓
    Hugging Face embeddings
            ↓
   ChromaDB (saved to disk)
            ↓
  Retriever + relevance threshold
            ↓
   Prompt template + Groq LLM
            ↓
  Answer with sources  ↔  Conversation memory
```

## Technologies Used

- Python
- LangChain
- Groq (LLM: `openai/gpt-oss-120b`)
- Hugging Face (embeddings: `all-MiniLM-L6-v2`)
- ChromaDB
- Streamlit
- pypdf, BeautifulSoup, python-dotenv

## Supported Source Types

| Type | Loader | Source shown |
|---|---|---|
| PDF | `PyPDFLoader` | `Employee_Handbook.pdf — Page 1` |
| Text file | `TextLoader` | `IT_Security_Policy.txt` |
| Web page | `WebBaseLoader` | The page URL |

Only public web pages are used.

## Project Structure

```
├── app.py              Streamlit chat app
├── loaders.py          Loads PDFs, text files and web pages
├── preprocess.py       Cleans the text
├── embeddings.py       Splits text into chunks, embedding model
├── vector_store.py     Builds and saves the ChromaDB index
├── retriever.py        Finds relevant chunks
├── rag_chain.py        Prompts, LLM and answer chain
├── memory.py           Conversation memory
├── rag_prompt.txt      Rules for the assistant
├── data/               Sample documents to upload in the app
│   ├── pdf/            Employee_Handbook.pdf, HR_Policies.pdf, Leave_Policy_2026.pdf,
│   │                   NIST_Cybersecurity_Framework_2_0_Enterprise_Guide_4_Pages.pdf
│   ├── text/           IT_Security_Policy.txt
│   └── Web source/     web_source.txt (the web page URL)
├── Knowledge_base/     Created on first upload. Holds uploaded files and urls.txt
├── Vector_store/       Created on first upload. Saved database
├── Processed_data/     Created on first upload. Saved chunks
├── chat_history.json   Created by the app. Chat shown in the Streamlit window
├── rag_strategy.md
├── test_log.md
├── requirements.txt
└── .env.example
```

## Installation

```bash
python -m venv venv
venv\Scripts\activate      
pip install -r requirements.txt
```

## Environment Configuration

Copy `.env.example` to `.env` and add your Groq API key:

```
GROQ_API_KEY=your_groq_api_key
```

Never share or upload the `.env` file.

## LLM Configuration

In `rag_chain.py`:

```python
ChatGroq(model="openai/gpt-oss-120b", temperature=0)
```

Temperature 0 keeps answers consistent.

## Embedding Configuration

In `embeddings.py`:

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Runs locally, with no API key needed
- Chunk size 500, overlap 100

## Vector Database Configuration

In `vector_store.py` and `retriever.py`:

- Database: ChromaDB, saved in `Vector_store/`
- Similarity: cosine
- Top-k: 5 chunks per question
- Relevance threshold: 0.30

## How to Load Documents

The knowledge base starts empty. Add the sample documents from the app sidebar:

1. Run the app with `streamlit run app.py`.
2. **PDF and text files:** click **Upload a file** and select all files from `data/pdf/` and `data/text/`.
3. **Web page:** copy the URL from `data/Web source/web_source.txt`, paste it into **Enter URL** and click **Save URL**.

Uploaded files are saved to `Knowledge_base/`, and URLs to `Knowledge_base/urls.txt`. The folder is created automatically on the first upload. Click **✕** next to a source to remove it.

## How to Build the Knowledge Base

The index is built automatically. Every upload or saved URL loads, cleans, splits and embeds the documents, then saves them to `Vector_store/`. No command is needed.

To rebuild by hand after documents have been uploaded:

```bash
python vector_store.py
```

Do not run this command before uploading anything. With no documents in `Knowledge_base/`, it stops with an error.

To start fresh, delete `Knowledge_base/`, `Vector_store/` and `Processed_data/`, then upload the documents again.

## How Vector Persistence Works

The database is saved in `Vector_store/`. When the app restarts, it loads the saved database instead of embedding everything again. When you build again, only new chunks are embedded.

## How to Run the Application

```bash
streamlit run app.py
```

Or use the command line:

```bash
python rag_chain.py
```

## How to Test the Assistant

First upload all sample documents and the URL, as described in **How to Load Documents**. Then ask these questions. Results are in `test_log.md`.

| Scenario | Question |
|---|---|
| PDF | What are the standard working hours? |
| PDF (multi-page) | What should a practical risk record describe? |
| Text file | What are the IT help desk hours? |
| Web page | What should the maximum password length be? |
| Multiple sources | How long is the probation period? |
| Not available | What is the company's parental leave policy? |
| Low relevance | What is the travel reimbursement limit? |
| Ambiguous | What is the policy? |
| Follow-up | What is the company's leave policy? → What about during probation? |
| Conflicting sources | How many days of annual leave do employees get? |

## Example Questions

- When is a medical certificate needed for sick leave?
- How often are performance reviews conducted?
- Where should I forward phishing emails?
- What should I do if my laptop is stolen?
- How does account lockout protect against brute-force attacks?
- How should backups be protected?

## Known Limitations

- The knowledge base is empty until documents are uploaded, so questions asked before that get the fallback message.
- Files copied into `Knowledge_base/` by hand need `python vector_store.py` to be indexed.
- After editing or deleting a file outside the app, do a fresh build.
- Scanned PDFs (images without text) are not supported.
- Conflict detection depends on the LLM following the prompt.
- Conversation memory resets when the app restarts.
- Needs an internet connection for Groq and web pages.
