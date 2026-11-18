from langchain_classic.memory import ConversationSummaryMemory


def create_memory(llm):
    return ConversationSummaryMemory(
        llm=llm,
        memory_key="chat_history",
        input_key="question",
        output_key="answer",
        return_messages=False
    )
