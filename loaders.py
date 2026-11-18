#1


from pathlib import Path
from bs4 import SoupStrainer
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader


files_dir=Path("Knowledge_base")

# Main content only
MAIN_CONTENT = SoupStrainer(["title", "meta", "article"])
# One line per HTML element
WEB_TEXT = {"separator": "\n", "strip": True}


def load_web(url):
    docs = WebBaseLoader(url, bs_kwargs={"parse_only": MAIN_CONTENT}, bs_get_text_kwargs=WEB_TEXT).load()
    title = docs[0].metadata.get("title", "") if docs else ""
    # No <article>: whole page
    if all(d.page_content.strip() == title.strip() for d in docs):
        docs = WebBaseLoader(url, bs_get_text_kwargs=WEB_TEXT).load()
    return docs


def load_document():
    pdf=list(files_dir.glob('*.pdf'))
    txt = [file for file in files_dir.glob('*.txt') if file.name!='urls.txt']
    pdf_docs = {}
    txt_docs={}
    urls_docs=[]
    for i in pdf:
        loader = PyPDFLoader(str(i))
        pdf_docs[i.name]=loader.load()
    for i in txt:
        loader = TextLoader(str(i), encoding="utf-8")
        txt_docs[i.name]=loader.load()
    url_file = files_dir/"urls.txt"
    urls = []
    if url_file.exists():
        urls=[line.strip() for line in url_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    for url in urls:
        try:
            urls_docs.extend(load_web(url))
        except Exception as e:
            print(f"Skipped {url}: {e}")    
            
    return {
        "pdf":pdf_docs,
        "txt":txt_docs,
        "url":urls_docs
    }



