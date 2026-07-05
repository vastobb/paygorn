from fastapi import FastAPI, HTTPException
import sqlite3
import secrets
import os

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(__file__), "keys.db")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "change_this_to_something_long_and_random")
DEFAULT_USES = 5


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            uses_left INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


@app.get("/")
def root():
    return {"status": "ok", "service": "ascii-key-server"}


@app.post("/generate")
def generate(secret: str, uses: int = DEFAULT_USES):
    """
    Admin-only endpoint. Call this yourself (or have your ad-locker backend
    call it) to mint a new key. Requires ADMIN_SECRET so randoms can't mint
    free keys directly.
    """
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    key = secrets.token_hex(8)  # 16-char hex key
    conn = get_db()
    conn.execute("INSERT INTO keys (key, uses_left) VALUES (?, ?)", (key, uses))
    conn.commit()
    conn.close()
    return {"key": key, "uses": uses}


@app.get("/check")
def check(key: str):
    conn = get_db()
    row = conn.execute("SELECT uses_left FROM keys WHERE key = ?", (key,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "uses_left": row[0]}


@app.post("/consume")
def consume(key: str):
    """
    Called by the client right before a conversion actually starts.
    Atomically decrements uses_left if > 0, otherwise rejects.
    """
    conn = get_db()
    row = conn.execute("SELECT uses_left FROM keys WHERE key = ?", (key,)).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Invalid key")

    uses_left = row[0]
    if uses_left <= 0:
        conn.close()
        raise HTTPException(status_code=403, detail="Key has no uses left")

    conn.execute("UPDATE keys SET uses_left = uses_left - 1 WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    return {"ok": True, "uses_left": uses_left - 1}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
