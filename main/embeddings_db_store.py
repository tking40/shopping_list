import sqlite3
import numpy as np
from typing import Optional, List, Dict
import io
import time
import threading


class EmbeddingsDBStore:
    def __init__(self, db_path: str = "embeddings.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._create_table()

    @property
    def conn(self):
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return self._local.conn

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT UNIQUE,
                    embedding BLOB,
                    created_at REAL,
                    updated_at REAL
                )
            """
            )
            # Add index for better performance
            self.conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_text ON embeddings(text)
            """
            )

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        try:
            cursor = self.conn.execute(
                "SELECT embedding FROM embeddings WHERE text = ?", (text,)
            )
            row = cursor.fetchone()
            if row:
                return np.load(io.BytesIO(row[0]), allow_pickle=True)
            return None
        except Exception as e:
            print(f"Error retrieving embedding for '{text}': {e}")
            return None

    def add_embedding(self, text: str, embedding: np.ndarray):
        try:
            out = io.BytesIO()
            np.save(out, embedding)
            now = time.time()
            with self.conn:
                self.conn.execute(
                    "INSERT OR REPLACE INTO embeddings (text, embedding, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (text, out.getvalue(), now, now),
                )
        except Exception as e:
            print(f"Error storing embedding for '{text}': {e}")

    def bulk_get_embeddings(self, texts: List[str]) -> Dict[str, np.ndarray]:
        if not texts:
            return {}

        try:
            placeholders = ",".join("?" for _ in texts)
            cursor = self.conn.execute(
                f"SELECT text, embedding FROM embeddings WHERE text IN ({placeholders})",
                texts,
            )
            result = {}
            for text, blob in cursor.fetchall():
                result[text] = np.load(io.BytesIO(blob), allow_pickle=True)
            return result
        except Exception as e:
            print(f"Error bulk retrieving embeddings: {e}")
            return {}

    def close(self):
        if hasattr(self._local, "conn"):
            self._local.conn.close()

    def get_all_texts(self) -> List[str]:
        """Return a list of all text items stored in the database."""
        try:
            cursor = self.conn.execute("SELECT text FROM embeddings ORDER BY text")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving all texts: {e}")
            return []

    def print_all_texts(self):
        """Print all text items in the database in a readable format."""
        texts = self.get_all_texts()
        if not texts:
            print("Store is empty - no text items found.")
        else:
            print(f"Store contains {len(texts)} text items:")
            for i, text in enumerate(texts, 1):
                print(f"  {i}. {text}")

    def remove_embedding(self, text: str) -> bool:
        """Remove an embedding by text key from the database.

        Args:
            text: The text key of the embedding to remove

        Returns:
            True if the embedding was found and removed, False otherwise
        """
        try:
            with self.conn:
                cursor = self.conn.execute(
                    "DELETE FROM embeddings WHERE text = ?", (text,)
                )
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error removing embedding for '{text}': {e}")
            return False

    def remove_embeddings(self, texts: List[str]) -> int:
        """Remove multiple embeddings by text keys from the database.

        Args:
            texts: List of text keys to remove

        Returns:
            Number of embeddings successfully removed
        """
        if not texts:
            return 0

        try:
            removed_count = 0
            with self.conn:
                for text in texts:
                    cursor = self.conn.execute(
                        "DELETE FROM embeddings WHERE text = ?", (text,)
                    )
                    if cursor.rowcount > 0:
                        removed_count += 1
            return removed_count
        except Exception as e:
            print(f"Error removing embeddings: {e}")
            return 0

    def clear_all_embeddings(self) -> int:
        """Remove all embeddings from the database.

        Returns:
            Number of embeddings removed
        """
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT COUNT(*) FROM embeddings")
                count = cursor.fetchone()[0]
                self.conn.execute("DELETE FROM embeddings")
                return count
        except Exception as e:
            print(f"Error clearing all embeddings: {e}")
            return 0

    def __str__(self):
        """Return a string listing all (text, embedding) pairs, or 'Store is empty.' if empty."""
        cursor = self.conn.execute("SELECT text, embedding FROM embeddings")
        rows = cursor.fetchall()
        import numpy as np
        import io

        if not rows:
            return "Store is empty."
        out = ["Current contents of the store:"]
        for text, blob in rows:
            emb = np.load(io.BytesIO(blob), allow_pickle=True)
            out.append(f"  {text}: {emb}")
        return "\n".join(out)
