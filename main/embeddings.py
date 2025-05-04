from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
from typing import List, Dict, Union
import os


class GroceryEmbeddings:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embeddings model.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model = SentenceTransformer(model_name)
        self.embeddings_cache = {}

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a given text.

        Args:
            text: Text to generate embedding for

        Returns:
            numpy array containing the embedding
        """
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]

        embedding = self.model.encode(text, convert_to_numpy=True)
        self.embeddings_cache[text] = embedding
        return embedding

    def find_similar_items(
        self, query: str, items: List[str], top_k: int = 5
    ) -> List[Dict[str, Union[str, float]]]:
        """Find similar items to the query from a list of items.

        Args:
            query: The search query
            items: List of items to search through
            top_k: Number of similar items to return

        Returns:
            List of dictionaries containing similar items and their similarity scores
        """
        query_embedding = self.generate_embedding(query)
        item_embeddings = [self.generate_embedding(item) for item in items]

        # Calculate cosine similarities
        similarities = [
            np.dot(query_embedding, item_embedding)
            / (np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding))
            for item_embedding in item_embeddings
        ]

        # Get top k similar items
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [
            {"item": items[idx], "similarity": similarities[idx]} for idx in top_indices
        ]

    def save_embeddings(self, filepath: str):
        """Save the embeddings cache to a file.

        Args:
            filepath: Path to save the embeddings to
        """
        np.save(filepath, self.embeddings_cache)

    def load_embeddings(self, filepath: str):
        """Load embeddings from a file.

        Args:
            filepath: Path to load the embeddings from
        """
        if os.path.exists(filepath):
            self.embeddings_cache = np.load(filepath, allow_pickle=True).item()
