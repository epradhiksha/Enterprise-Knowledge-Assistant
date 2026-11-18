#2
import re
from collections import Counter
from langchain_core.documents import Document

# Heading anchors
SYMBOL_LINES = {"¶", "#", "§", "↩", "^", "|", "»", "«", "›", "‹"}

# Interface-only lines
INTERFACE_LINE = re.compile(
    r"^(skip to (main )?content|back to top|(accept|reject) all cookies"
    r"|cookie (preferences|settings)|share this article|follow us on.*"
    r"|.*all rights reserved\.?|subscribe now)$",
    re.IGNORECASE,
)


def remove_headers_footers(pages, edge=3):
    """Drop lines repeated at the top or bottom of most pages of one PDF."""
    if len(pages) < 2:
        return pages

    def key(line):
        # Ignore page numbers
        return re.sub(r"\d+", "#", line.strip().lower())

    page_lines = [[l for l in p.splitlines() if l.strip()] for p in pages]
    counts = Counter()
    for lines in page_lines:
        counts.update({key(l) for l in lines[:edge] + lines[-edge:]})

    min_pages = max(2, (len(pages) + 1) // 2)
    repeated = {k for k, n in counts.items() if n >= min_pages}

    cleaned = []
    for lines in page_lines:
        last = len(lines) - edge
        cleaned.append("\n".join(
            l for i, l in enumerate(lines)
            if not ((i < edge or i >= last) and key(l) in repeated)
        ))
    return cleaned


def clean_text(text):
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Remove repeated spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Reduce excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)


    return text.strip()

def clean_web_text(text):
    # Content phrases ("log in", "privacy policy") and URLs are kept
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line in SYMBOL_LINES or INTERFACE_LINE.match(line):
            continue
        lines.append(line)

    text = " ".join(lines)
    # Re-attach punctuation
    text = re.sub(r"\s+([.,;:!?)\]}])", r"\1", text)
    text = re.sub(r"([(\[{])\s+", r"\1", text)

    return re.sub(r"\s+", " ", text).strip()


def preprocess(data):
    processed = {
        "pdf": {},
        "txt": {},
        "url": []
    }
    for filename,content in data['pdf'].items():
        processed['pdf'][filename]=[]
        pages = remove_headers_footers([i.page_content for i in content])

        for i, page in zip(content, pages):
            cleaned = clean_text(page)

            if cleaned:
                processed["pdf"][filename].append(
                    Document(
                        page_content=cleaned,
                        metadata=i.metadata
                    )
                )
    for txtname, doc in data['txt'].items():
        processed['txt'][txtname]=[]

        for i in doc:
            cleaned = clean_text(i.page_content)

            if cleaned : 
                processed['txt'][txtname].append(
                    Document(
                        page_content=cleaned,
                        metadata = i.metadata
                    )
                )

    for url in data['url']:
        cleaned = clean_web_text(url.page_content)

        if cleaned:
            processed["url"].append(
                Document(
                    page_content=cleaned,
                    metadata=url.metadata
                )
            )

    return processed
