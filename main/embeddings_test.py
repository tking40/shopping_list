import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
from embeddings import GroceryEmbeddings


class TestGroceryEmbeddings(unittest.TestCase):
    def setUp(self):
        # Patch SentenceTransformer to avoid loading real models
        patcher = patch("embeddings.SentenceTransformer")
        self.addCleanup(patcher.stop)
        self.mock_transformer = patcher.start()
        # Mock encode to return deterministic vectors
        self.mock_transformer.return_value.encode.side_effect = (
            lambda text, convert_to_numpy=True: np.array([len(text), 1.0])
        )
        self.emb = GroceryEmbeddings()

    def test_generate_embedding_and_cache(self):
        text = "apple"
        emb1 = self.emb.generate_embedding(text)
        emb2 = self.emb.generate_embedding(text)
        self.assertTrue(np.array_equal(emb1, emb2))
        self.assertIn(text, self.emb.embeddings_cache)

    def test_find_similar_items(self):
        items = ["apple", "banana", "carrot"]
        query = "apple"
        results = self.emb.find_similar_items(query, items, top_k=2)
        self.assertEqual(len(results), 2)
        self.assertIn("item", results[0])
        self.assertIn("similarity", results[0])
        # Since all embeddings are based on len(text), apple should be most similar to itself
        self.assertEqual(results[0]["item"], "apple")

    @patch("numpy.save")
    def test_save_embeddings(self, mock_save):
        self.emb.embeddings_cache = {"foo": np.array([1, 2, 3])}
        self.emb.save_embeddings("dummy.npy")
        mock_save.assert_called_once()

    @patch("os.path.exists", return_value=True)
    @patch("numpy.load")
    def test_load_embeddings(self, mock_load, mock_exists):
        mock_load.return_value.item.return_value = {"bar": np.array([4, 5, 6])}
        self.emb.load_embeddings("dummy.npy")
        self.assertIn("bar", self.emb.embeddings_cache)


if __name__ == "__main__":
    unittest.main()
