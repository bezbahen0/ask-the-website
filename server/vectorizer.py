from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceBgeEmbeddings


class Vectorizer:
    def __init__(self, model_name="BAAI/bge-m3"):
        self.embedding_model = HuggingFaceBgeEmbeddings(model_name=model_name)

    def get_relevant_chunks(self, query, documents, page_url):
        db = Chroma.from_documents(
            documents, self.embedding_model
        )
        docs = db.similarity_search(query, filter={"source": page_url})
        return [d.page_content for d in docs]
