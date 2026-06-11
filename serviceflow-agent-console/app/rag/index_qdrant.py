from app.rag.qdrant_retriever import index_knowledge_base


if __name__ == "__main__":
    count = index_knowledge_base(reset=True)
    print(f"Indexed {count} knowledge chunks into Qdrant")
