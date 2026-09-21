import json
import os
import threading
from pathlib import Path

import numpy as np

DB_PATH = Path(__file__).parent / "embeddings.json"
_lock = threading.Lock()


def load_db() -> dict:
    """Return {name: [embedding, ...]}; empty dict if missing or corrupt."""
    with _lock:
        if not DB_PATH.exists():
            return {}
        try:
            return json.loads(DB_PATH.read_text())
        except json.JSONDecodeError:
            return {}


def save_db(db: dict) -> None:
    """Atomic write: temp file, then replace."""
    with _lock:
        tmp = DB_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(db))
        os.replace(tmp, DB_PATH)


def add_embedding(name: str, embedding: list) -> None:
    db = load_db()
    db.setdefault(name, []).append([float(x) for x in embedding])
    save_db(db)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def best_match(embedding, db: dict, threshold: float = 0.40):
    """Return (name, score) if the best cosine similarity >= threshold,
    else (None, best_score) so the UI can still show the score."""
    query = np.asarray(embedding, dtype=np.float32)
    best_name, best_score = None, 0.0
    for name, embeddings in db.items():
        for stored in embeddings:
            score = _cosine(query, np.asarray(stored, dtype=np.float32))
            if score > best_score:
                best_name, best_score = name, score
    if best_score >= threshold:
        return best_name, best_score
    return None, best_score
