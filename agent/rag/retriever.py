class Retriever:
    def __init__(self, memory):
        self.memory = memory

    def retrieve(self, query: str, top_k: int = 3):
        return self.memory.get_top_chunks(query, top_k=top_k)
