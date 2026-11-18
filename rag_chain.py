from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableBranch, RunnableLambda

from memory import create_memory as create_summary_memory
from retriever import add_citations, get_retriever, validate_query

load_dotenv()


FALLBACK_MESSAGE = (
    "I could not find sufficient information in the indexed knowledge base "
    "to answer this question."
)

# Same layout as the prompt's "insufficient information" answer
FALLBACK = f"Answer:\n{FALLBACK_MESSAGE}\n\nSources:\nNone"

with open("rag_prompt.txt","r",encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


# Turns "What about during probation?" into a question the retriever can search
CONDENSE_PROMPT = PromptTemplate.from_template(
"""Given the conversation summary and a follow-up question, rewrite the follow-up
as a standalone question that can be searched in a knowledge base.
If the question is already standalone, return it unchanged.
Return only the question, nothing else.

Conversation summary:
{chat_history}

Follow-up question:
{input}

"""
)

ANSWER_PROMPT = PromptTemplate.from_template(
"""{system_prompt}

Conversation summary:
{chat_history}

Retrieved knowledge-base context:
{context}

Current question:
{input}

Answer using the retrieved context and follow the system prompt's grounding rules.
Do not treat the conversation summary as factual evidence."""
).partial(system_prompt=SYSTEM_PROMPT)

# How each retrieved chunk is shown to the LLM inside {context}
DOCUMENT_PROMPT = PromptTemplate.from_template("Source: {citation}\n{page_content}")

condense_chain = CONDENSE_PROMPT | llm | StrOutputParser()


def create_memory():
    return create_summary_memory(llm)


def dedupe_sources(answer):
    """List each source only once under "Sources:", even if the LLM repeats it."""
    head, marker, tail = answer.rpartition("Sources:")
    if not marker:
        return answer

    seen = set()
    lines = []
    for line in tail.splitlines():
        label = line.strip().lstrip("-").strip()
        if line.strip().startswith("-"):
            if label in seen:
                continue
            seen.add(label)
        lines.append(line)
    return head + marker + "\n".join(lines)


def standalone_question(inputs):
    if not inputs.get("chat_history"):
        return inputs["input"]
    return condense_chain.invoke(inputs).strip()


@lru_cache(maxsize=1)
def create_conversation_chain():
    history_aware_retriever = (
        RunnableLambda(standalone_question)
        | get_retriever()
        | RunnableLambda(add_citations)
    )

    answer_chain = create_stuff_documents_chain(
        llm,
        ANSWER_PROMPT,
        document_prompt=DOCUMENT_PROMPT,
        document_separator="\n\n",
    )

    # Nothing passed the relevance threshold -> fallback, the LLM is never called
    grounded_answer = RunnableBranch(
        (lambda x: not x["context"], RunnableLambda(lambda _: FALLBACK)),
        answer_chain,
    )

    return create_retrieval_chain(history_aware_retriever, grounded_answer)


def answer_query(query, memory=None):
    """Returns (answer, retrieved_sources)."""
    valid, query = validate_query(query)
    if not valid:
        return query, []

    try:
        chat_history = memory.load_memory_variables({})["chat_history"] if memory else ""

        response = create_conversation_chain().invoke({
            "input": query,
            "chat_history": chat_history
        })

        answer = dedupe_sources(response["answer"])
        sources = list(dict.fromkeys(
            doc.metadata["citation"] for doc in response["context"]
        ))

        if memory:
            memory.save_context({"question": query}, {"answer": answer})

        return answer, sources

    except Exception as e:
        return f"Sorry, an error occurred: {type(e).__name__}: {e}", []


if __name__ == "__main__":
    memory = create_memory()
    print("Enterprise Knowledge Assistant (type 'exit' to quit)")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        answer, sources = answer_query(question, memory)
        print(f"\nAssistant:\n{answer}")
        print(f"\n[retrieved: {', '.join(sources) or 'none'}]")
