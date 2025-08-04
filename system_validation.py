#!/usr/bin/env python3
"""
SEC Filings QA Agent - System Validation Script

Project Repository: https://github.com/Rehan018/Scalar-Field.git

This script validates all system components and environment configuration
to ensure the system is ready for production use.
"""

import os
import sys
import requests
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(item: str, status: bool, details: str = ""):
    """Print status with colored indicators."""
    indicator = "✅" if status else "❌"
    print(f"{indicator} {item}")
    if details:
        print(f"   {details}")

def validate_environment_variables() -> Dict:
    """Validate all environment variables are properly loaded."""
    print_header("ENVIRONMENT VARIABLES VALIDATION")
    
    results = {}
    
    try:
        from config.settings import (
            SEC_API_KEY, OLLAMA_URL, OLLAMA_MODEL, CHUNK_SIZE, 
            CHUNK_OVERLAP, MAX_TOKENS, TEMPERATURE, DEBUG_MODE,
            CHROMA_PERSIST_DIRECTORY, EMBEDDINGS_DIR, RAW_DATA_DIR
        )
        
        # Check required variables
        checks = [
            ("SEC_API_KEY", SEC_API_KEY is not None and len(SEC_API_KEY) > 10),
            ("OLLAMA_URL", OLLAMA_URL is not None and OLLAMA_URL.startswith('http')),
            ("OLLAMA_MODEL", OLLAMA_MODEL is not None and len(OLLAMA_MODEL) > 0),
            ("CHUNK_SIZE", isinstance(CHUNK_SIZE, int) and CHUNK_SIZE > 0),
            ("CHUNK_OVERLAP", isinstance(CHUNK_OVERLAP, int) and CHUNK_OVERLAP >= 0),
            ("MAX_TOKENS", isinstance(MAX_TOKENS, int) and MAX_TOKENS > 0),
            ("TEMPERATURE", isinstance(TEMPERATURE, float) and 0 <= TEMPERATURE <= 1),
            ("DEBUG_MODE", isinstance(DEBUG_MODE, bool)),
        ]
        
        for var_name, is_valid in checks:
            print_status(f"{var_name}", is_valid)
            results[var_name] = is_valid
        
        # Print current values
        print(f"\n📋 Current Configuration:")
        print(f"   Ollama URL: {OLLAMA_URL}")
        print(f"   Model: {OLLAMA_MODEL}")
        print(f"   Chunk Size: {CHUNK_SIZE}")
        print(f"   Temperature: {TEMPERATURE}")
        print(f"   Debug Mode: {DEBUG_MODE}")
        
        results['environment_config'] = True
        
    except Exception as e:
        print_status("Environment Configuration", False, f"Error: {e}")
        results['environment_config'] = False
    
    return results

def validate_ollama_connection() -> bool:
    """Validate connection to Ollama server."""
    print_header("OLLAMA SERVER VALIDATION")
    
    try:
        from config.settings import OLLAMA_URL, OLLAMA_MODEL
        
        # Test connection to Ollama
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print_status("Ollama Server Connection", True, f"Connected to {OLLAMA_URL}")
            
            # Check if model is available
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            
            model_available = any(OLLAMA_MODEL in model for model in models)
            print_status(f"Model '{OLLAMA_MODEL}' Available", model_available)
            
            if models:
                print(f"\n📋 Available Models:")
                for model in models[:5]:  # Show first 5 models
                    print(f"   - {model}")
            
            return model_available
        else:
            print_status("Ollama Server Connection", False, f"HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_status("Ollama Server Connection", False, "Connection refused - is Ollama running?")
        return False
    except Exception as e:
        print_status("Ollama Server Connection", False, f"Error: {e}")
        return False

def validate_directories() -> bool:
    """Validate all required directories exist or can be created."""
    print_header("DIRECTORY STRUCTURE VALIDATION")
    
    try:
        from config.settings import (
            DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
            EMBEDDINGS_DIR, CHROMA_PERSIST_DIRECTORY
        )
        
        directories = [
            ("Data Directory", DATA_DIR),
            ("Raw Data Directory", RAW_DATA_DIR),
            ("Processed Data Directory", PROCESSED_DATA_DIR),
            ("Embeddings Directory", EMBEDDINGS_DIR),
            ("ChromaDB Directory", CHROMA_PERSIST_DIRECTORY),
        ]
        
        all_good = True
        
        for name, path in directories:
            try:
                os.makedirs(path, exist_ok=True)
                exists = os.path.exists(path)
                writable = os.access(path, os.W_OK)
                
                status = exists and writable
                details = f"Path: {path}"
                if not writable:
                    details += " (Not writable)"
                
                print_status(name, status, details)
                all_good = all_good and status
                
            except Exception as e:
                print_status(name, False, f"Error creating {path}: {e}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print_status("Directory Validation", False, f"Error: {e}")
        return False

def validate_dependencies() -> bool:
    """Validate all required Python packages are installed."""
    print_header("DEPENDENCIES VALIDATION")
    
    required_packages = [
        ("requests", "HTTP requests"),
        ("numpy", "Numerical computing"),
        ("pandas", "Data manipulation"),
        ("beautifulsoup4", "HTML parsing"),
        ("scikit-learn", "Machine learning"),
        ("python-dotenv", "Environment variables"),
        ("pickle", "Data serialization (built-in)"),
    ]
    
    optional_packages = [
        ("sentence-transformers", "Sentence embeddings"),
        ("chromadb", "Vector database"),
        ("transformers", "Transformer models"),
    ]
    
    all_required = True
    
    print("📦 Required Packages:")
    for package, description in required_packages:
        try:
            if package == "pickle":
                import pickle
            elif package == "beautifulsoup4":
                import bs4
            elif package == "python-dotenv":
                import dotenv
            elif package == "scikit-learn":
                import sklearn
            else:
                __import__(package.replace('-', '_'))
            print_status(f"{package}", True, description)
        except ImportError:
            print_status(f"{package}", False, f"Missing: {description}")
            all_required = False
    
    print("\n📦 Optional Packages:")
    for package, description in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(f"{package}", True, description)
        except ImportError:
            print_status(f"{package}", False, f"Optional: {description}")
    
    return all_required

def validate_system_components() -> Dict:
    """Validate core system components can be imported and initialized."""
    print_header("SYSTEM COMPONENTS VALIDATION")
    
    results = {}
    
    components = [
        ("Configuration Settings", "config.settings"),
        ("Data Downloader", "data_collection.data_downloader"),
        ("Document Chunker", "document_processing.document_chunker"),
        ("Vector Database", "vector_store.vector_db"),
        ("LLM Client", "answer_generation.llm_client"),
        ("Query Router", "query_processing.query_router"),
        ("Answer Synthesizer", "answer_generation.answer_synthesizer"),
    ]
    
    for name, module_path in components:
        try:
            module = __import__(module_path, fromlist=[''])
            print_status(name, True, f"Module: {module_path}")
            results[name] = True
        except Exception as e:
            print_status(name, False, f"Import error: {e}")
            results[name] = False
    
    return results

def test_basic_functionality() -> bool:
    """Test basic system functionality."""
    print_header("BASIC FUNCTIONALITY TEST")
    
    try:
        # Test LLM Client
        print("🧪 Testing LLM Client...")
        from answer_generation.llm_client import LLMClient
        
        llm_client = LLMClient()
        print_status("LLM Client Initialization", True)
        
        # Test Vector Database
        print("\n🧪 Testing Vector Database...")
        from vector_store.vector_db import VectorDB
        
        vector_db = VectorDB()
        stats = vector_db.get_collection_stats()
        print_status("Vector Database Initialization", True)
        print(f"   Total chunks in database: {stats.get('total_chunks', 0)}")
        
        # Test Document Chunker
        print("\n🧪 Testing Document Chunker...")
        from document_processing.document_chunker import DocumentChunker
        
        chunker = DocumentChunker()
        print_status("Document Chunker Initialization", True)
        
        return True
        
    except Exception as e:
        print_status("Basic Functionality Test", False, f"Error: {e}")
        return False

def generate_system_report(results: Dict) -> None:
    """Generate a comprehensive system report."""
    print_header("SYSTEM VALIDATION REPORT")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"📊 Overall Status: {passed_checks}/{total_checks} checks passed")
    print(f"📈 Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 SYSTEM STATUS: FULLY OPERATIONAL")
        print("✅ All components validated successfully")
        print("✅ Ready for production use")
    elif passed_checks >= total_checks * 0.8:
        print("\n⚠️  SYSTEM STATUS: MOSTLY OPERATIONAL")
        print("✅ Core components working")
        print("⚠️  Some optional features may be limited")
    else:
        print("\n❌ SYSTEM STATUS: NEEDS ATTENTION")
        print("❌ Critical components need fixing")
        print("🔧 Please address the failed checks above")
    
    print(f"\n📅 Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Repository: https://github.com/Rehan018/Scalar-Field.git")

def main():
    """Run complete system validation."""
    print("🚀 SEC Filings QA Agent - System Validation")
    print("=" * 60)
    
    results = {}
    
    # Run all validation checks
    env_results = validate_environment_variables()
    results.update(env_results)
    
    results['ollama_connection'] = validate_ollama_connection()
    results['directories'] = validate_directories()
    results['dependencies'] = validate_dependencies()
    
    component_results = validate_system_components()
    results.update(component_results)
    
    results['basic_functionality'] = test_basic_functionality()
    
    # Generate final report
    generate_system_report(results)
    
    # Return exit code based on critical components
    critical_components = [
        'environment_config', 'dependencies', 'directories'
    ]
    
    critical_passed = all(results.get(comp, False) for comp in critical_components)
    
    if critical_passed:
        print("\n✅ System validation completed successfully!")
        return 0
    else:
        print("\n❌ System validation found critical issues!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)