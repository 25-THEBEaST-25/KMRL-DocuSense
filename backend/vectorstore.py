"""
Step 4 of the pipeline: store/retrieve chunk embeddings in ChromaDB.
"""
import os
import chromadb
from dotenv import load_dotenv
from embeddings import embed_texts, embed_query

load_dotenv()
CHROMA_DIR = os.getenv("CHROMA_DIR", "../data/chroma_db")

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _client.get_or_create_collection(
            name="kochi_metro_docs",
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def add_chunks(doc_id: int, chunks: list[str], metadata: dict):
    """metadata example: {"filename": "...", "category": "Maintenance", "station": "Aluva"}"""
    if not chunks:
        return
    collection = get_collection()
    ids = [f"doc{doc_id}_chunk{i}" for i in range(len(chunks))]
    embeddings = embed_texts(chunks)
    metadatas = [{**metadata, "doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)


def search(query: str, top_k: int = 5, where: dict = None):
    collection = get_collection()
    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,  # e.g. {"category": "Maintenance"}
    )
    return results


def delete_doc_chunks(doc_id: int):
    collection = get_collection()
    collection.delete(where={"doc_id": doc_id})
