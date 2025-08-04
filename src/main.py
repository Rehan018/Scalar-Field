#!/usr/bin/env python3

import os
import sys
from typing import Dict, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collection.data_downloader import DataDownloader
from document_processing.document_chunker import DocumentChunker
from vector_store.vector_db import VectorDB
from query_processing.query_router import QueryRouter
from answer_generation.answer_synthesizer import AnswerSynthesizer
from config.settings import RAW_DATA_DIR


class SECFilingsQA:
    def __init__(self):
        self.downloader = DataDownloader()
        self.chunker = DocumentChunker()
        self.vector_db = VectorDB()
        self.query_router = QueryRouter()
        self.answer_synthesizer = AnswerSynthesizer()
        self.chunks = []
        self.system_ready = False
        
    def setup_system(self):
        print("=== SEC Filings QA Agent Setup ===")
        
        print("\n1. Downloading SEC filings...")
        download_results = self.downloader.download_all_companies()
        
        print(f"[OK] Downloaded {download_results['summary']['total_files_downloaded']} files")
        print(f"[OK] Success rate: {download_results['summary']['success_rate']}")
        
        print("\n2. Processing documents...")
        self._process_documents()
        
        print(f"[OK] Created {len(self.chunks)} document chunks")
        
        print("\n3. Building vector database...")
        self.vector_db.add_chunks(self.chunks)
        
        self._display_statistics()
        
        self.system_ready = True
        print("\n[OK] System setup complete!")
        return True
    
    def _process_documents(self):
        html_files = []
        if os.path.exists(RAW_DATA_DIR):
            for filename in os.listdir(RAW_DATA_DIR):
                if filename.endswith('.html'):
                    html_files.append(os.path.join(RAW_DATA_DIR, filename))
        
        if not html_files:
            print("[WARNING] No HTML files found to process")
            return
        
        self.chunks = self.chunker.chunk_multiple_files(html_files)
    
    def _display_statistics(self):
        if not self.chunks:
            print("[WARNING] No chunks available for statistics")
            return
        
        stats = self.chunker.get_chunk_statistics(self.chunks)
        
        print("\n=== System Statistics ===")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Average words per chunk: {stats['average_words_per_chunk']:.1f}")
        print(f"Unique companies: {stats['unique_tickers']}")
        print(f"Unique filing types: {stats['unique_filing_types']}")
        
        print("\n--- Chunks by Company ---")
        for ticker, count in sorted(stats['chunks_by_ticker'].items()):
            print(f"{ticker}: {count} chunks")
        
        print("\n--- Chunks by Filing Type ---")
        for filing_type, count in sorted(stats['chunks_by_filing_type'].items()):
            print(f"{filing_type}: {count} chunks")
    
    def query(self, question: str) -> Dict:
        if not self.system_ready:
            return {
                "answer": "[ERROR] System not initialized. Please run setup_system() first.",
                "confidence": 0.0,
                "sources": [],
                "status": "system_not_ready"
            }
        
        try:
            print(f"\n🔍 Processing query: {question}")
            query_analysis = self.query_router.route_query(question)
            
            print(f"Query type: {query_analysis['query_type']}")
            print(f"Found {len(query_analysis['relevant_documents'])} relevant documents")
            
            result = self.answer_synthesizer.synthesize_answer(query_analysis)
            
            return result
            
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "confidence": 0.0,
                "sources": [],
                "status": "error",
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict:
        download_status = self.downloader.get_download_status()
        
        processing_status = {
            "chunks_loaded": len(self.chunks),
            "chunks_available": len(self.chunks) > 0
        }
        
        vector_db_stats = self.vector_db.get_collection_stats()
        
        return {
            "download_status": download_status,
            "processing_status": processing_status,
            "vector_db_status": vector_db_stats,
            "system_ready": self.system_ready and vector_db_stats["total_chunks"] > 0
        }


def main():
    print("SEC Filings QA Agent")
    print("===================")
    
    qa_system = SECFilingsQA()
    
    status = qa_system.get_system_status()
    
    if not status["system_ready"]:
        print("System not ready. Starting setup...")
        success = qa_system.setup_system()
        if not success:
            print("[ERROR] Setup failed. Exiting.")
            return
    else:
        print("[OK] System already initialized")
        qa_system._display_statistics()
    
    print("\n=== Interactive Mode ===")
    print("Enter your questions about SEC filings (type 'quit' to exit)")
    
    while True:
        try:
            question = input("\nQuestion: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                continue
            
            result = qa_system.query(question)
            
            print(f"\nAnswer: {result['answer']}")
            print(f"\nConfidence: {result['confidence']:.2f}")
            
            if result.get('sources'):
                print(f"\nSources ({len(result['sources'])}):")
                for source in result['sources'][:3]:
                    print(f"- {source['citation_text']}")
            
            if result['status'] != 'success':
                print(f"Status: {result['status']}")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()