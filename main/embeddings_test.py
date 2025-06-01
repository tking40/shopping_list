import unittest
import numpy as np
import tempfile
import os

try:
    from embeddings import GroceryEmbeddings
except ImportError:
    from main.embeddings import GroceryEmbeddings
try:
    from embeddings_db_store import EmbeddingsDBStore
except ImportError:
    from main.embeddings_db_store import EmbeddingsDBStore


class EmbeddingsDBStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.store = EmbeddingsDBStore(self.db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_add_and_get_embedding(self):
        text = "test text"
        embedding = np.array([1.0, 2.0, 3.0])

        # Add embedding
        self.store.add_embedding(text, embedding)

        # Retrieve embedding
        retrieved = self.store.get_embedding(text)
        np.testing.assert_array_equal(retrieved, embedding)

    def test_get_nonexistent_embedding(self):
        result = self.store.get_embedding("nonexistent")
        self.assertIsNone(result)

    def test_bulk_operations(self):
        texts = ["apple", "banana", "cherry"]
        embeddings = [np.array([i, i + 1, i + 2]) for i in range(3)]

        # Add embeddings
        for text, emb in zip(texts, embeddings):
            self.store.add_embedding(text, emb)

        # Bulk retrieve
        result = self.store.bulk_get_embeddings(texts)

        self.assertEqual(len(result), 3)
        for i, text in enumerate(texts):
            np.testing.assert_array_equal(result[text], embeddings[i])

    def test_empty_bulk_get(self):
        result = self.store.bulk_get_embeddings([])
        self.assertEqual(result, {})


class GroceryEmbeddingsTest(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.embeddings = GroceryEmbeddings(db_path=self.db_path)

    def tearDown(self):
        self.embeddings.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_generate_embedding_basic(self):
        text = "apple"
        embedding = self.embeddings.generate_embedding(text)

        self.assertIsInstance(embedding, np.ndarray)
        self.assertGreater(embedding.size, 0)

    def test_generate_embedding_database_reuse(self):
        text = "banana"

        # First call - should generate and optionally save
        embedding1 = self.embeddings.generate_embedding(text, auto_save=True)

        # Second call - should use database
        embedding2 = self.embeddings.generate_embedding(text)

        np.testing.assert_array_equal(embedding1, embedding2)

    def test_generate_embedding_validation(self):
        # Test empty string
        with self.assertRaises(ValueError):
            self.embeddings.generate_embedding("")

        # Test None
        with self.assertRaises(ValueError):
            self.embeddings.generate_embedding(None)

        # Test non-string
        with self.assertRaises(ValueError):
            self.embeddings.generate_embedding(123)

        # Test whitespace only
        with self.assertRaises(ValueError):
            self.embeddings.generate_embedding("   ")

    def test_text_normalization(self):
        # These should produce the same embedding due to normalization
        embedding1 = self.embeddings.generate_embedding("Apple", auto_save=True)
        embedding2 = self.embeddings.generate_embedding("  APPLE  ")
        embedding3 = self.embeddings.generate_embedding("apple")

        np.testing.assert_array_equal(embedding1, embedding2)
        np.testing.assert_array_equal(embedding1, embedding3)

    def test_find_similar_items_basic(self):
        items = ["apple", "banana", "orange", "grape"]
        results = self.embeddings.find_similar_items("fruit", items, top_k=2)

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("item", result)
            self.assertIn("similarity", result)
            self.assertIn(result["item"], items)
            self.assertIsInstance(result["similarity"], float)

    def test_find_similar_items_edge_cases(self):
        # Empty items list
        results = self.embeddings.find_similar_items("query", [], top_k=5)
        self.assertEqual(results, [])

        # Zero top_k
        results = self.embeddings.find_similar_items("query", ["item1"], top_k=0)
        self.assertEqual(results, [])

        # top_k larger than items
        items = ["apple", "banana"]
        results = self.embeddings.find_similar_items("fruit", items, top_k=10)
        self.assertEqual(len(results), 2)

    def test_save_load_embeddings(self):
        # Generate some embeddings and save to database
        texts = ["apple", "banana", "cherry"]
        for text in texts:
            self.embeddings.generate_embedding(text, auto_save=True)

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".npy")
        temp_path = temp_file.name
        temp_file.close()

        try:
            self.embeddings.save_embeddings(temp_path)

            # Create new instance and load
            new_embeddings = GroceryEmbeddings()
            new_embeddings.load_embeddings(temp_path)

            # Verify loaded embeddings match
            for text in texts:
                original = self.embeddings.generate_embedding(text)
                loaded = new_embeddings.generate_embedding(text)
                np.testing.assert_array_equal(original, loaded)

            new_embeddings.close()
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_generate_embedding_auto_save_false(self):
        """Test that embeddings are not saved to DB by default."""
        text = "test item"

        # Generate without auto_save (default)
        embedding = self.embeddings.generate_embedding(text)

        # Should not be in database
        db_embedding = self.embeddings.db_store.get_embedding(text)
        self.assertIsNone(db_embedding)

    def test_generate_embedding_auto_save_true(self):
        """Test that embeddings are saved to DB when auto_save=True."""
        text = "test item"

        # Generate with auto_save=True
        embedding = self.embeddings.generate_embedding(text, auto_save=True)

        # Should be in database
        db_embedding = self.embeddings.db_store.get_embedding(text)
        self.assertIsNotNone(db_embedding)
        np.testing.assert_array_equal(db_embedding, embedding)

    def test_save_embedding_to_db(self):
        """Test explicit saving of embedding to database."""
        text = "explicit save test"

        # Generate embedding (not saved to DB)
        embedding = self.embeddings.generate_embedding(text)

        # Verify not in DB initially
        self.assertIsNone(self.embeddings.db_store.get_embedding(text))

        # Explicitly save to DB
        result = self.embeddings.save_embedding_to_db(text)
        self.assertTrue(result)

        # Now should be in DB
        db_embedding = self.embeddings.db_store.get_embedding(text)
        self.assertIsNotNone(db_embedding)
        np.testing.assert_array_equal(db_embedding, embedding)

    def test_save_embeddings_to_db_bulk(self):
        """Test bulk saving of embeddings to database."""
        texts = ["bulk1", "bulk2", "bulk3"]

        # Save bulk embeddings
        saved_count = self.embeddings.save_embeddings_to_db(texts)
        self.assertEqual(saved_count, 3)

        # Verify all are in database
        for text in texts:
            stored_embedding = self.embeddings.db_store.get_embedding(text)
            self.assertIsNotNone(stored_embedding)

        self.embeddings.close()

    def test_remove_embedding_single(self):
        """Test removing a single embedding from database."""
        text = "remove_test"

        # Add embedding to database
        self.embeddings.generate_embedding(text, auto_save=True)

        # Verify it exists
        self.assertIsNotNone(self.embeddings.db_store.get_embedding(text))

        # Remove it
        removed = self.embeddings.remove_embedding(text)
        self.assertTrue(removed)

        # Verify it's gone from database
        self.assertIsNone(self.embeddings.db_store.get_embedding(text))

        # Verify removing non-existent item returns False
        removed_again = self.embeddings.remove_embedding(text)
        self.assertFalse(removed_again)

        self.embeddings.close()

    def test_remove_embedding_not_in_db(self):
        """Test removing an embedding that's not in database."""
        text = "not_in_db"

        # Generate but don't save to database
        self.embeddings.generate_embedding(text, auto_save=False)

        # Verify it's not in database
        self.assertIsNone(self.embeddings.db_store.get_embedding(text))

        # Remove it
        removed = self.embeddings.remove_embedding(text)
        self.assertFalse(removed)  # False because not in database

        self.embeddings.close()

    def test_remove_embeddings_bulk(self):
        """Test bulk removal of embeddings."""
        texts = ["bulk_remove1", "bulk_remove2", "bulk_remove3"]

        # Add all to database
        for text in texts:
            self.embeddings.generate_embedding(text, auto_save=True)

        # Verify all exist
        for text in texts:
            self.assertIsNotNone(self.embeddings.db_store.get_embedding(text))

        # Remove bulk
        removed_count = self.embeddings.remove_embeddings(texts)
        self.assertEqual(removed_count, 3)

        # Verify all are gone
        for text in texts:
            self.assertIsNone(self.embeddings.db_store.get_embedding(text))

        self.embeddings.close()

    def test_remove_embeddings_mixed(self):
        """Test bulk removal with mix of database and non-database items."""
        db_texts = ["db_item1", "db_item2"]
        non_db_texts = ["non_db_item1", "non_db_item2"]

        # Add some to database
        for text in db_texts:
            self.embeddings.generate_embedding(text, auto_save=True)

        # Generate some but don't save to database
        for text in non_db_texts:
            self.embeddings.generate_embedding(text, auto_save=False)

        # Remove all
        all_texts = db_texts + non_db_texts
        removed_count = self.embeddings.remove_embeddings(all_texts)

        # Should only count database removals
        self.assertEqual(removed_count, len(db_texts))

        # Verify database items are gone
        for text in db_texts:
            self.assertIsNone(self.embeddings.db_store.get_embedding(text))

        self.embeddings.close()

    def test_clear_all_embeddings(self):
        """Test clearing all embeddings from database."""
        # Add some items to database
        db_texts = ["clear_db1", "clear_db2"]
        for text in db_texts:
            self.embeddings.generate_embedding(text, auto_save=True)

        # Verify items exist
        for text in db_texts:
            self.assertIsNotNone(self.embeddings.db_store.get_embedding(text))

        # Clear all
        cleared_count = self.embeddings.clear_all_embeddings()
        self.assertEqual(cleared_count, len(db_texts))

        # Verify database is empty
        all_texts = self.embeddings.db_store.get_all_texts()
        self.assertEqual(len(all_texts), 0)

        self.embeddings.close()

    def test_remove_embedding_text_normalization(self):
        """Test that removal works with text normalization (case, whitespace)."""
        original_text = "  Test Item  "
        normalized_text = "test item"

        # Add with original text
        self.embeddings.generate_embedding(original_text, auto_save=True)

        # Verify it's stored with normalized text
        self.assertIsNotNone(self.embeddings.db_store.get_embedding(normalized_text))

        # Remove using different case/whitespace
        removed = self.embeddings.remove_embedding("TEST ITEM")
        self.assertTrue(removed)

        # Verify it's gone
        self.assertIsNone(self.embeddings.db_store.get_embedding(normalized_text))

        self.embeddings.close()


if __name__ == "__main__":
    unittest.main()
