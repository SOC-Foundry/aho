import unittest
from unittest.mock import patch, MagicMock
from aho.rag.archive import query_archive

class TestRAGForbiddenFilter(unittest.TestCase):
    @patch('aho.rag.archive._get_client')
    @patch('aho.rag.archive._get_embedder')
    def test_query_filters_forbidden(self, mock_embedder, mock_client):
        # Mock collection
        mock_col = MagicMock()
        mock_client.return_value.get_collection.return_value = mock_col
        
        # Mock results: one clean, one forbidden
        mock_col.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["This is a clean document.", "This doc has ahomw-Pillar-1 in it."]],
            "metadatas": [[{"iteration": "0.1.7"}, {"iteration": "0.1.5"}]],
            "distances": [[0.1, 0.2]]
        }
        
        # Query with default forbidden list
        results = query_archive("ahomw", "pillar", prefer_recent=False)
        
        # Should only return one result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "id1")
        self.assertNotIn("ahomw-Pillar-", results[0]["document"])

    @patch('aho.rag.archive._get_client')
    @patch('aho.rag.archive._get_embedder')
    def test_query_custom_forbidden(self, mock_embedder, mock_client):
        mock_col = MagicMock()
        mock_client.return_value.get_collection.return_value = mock_col
        mock_col.query.return_value = {
            "ids": [["id1", "id2"]],
            "documents": [["Clean", "Forbidden phrase"]],
            "metadatas": [[{}, {}]],
            "distances": [[0.1, 0.2]]
        }
        
        results = query_archive("ahomw", "test", forbidden_substrings=["Forbidden phrase"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["document"], "Clean")

if __name__ == "__main__":
    unittest.main()
