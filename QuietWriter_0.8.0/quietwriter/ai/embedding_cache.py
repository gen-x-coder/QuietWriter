from __future__ import annotations
import json, math, sqlite3
from pathlib import Path


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b): return -1.0
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else -1.0


class EmbeddingCache:
    """Kleine persistente cache voor verhaal-embeddings; veilig te openen vanuit een worker-thread."""
    def __init__(self, path: Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn=sqlite3.connect(self.path)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS embeddings(
            path TEXT, model TEXT, mtime REAL, vector TEXT,
            PRIMARY KEY(path, model)
        )''')
        self.conn.commit()

    def get(self, path: str, model: str, mtime: float):
        row=self.conn.execute('SELECT mtime,vector FROM embeddings WHERE path=? AND model=?',(path,model)).fetchone()
        if not row or abs(float(row[0] or 0)-float(mtime or 0)) > 0.001: return None
        try: return json.loads(row[1])
        except Exception: return None

    def put(self, path: str, model: str, mtime: float, vector: list[float]):
        self.conn.execute('INSERT OR REPLACE INTO embeddings(path,model,mtime,vector) VALUES(?,?,?,?)',
                          (path,model,float(mtime or 0),json.dumps(vector)))
        self.conn.commit()

    def close(self):
        self.conn.close()
