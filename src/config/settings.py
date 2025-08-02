import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
SEC_API_KEY = os.getenv("SEC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SEC API Configuration
SEC_API_BASE_URL = "https://api.sec-api.io"
SEC_API_SEARCH_URL = "https://api.sec-api.io"
SEC_EDGAR_BASE_URL = "https://www.sec.gov/edgar"
SEC_EDGAR_DATA_URL = "https://www.sec.gov/Archives/edgar/data"
SEC_FORMS_URL = "https://www.sec.gov/forms"

# Companies to analyze (15 companies across sectors)
COMPANIES = {
    # Technology
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology"},

    # Finance
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Finance"},
    "BAC": {"name": "Bank of America Corporation", "sector": "Finance"},
    "WFC": {"name": "Wells Fargo & Company", "sector": "Finance"},

    # Healthcare
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare"},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare"},

    # Energy
    "XOM": {"name": "Exxon Mobil Corporation", "sector": "Energy"},
    "CVX": {"name": "Chevron Corporation", "sector": "Energy"},

    # Retail/Consumer
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Retail"},
    "WMT": {"name": "Walmart Inc.", "sector": "Retail"},

    # Manufacturing
    "GE": {"name": "General Electric Company", "sector": "Manufacturing"},
    "CAT": {"name": "Caterpillar Inc.", "sector": "Manufacturing"},
    "BA": {"name": "The Boeing Company", "sector": "Manufacturing"}
}

# Filing types to collect
FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A", "3", "4", "5"]

# Document processing configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 5))

# Vector database configuration
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-pro")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))

# Data paths
DATA_DIR = "./data"
RAW_DATA_DIR = "./data/raw"
PROCESSED_DATA_DIR = "./data/processed"
EMBEDDINGS_DIR = "./data/embeddings"