from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings


class Vectorizer:
    def __init__(self, model_name="BAAI/bge-m3"):
        model_kwargs = {"device": "cpu"}

        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=model_name, model_kwargs=model_kwargs
        )

    def get_relevant_documents(self, query, documents, page_url):
        db = Chroma.from_documents(documents, self.embedding_model)

        retriever = db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "score_threshold": 0.15,
                "filter": {"source": page_url},
                "k": len(documents),
            },
        )
        docs = retriever.get_relevant_documents(query)
        print(f"Надено чанков: {len(docs)}")
        # docs = db.similarity_search_with_relevance_scores(
        #    query, filter={"source": page_url}
        # )

        return docs
