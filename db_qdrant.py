import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

COLLECTION = "products"
DIM = 768  # text-embedding-004 output dimension

_client = None


def _is_local(url: str) -> bool:
    return any(h in url for h in ("localhost", "127.0.0.1", "0.0.0.0"))


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY") or None

        # Railway (y cualquier proxy cloud) termina TLS aunque la URL
        # interna diga http://. Corregir siempre salvo entorno local.
        if not _is_local(url) and url.startswith("http://"):
            url = url.replace("http://", "https://", 1)

        _client = QdrantClient(
            url=url,
            api_key=api_key,
            prefer_grpc=False,  # REST sobre HTTPS; gRPC usa puerto 6334
        )
    return _client


def init_qdrant():
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION not in existing:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )


def index_product(product_id: str, vector: list[float], payload: dict):
    client = _get_client()
    client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(id=product_id, vector=vector, payload=payload)],
    )


def semantic_search(vector: list[float], top_k: int = 5):
    client = _get_client()
    return client.search(
        collection_name=COLLECTION,
        query_vector=vector,
        limit=top_k,
    )
