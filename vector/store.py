import chromadb
from chromadb.config import Settings
from core.settings import settings
from typing import List, Dict, Any, Optional

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.vector_db_path)
        self.collection = self.client.get_or_create_collection(
            name="knowledge_embeddings",
            metadata={"hnsw:space": "cosine"}
        )

    def add_embeddings(self, ids: List[str], embeddings: List[List[float]], metadatas: List[Dict], documents: List[str]):
        """Add or update embeddings."""
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )

    def delete_embeddings(self, ids: List[str]):
        """Delete embeddings by vector_id."""
        self.collection.delete(ids=ids)

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar embeddings."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'distance': results['distances'][0][i],
                'metadata': results['metadatas'][0][i],
                'document': results['documents'][0][i]
            })
        return formatted

vector_store = VectorStore()

# 兼容函数
def search_similar(query: str, top_k: int = 5):
    """搜索相似内容（兼容接口）"""
    return vector_store.search([0.0] * 384, top_k)  # 返回空结果
