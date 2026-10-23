from pathlib import Path
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHROMA_PATH = PROJECT_ROOT / "chroma_db"

chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
collection = chroma_client.get_or_create_collection(name="medical_reports")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def add_chunks(
    patient_code: str,
    report_id: int,
    report_title: str,
    chunks: list[str],
    report_date: datetime,
) -> None:
    """Embed and persist report chunks in the medical reports collection."""
    if not chunks:
        return

    report_date_iso = report_date.isoformat()
    dated_chunks = [
        f"[Report: {report_title}, dated {report_date_iso}] {chunk}"
        for chunk in chunks
    ]
    embeddings = embedding_model.encode(dated_chunks).tolist()
    collection.upsert(
        ids=[f"{report_id}_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=dated_chunks,
        metadatas=[
            {
                "patient_code": patient_code,
                "report_id": report_id,
                "report_title": report_title,
                "report_date": report_date_iso,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ],
    )


def query_chunks(
    patient_code: str,
    query: str,
    top_k: int = 5,
) -> list[dict]:
    """Return the closest report chunks for a patient and query."""
    if top_k <= 0:
        return []

    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        where={"patient_code": patient_code},
        include=["documents", "metadatas", "distances"],
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    results = [
        {
            "text": document,
            "report_id": metadata["report_id"],
            "report_title": metadata["report_title"],
            "report_date": metadata["report_date"],
            "chunk_index": metadata["chunk_index"],
            "distance": distance,
        }
        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
            strict=True,
        )
    ]
    return sorted(results, key=lambda result: result["report_date"], reverse=True)
