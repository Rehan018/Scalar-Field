import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import SECFilingsQA


class TestIntegration(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        cls.qa_system = SECFilingsQA()
    
    def test_system_initialization(self):
        """Test that system initializes properly."""
        self.assertIsNotNone(self.qa_system.downloader)
        self.assertIsNotNone(self.qa_system.chunker)
        self.assertIsNotNone(self.qa_system.vector_db)
        self.assertIsNotNone(self.qa_system.query_router)
        self.assertIsNotNone(self.qa_system.answer_synthesizer)
    
    def test_system_status(self):
        """Test system status reporting."""
        status = self.qa_system.get_system_status()
        
        self.assertIn('download_status', status)
        self.assertIn('processing_status', status)
        self.assertIn('vector_db_status', status)
        self.assertIn('system_ready', status)
    
    def test_query_without_setup(self):
        """Test query handling when system is not set up."""
        result = self.qa_system.query("Test question")
        
        self.assertIn('answer', result)
        self.assertIn('confidence', result)
        self.assertIn('sources', result)
        self.assertIn('status', result)
        
        # Should indicate system not ready
        self.assertEqual(result['status'], 'system_not_ready')
        self.assertEqual(result['confidence'], 0.0)
    
    def test_sample_evaluation_questions(self):
        """Test a few sample evaluation questions."""
        
        sample_questions = [
            "What are Apple's main risk factors?",
            "Compare revenue trends for technology companies",
            "How do companies describe AI and automation?"
        ]
        
        for question in sample_questions:
            with self.subTest(question=question):
                result = self.qa_system.query(question)
                
                # Should return proper structure even if not set up
                self.assertIsInstance(result, dict)
                self.assertIn('answer', result)
                self.assertIn('confidence', result)
                self.assertIn('sources', result)
                self.assertIn('status', result)


if __name__ == '__main__':
    unittest.main()