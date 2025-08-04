import re
from typing import List, Dict, Optional, Set
from datetime import datetime

from config.settings import COMPANIES


class EntityExtractor:
    def __init__(self):
        self.ticker_to_name = {ticker: info["name"] for ticker, info in COMPANIES.items()}
        self.name_to_ticker = {info["name"].lower(): ticker for ticker, info in COMPANIES.items()}
        
        
        self.company_variations = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "wells fargo": "WFC",
            "johnson & johnson": "JNJ",
            "johnson and johnson": "JNJ",
            "pfizer": "PFE",
            "exxon": "XOM",
            "exxon mobil": "XOM",
            "chevron": "CVX",
            "walmart": "WMT",
            "general electric": "GE",
            "caterpillar": "CAT",
            "boeing": "BA"
        }
    
    def extract_tickers(self, query: str) -> List[str]:
        
        tickers = set()
        query_lower = query.lower()
        
        
        for ticker in COMPANIES.keys():
            pattern = r'\b' + re.escape(ticker.lower()) + r'\b'
            if re.search(pattern, query_lower):
                if len(ticker) <= 2:
                    if self._validate_short_ticker_context(query_lower, ticker.lower()):
                        tickers.add(ticker)
                else:
                    tickers.add(ticker)
        
        for name_variant, ticker in self.company_variations.items():
            pattern = r'\b' + re.escape(name_variant) + r'\b'
            if re.search(pattern, query_lower):
                tickers.add(ticker)
        
        
        for full_name, ticker in self.name_to_ticker.items():
            if full_name in query_lower:
                tickers.add(ticker)
        
        return list(tickers)
    
    def _validate_short_ticker_context(self, query_lower: str, ticker: str) -> bool:
        
        false_positive_contexts = {
            'ge': ['general', 'generate', 'generation', 'genetic', 'geography', 'geometry'],
            'ba': ['bachelor', 'basic', 'basketball', 'battle'],
            'cat': ['category', 'catalog', 'catch', 'cattle'],
            'cvx': [],
            'ge': ['general', 'generate', 'generation', 'genetic', 'geography', 'geometry']
        }
        
        if ticker not in false_positive_contexts:
            return True
        
        for false_context in false_positive_contexts[ticker]:
            if false_context in query_lower:
                ticker_pattern = r'\b' + re.escape(ticker) + r'\b'
                false_pattern = r'\b' + re.escape(false_context) + r'\b'
                
                ticker_matches = list(re.finditer(ticker_pattern, query_lower))
                false_matches = list(re.finditer(false_pattern, query_lower))
                
                for ticker_match in ticker_matches:
                    for false_match in false_matches:
                        if (abs(ticker_match.start() - false_match.start()) < len(false_context) or
                            ticker_match.start() >= false_match.start() and 
                            ticker_match.end() <= false_match.end()):
                            return False
        
        return True
    
    def extract_time_periods(self, query: str) -> Dict:
        
        time_info = {
            "years": [],
            "quarters": [],
            "specific_dates": [],
            "relative_terms": []
        }
        
        year_pattern = r'\b(20[2-4][0-9])\b'
        years = re.findall(year_pattern, query)
        time_info["years"] = list(set(years))
        
        quarter_patterns = [
            r'\bQ[1-4]\b',
            r'\b[1-4]Q\b',
            r'\bfirst quarter\b',
            r'\bsecond quarter\b',
            r'\bthird quarter\b',
            r'\bfourth quarter\b'
        ]
        
        for pattern in quarter_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            time_info["quarters"].extend(matches)
        
        relative_terms = [
            "recent", "latest", "current", "last year", "this year",
            "over time", "historical", "trend", "evolution"
        ]
        
        for term in relative_terms:
            if term in query.lower():
                time_info["relative_terms"].append(term)
        
        return time_info
    
    def extract_filing_types(self, query: str) -> List[str]:
        
        filing_types = []
        query_lower = query.lower()
        
        filing_patterns = {
            r'\b10-k\b': '10-K',
            r'\bannual report\b': '10-K',
            r'\b10-q\b': '10-Q',
            r'\bquarterly report\b': '10-Q',
            r'\b8-k\b': '8-K',
            r'\bcurrent report\b': '8-K',
            r'\bproxy\b': 'DEF 14A',
            r'\bdef 14a\b': 'DEF 14A',
            r'\binsider trading\b': ['3', '4', '5'],
            r'\bform [345]\b': ['3', '4', '5']
        }
        
        for pattern, filing_type in filing_patterns.items():
            if re.search(pattern, query_lower):
                if isinstance(filing_type, list):
                    filing_types.extend(filing_type)
                else:
                    filing_types.append(filing_type)
        
        return list(set(filing_types))
    
    def extract_financial_concepts(self, query: str) -> List[str]:
        
        concepts = []
        query_lower = query.lower()
        
        financial_terms = {
            "revenue": ["revenue", "sales", "income", "earnings"],
            "expenses": ["expenses", "costs", "spending"],
            "profit": ["profit", "net income", "earnings"],
            "cash_flow": ["cash flow", "operating cash", "free cash flow"],
            "debt": ["debt", "liabilities", "borrowing"],
            "assets": ["assets", "balance sheet"],
            "risk_factors": ["risk", "risks", "risk factors"],
            "competition": ["competition", "competitive", "competitors"],
            "r&d": ["r&d", "research", "development", "innovation"],
            "acquisitions": ["acquisition", "merger", "m&a"],
            "executive_compensation": ["compensation", "executive pay", "salary"],
            "working_capital": ["working capital", "current assets"],
            "climate": ["climate", "environmental", "sustainability"],
            "ai_automation": ["ai", "artificial intelligence", "automation", "technology"]
        }
        
        for concept, keywords in financial_terms.items():
            if any(keyword in query_lower for keyword in keywords):
                concepts.append(concept)
        
        return concepts
    
    def extract_comparison_intent(self, query: str) -> Dict:
        
        comparison_info = {
            "is_comparison": False,
            "comparison_type": None,
            "entities": []
        }
        
        comparison_keywords = [
            "compare", "comparison", "versus", "vs", "against",
            "difference", "similar", "contrast", "between"
        ]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in comparison_keywords):
            comparison_info["is_comparison"] = True
            
            if "trend" in query_lower or "over time" in query_lower:
                comparison_info["comparison_type"] = "temporal"
            elif len(self.extract_tickers(query)) > 1:
                comparison_info["comparison_type"] = "cross_company"
            else:
                comparison_info["comparison_type"] = "general"
            
            comparison_info["entities"] = self.extract_tickers(query)
        
        return comparison_info
    
    def extract_all_entities(self, query: str) -> Dict:
        
        return {
            "tickers": self.extract_tickers(query),
            "time_periods": self.extract_time_periods(query),
            "filing_types": self.extract_filing_types(query),
            "financial_concepts": self.extract_financial_concepts(query),
            "comparison_intent": self.extract_comparison_intent(query),
            "original_query": query
        }