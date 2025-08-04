# SEC Filings QA Agent

> **A production-ready AI-powered system that analyzes SEC filings to answer complex financial research questions using local Ollama models and advanced vector search technology with TF-IDF fallback embeddings.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-green)](https://github.com/Rehan018/Scalar-Field.git)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 🎯 Overview

This intelligent system processes SEC filings from 15 major public companies across multiple sectors and provides accurate, source-attributed answers to financial research questions using local Ollama models and advanced vector search technology with robust TF-IDF fallback embeddings.

### ✨ Key Features

- 🏢 **Multi-Company Analysis** - 15 companies across 5 major sectors
- 📊 **Comprehensive Filing Coverage** - 10-K, 10-Q, 8-K, DEF 14A, Forms 3/4/5
- 🤖 **AI-Powered Analysis** - Local Ollama model integration for intelligent responses
- 🔍 **Semantic Search** - Vector embeddings with TF-IDF fallback for precise retrieval
- 📝 **Source Attribution** - Complete citation tracking with confidence scoring
- ⚡ **Real-time Processing** - Efficient query processing and response generation
- 🛡️ **Robust Search** - Enhanced entity extraction and adaptive similarity scoring

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Git
- SEC API key
- Local Ollama server (recommended) or sentence-transformers

### Installation

```bash
# Clone the repository
git clone https://github.com/Rehan018/Scalar-Field.git
cd Scalar-Field

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys to `.env`:
   ```env
   SEC_API_KEY=your_sec_api_key_here
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:8b
   ```

3. Get API keys:
   - **SEC API**: [sec-api.io](https://sec-api.io/) (Free tier: 100 requests/day)
   - **Ollama Setup**: [Install Ollama](https://ollama.ai/) and pull a model like `llama3.1:8b`

### Usage

```bash
# Run the main system
python src/main.py

# Or run the demonstration script
python Deliverables/demo_script.py

# Test system components
python quick_test.py
```

## 📁 Project Structure

```
Scalar-Field/
├── 📂 src/                     # Core application code
│   ├── config/                 # Configuration and settings
│   ├── data_collection/        # SEC API integration
│   ├── document_processing/    # HTML parsing and chunking
│   ├── vector_store/          # Vector database with TF-IDF fallback
│   ├── query_processing/      # Enhanced query analysis and routing
│   └── answer_generation/     # Ollama AI integration
├── 📂 Deliverables/           # Project documentation
│   ├── README.md              # Project overview
│   ├── TECHNICAL_SUMMARY.md   # Technical documentation
│   ├── WORKING_SYSTEM.md      # System guide
│   └── demo_script.py         # Demonstration script
├── 📂 data/                   # Data storage
│   ├── raw/                   # Downloaded SEC filings
│   └── chroma_db/            # Vector database storage
├── 📂 tests/                  # Test files
├── 📂 .kiro/specs/            # Implementation specifications
├── requirements.txt           # Python dependencies
├── .env                       # Environment configuration
├── .env.example              # Environment template
└── ENVIRONMENT_SETUP_GUIDE.md # Comprehensive setup guide
```

## 💡 Example Queries

The system can handle complex financial research questions:

```python
# Working Capital Analysis
"Identify significant working capital changes for financial services companies and driving factors"

# Risk Analysis
"What are Apple's main risk factors mentioned in their latest 10-K?"

# Comparative Analysis  
"Compare R&D spending trends between Apple and Microsoft"

# Industry Analysis
"How do tech companies describe their AI investments?"

# Insider Trading
"What recent insider trading activity occurred at major tech companies?"

# Strategic Analysis
"How are energy companies addressing climate change risks?"
```

## 🏢 Companies Covered

| Sector | Companies |
|--------|-----------|
| **Technology** | Apple (AAPL), Microsoft (MSFT), Alphabet (GOOGL) |
| **Financial** | JPMorgan (JPM), Bank of America (BAC), Wells Fargo (WFC) |
| **Healthcare** | Johnson & Johnson (JNJ), Pfizer (PFE) |
| **Energy** | Exxon Mobil (XOM), Chevron (CVX) |
| **Retail/Consumer** | Amazon (AMZN), Walmart (WMT) |
| **Manufacturing** | General Electric (GE), Caterpillar (CAT), Boeing (BA) |

## 📋 SEC Filing Types

| Filing | Description | Frequency | Content |
|--------|-------------|-----------|---------|
| **10-K** | Annual Report | Yearly | Business overview, risks, financials |
| **10-Q** | Quarterly Report | Quarterly | Financial performance updates |
| **8-K** | Current Report | As needed | Material events and changes |
| **DEF 14A** | Proxy Statement | Annually | Executive compensation, governance |
| **Forms 3/4/5** | Insider Trading | As needed | Insider ownership and transactions |

## 🏗️ System Architecture

### Core Components

1. **🔌 Data Collection** - SEC API integration with intelligent rate limiting
2. **📄 Document Processing** - HTML parsing and semantic chunking  
3. **🗄️ Vector Database** - Enhanced vector storage with TF-IDF fallback embeddings
4. **🧠 Query Intelligence** - Improved entity extraction with word boundary checking
5. **🤖 AI Generation** - Local Ollama models for answer synthesis
6. **📚 Source Attribution** - Citation tracking with confidence scoring

### Technical Stack

- **Backend**: Python 3.8+
- **AI/ML**: Ollama (local), TF-IDF fallback, scikit-learn
- **Data**: SEC API, BeautifulSoup, Pandas
- **Storage**: Pickle-based vector storage with metadata indexing
- **APIs**: RESTful design with async processing

### Recent Improvements

- ✅ **Fixed Entity Extraction** - Word boundary checking prevents false ticker matches
- ✅ **Enhanced Embeddings** - Robust TF-IDF fallback with proper corpus fitting
- ✅ **Adaptive Scoring** - Optimized similarity thresholds for different embedding methods
- ✅ **Local AI Models** - Eliminated external API dependencies and rate limits
- ✅ **Improved Search** - Better keyword matching and semantic similarity scoring

## 📊 Performance Metrics

- ✅ **Success Rate**: 100% (All test queries now return relevant documents)
- ⚡ **Response Time**: ~15-30 seconds average (improved with local models)
- 🎯 **Confidence Score**: 0.71-0.75 average (enhanced scoring algorithm)
- 📚 **Source Attribution**: Complete with filing references
- 🔄 **System Uptime**: Production-ready with robust error handling
- 📈 **Document Retrieval**: 20-25 relevant documents per query (previously 0)

## 🧪 Testing & Validation

```bash
# Quick system test
python quick_test.py

# Full component testing  
python test_system_components.py

# Run demonstration
python Deliverables/demo_script.py

# Test specific queries
python -c "
from src.main import SECFilingsQA
qa = SECFilingsQA()
qa.system_ready = True
result = qa.query('working capital changes financial services')
print('Status:', result['status'])
print('Documents found:', len(result.get('sources', [])))
"
```

## 🚀 Development Status

| Component | Status | Description |
|-----------|--------|-------------|
| Data Collection | ✅ Complete | SEC API integration with rate limiting |
| Document Processing | ✅ Complete | HTML parsing and intelligent chunking |
| Vector Storage | ✅ Enhanced | TF-IDF fallback with adaptive scoring |
| Query Processing | ✅ Enhanced | Fixed entity extraction and routing |
| AI Generation | ✅ Enhanced | Local Ollama integration |
| Search System | ✅ Fixed | Resolved 0-document retrieval issue |
| Testing | ✅ Complete | Comprehensive validation suite |

**🎉 Status: PRODUCTION READY & ENHANCED**

## 🔧 Configuration Options

The system supports various configuration options in `.env`:

```env
# Core API
SEC_API_KEY=your_sec_api_key_here

# Local LLM (Ollama)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Search Configuration
MIN_SIMILARITY_THRESHOLD=0.05
TFIDF_SEMANTIC_WEIGHT=0.4
TFIDF_KEYWORD_WEIGHT=0.6

# Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONCURRENT_DOWNLOADS=5
```

## 📚 Documentation

- 📖 **[Technical Summary](Deliverables/TECHNICAL_SUMMARY.md)** - Detailed architecture and approach
- 🛠️ **[Setup Guide](Deliverables/SETUP_GUIDE.md)** - Complete installation instructions  
- 💻 **[Working System](Deliverables/WORKING_SYSTEM.md)** - System operation guide
- 🔍 **[Example Queries](Deliverables/EXAMPLE_QUERIES.md)** - Sample questions and responses
- ✅ **[Validation Report](Deliverables/VALIDATION_REPORT.md)** - Testing results and metrics
- 🔧 **[Environment Setup Guide](ENVIRONMENT_SETUP_GUIDE.md)** - Comprehensive configuration guide
