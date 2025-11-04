from agent.rag.retriever import Retriever
from agent.prompts import SUMMARY_PROMPT
import textwrap

class RAGPipeline:
    def __init__(self, llm, memory):
        self.llm = llm
        self.memory = memory
        self.retriever = Retriever(memory)

    def query(self, user_query: str):
        # retrieve relevant chunks
        chunks = self.retriever.retrieve(user_query, top_k=3)
        combined = "\n\n".join(chunks) if chunks else ""
        prompt = f"{user_query}\n\nRelevant resume fragments:\n{combined}\n\nAnswer concisely."
        resp = self.llm.generate(prompt)
        return textwrap.fill(resp.strip(), width=100)
