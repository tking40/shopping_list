import unittest
import numpy as np
import os
from embeddings_db_store import EmbeddingsDBStore


class TestEmbeddingsDBStore(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for testing
        self.test_db_path = "test_embeddings.db"
        self.store = EmbeddingsDBStore(self.test_db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_add_and_get_embedding(self):
        text = "apple"
        embedding = np.random.rand(10)
        self.store.add_embedding(text, embedding)
        loaded = self.store.get_embedding(text)
        np.testing.assert_array_almost_equal(embedding, loaded)

    def test_get_nonexistent_embedding(self):
        self.assertIsNone(self.store.get_embedding("not_in_db"))

    def test_bulk_get_embeddings(self):
        texts = ["a", "b", "c"]
        embeddings = [np.random.rand(5) for _ in texts]
        for t, e in zip(texts, embeddings):
            self.store.add_embedding(t, e)
        result = self.store.bulk_get_embeddings(texts)
        for t, e in zip(texts, embeddings):
            np.testing.assert_array_almost_equal(result[t], e)

    def test_str_empty(self):
        self.assertIn("Store is empty.", str(self.store))

    def test_str_nonempty(self):
        self.store.add_embedding("foo", np.array([1.0, 2.0]))
        self.store.add_embedding("bar", np.array([3.0, 4.0]))
        s = str(self.store)
        self.assertIn("Current contents of the store:", s)
        self.assertIn("foo", s)
        self.assertIn("bar", s)


if __name__ == "__main__":
    unittest.main()
