import os
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))


def init_sql():
    with engine.connect() as conn:
        # pgvector viene preinstalado en el PostgreSQL de Railway
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                product_id  TEXT PRIMARY KEY,
                embedding   vector(768)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS search_logs (
                id        SERIAL PRIMARY KEY,
                query     TEXT NOT NULL,
                n_results INTEGER DEFAULT 0,
                ts        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()


def upsert_embedding(product_id: str, vector: list[float]):
    vec_str = "[" + ",".join(str(v) for v in vector) + "]"
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO products (product_id, embedding)
            VALUES (:pid, :vec::vector)
            ON CONFLICT (product_id)
            DO UPDATE SET embedding = EXCLUDED.embedding
        """), {"pid": product_id, "vec": vec_str})
        conn.commit()


def semantic_search(vector: list[float], top_k: int = 5) -> list[tuple[str, float]]:
    vec_str = "[" + ",".join(str(v) for v in vector) + "]"
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT product_id,
                   1 - (embedding <=> :vec::vector) AS score
            FROM products
            ORDER BY embedding <=> :vec::vector
            LIMIT :k
        """), {"vec": vec_str, "k": top_k}).fetchall()
    return [(r[0], float(r[1])) for r in rows]


def log_search(query: str, n_results: int):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO search_logs (query, n_results) VALUES (:q, :n)"),
            {"q": query, "n": n_results},
        )
        conn.commit()


def get_search_stats() -> list[tuple]:
    with engine.connect() as conn:
        total  = conn.execute(text("SELECT COUNT(*) FROM search_logs")).scalar()
        today  = conn.execute(text(
            "SELECT COUNT(*) FROM search_logs WHERE ts::date = CURRENT_DATE"
        )).scalar()
        top    = conn.execute(text("""
            SELECT query FROM search_logs
            GROUP BY query ORDER BY COUNT(*) DESC LIMIT 1
        """)).scalar()
    return [
        ("Total búsquedas", total or 0),
        ("Búsquedas hoy",   today or 0),
        ("Query más popular", top or "—"),
    ]
