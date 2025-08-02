#!/usr/bin/env python3
"""
Test script to validate SEC Filings QA Agent components
This script tests individual components to ensure they work correctly
"""

import sys
import os
import tempfile
from datetime import datetime

# Add src to path
sys.path.append('src')

def test_html_parser():
    """Test the HTML parser component"""
    print("🧪 Testing HTML Parser...")
    
    try:
        from document_processing.html_parser import HTMLParser
        
        # Create sample SEC filing HTML
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head><title>Apple Inc. - Form 10-K</title></head>
        <body>
        <div class="document">
            <h1>UNITED STATES SECURITIES AND EXCHANGE COMMISSION</h1>
            <h2>FORM 10-K</h2>
            <h3>ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934</h3>
            
            <div class="section">
                <h4>ITEM 1. BUSINESS</h4>
                <p>Apple Inc. ("Apple" or the "Company") designs, manufactures and markets smartphones, 
                personal computers, tablets, wearables and accessories worldwide. The Company sells and 
                delivers digital content and applications through the iTunes Store, App Store, Mac App Store, 
                TV App Store, Book Store and Apple Music.</p>
                
                <p>The Company's fiscal year is the 52 or 53-week period that ends on the last Saturday of September. 
                The Company's fiscal 2023 spanned 52 weeks and ended on September 30, 2023.</p>
            </div>
            
            <div class="section">
                <h4>ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS</h4>
                <p>Net sales for 2023 were $383.3 billion, a decrease of 3% or $11.0 billion compared to 2022. 
                The decrease was driven by lower net sales of iPhone, Mac and iPad, partially offset by higher 
                net sales of Services.</p>
                
                <table>
                    <tr><th>Product</th><th>2023 Revenue</th><th>2022 Revenue</th></tr>
                    <tr><td>iPhone</td><td>$200.6B</td><td>$205.5B</td></tr>
                    <tr><td>Services</td><td>$85.2B</td><td>$78.1B</td></tr>
                </table>
            </div>
        </div>
        </body>
        </html>
        """
        
        parser = HTMLParser()
        result = parser.parse_content(sample_html, "test_file.html")
        
        # Validate results
        assert result['parsing_status'] == 'success'
        assert 'Apple Inc.' in result['full_text']
        assert result['word_count'] > 50
        assert len(result['sections']) > 0
        assert len(result['tables']) > 0
        
        print("  ✅ HTML Parser working correctly")
        print(f"  📊 Extracted {result['word_count']} words")
        print(f"  📑 Found {len(result['sections'])} sections")
        print(f"  📋 Found {len(result['tables'])} tables")
        return True
        
    except Exception as e:
        print(f"  ❌ HTML Parser failed: {e}")
        return False

def test_document_chunker():
    """Test the document chunker component"""
    print("\n🧪 Testing Document Chunker...")
    
    try:
        from document_processing.document_chunker import DocumentChunker
        
        # Create a temporary HTML file
        sample_content = """
        <html><body>
        <h1>Apple Inc. Form 10-K Annual Report</h1>
        <p>Apple Inc. designs, manufactures and markets smartphones, personal computers, tablets, 
        wearables and accessories worldwide. The Company sells and delivers digital content and 
        applications through various digital stores.</p>
        
        <p>For fiscal 2023, total net sales were $383.3 billion, representing a decrease of 3% 
        compared to fiscal 2022. This decrease was primarily driven by lower iPhone sales due to 
        challenging macroeconomic conditions and foreign exchange headwinds.</p>
        
        <p>The Company's gross margin for fiscal 2023 was 44.1% compared to 43.3% for fiscal 2022. 
        The increase in gross margin was primarily driven by favorable product mix and cost savings 
        initiatives, partially offset by foreign exchange headwinds.</p>
        
        <p>Research and development expenses were $29.9 billion for fiscal 2023, representing 7.8% 
        of total net sales. The Company continues to invest heavily in innovation across all product 
        categories and services.</p>
        </body></html>
        """
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(sample_content)
            temp_file = f.name
        
        try:
            chunker = DocumentChunker(chunk_size=50, overlap=10)  # Small chunks for testing
            chunks = chunker.chunk_file(temp_file)
            
            # Validate results
            assert len(chunks) > 0
            assert all(hasattr(chunk, 'content') for chunk in chunks)
            assert all(hasattr(chunk, 'metadata') for chunk in chunks)
            
            print("  ✅ Document Chunker working correctly")
            print(f"  📄 Created {len(chunks)} chunks")
            print(f"  📝 Sample chunk: {chunks[0].content[:100]}...")
            return True
            
        finally:
            os.unlink(temp_file)
        
    except Exception as e:
        print(f"  ❌ Document Chunker failed: {e}")
        return False

def test_vector_store():
    """Test the vector store component"""
    print("\n🧪 Testing Vector Store...")
    
    try:
        from vector_store.chroma_store import ChromaVectorStore
        from document_processing.document_chunker import DocumentChunk
        
        # Create sample chunks
        sample_chunks = [
            DocumentChunk(
                content="Apple Inc. reported total revenue of $383.3 billion for fiscal year 2023.",
                metadata={"ticker": "AAPL", "filing_type": "10-K", "section": "financial_highlights"}
            ),
            DocumentChunk(
                content="Microsoft Corporation's revenue grew 7% year-over-year to $211.9 billion.",
                metadata={"ticker": "MSFT", "filing_type": "10-K", "section": "financial_highlights"}
            ),
            DocumentChunk(
                content="Apple's iPhone revenue decreased 2.4% to $200.6 billion in fiscal 2023.",
                metadata={"ticker": "AAPL", "filing_type": "10-K", "section": "product_revenue"}
            )
        ]
        
        # Test vector store operations
        vector_store = ChromaVectorStore()
        
        # Add chunks
        vector_store.add_chunks(sample_chunks)
        
        # Test search
        results = vector_store.search("Apple revenue 2023", limit=2)
        
        # Validate results
        assert len(results) > 0
        assert any("Apple" in result.content for result in results)
        
        print("  ✅ Vector Store working correctly")
        print(f"  🔍 Search returned {len(results)} results")
        print(f"  📊 Top result: {results[0].content[:80]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Vector Store failed: {e}")
        return False

def test_query_processor():
    """Test the query processing component"""
    print("\n🧪 Testing Query Processor...")
    
    try:
        from query_processing.query_processor import QueryProcessor
        
        processor = QueryProcessor()
        
        # Test entity extraction
        test_queries = [
            "What was Apple's revenue in 2023?",
            "Compare MSFT and GOOGL profit margins",
            "Show me JPM's 10-K filing from Q4 2023"
        ]
        
        for query in test_queries:
            processed = processor.process_query(query)
            
            # Validate processing
            assert 'entities' in processed
            assert 'expanded_query' in processed
            
        print("  ✅ Query Processor working correctly")
        print(f"  🔍 Processed {len(test_queries)} test queries")
        return True
        
    except Exception as e:
        print(f"  ❌ Query Processor failed: {e}")
        return False

def test_answer_generator():
    """Test the answer generation component"""
    print("\n🧪 Testing Answer Generator...")
    
    try:
        from answer_generation.gemini_generator import GeminiAnswerGenerator
        from document_processing.document_chunker import DocumentChunk
        
        # Create sample context
        context_chunks = [
            DocumentChunk(
                content="Apple Inc. reported net sales of $383.3 billion for fiscal 2023, compared to $394.3 billion for fiscal 2022, representing a decrease of 3%.",
                metadata={"ticker": "AAPL", "filing_type": "10-K", "filing_date": "2023-11-02"}
            )
        ]
        
        generator = GeminiAnswerGenerator()
        
        # Test answer generation
        query = "What was Apple's revenue in 2023?"
        answer = generator.generate_answer(query, context_chunks)
        
        # Validate answer
        assert 'answer' in answer
        assert 'sources' in answer
        assert 'confidence' in answer
        
        print("  ✅ Answer Generator working correctly")
        print(f"  💬 Generated answer: {answer['answer'][:100]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Answer Generator failed: {e}")
        print(f"  ℹ️  Note: This may fail if Gemini API key is not configured")
        return False

def main():
    """Run all component tests"""
    print("🚀 SEC Filings QA Agent - Component Testing")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_html_parser,
        test_document_chunker,
        test_vector_store,
        test_query_processor,
        test_answer_generator
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} tests")
    print(f"📈 Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All components working correctly!")
        print("✅ System architecture validated")
    elif passed >= total * 0.8:
        print("\n✅ Most components working correctly")
        print("⚠️  Some components may need configuration")
    else:
        print("\n❌ Multiple component failures detected")
        print("🔧 System needs troubleshooting")
    
    print("\n📚 Next Steps:")
    print("  1. Configure API keys in .env file")
    print("  2. Download SEC filings using data collection")
    print("  3. Run full system integration test")
    print("  4. Try example queries from documentation")
    
    return passed >= total * 0.8

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
