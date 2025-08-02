import requests
import time
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import os

try:
    from config.settings import SEC_API_KEY, SEC_API_SEARCH_URL, SEC_EDGAR_BASE_URL, SEC_FORMS_URL, RAW_DATA_DIR
except ImportError:
    from src.config.settings import SEC_API_KEY, SEC_API_SEARCH_URL, SEC_EDGAR_BASE_URL, SEC_FORMS_URL, RAW_DATA_DIR


class SECAPIClient:
    def __init__(self):
        self.api_key = SEC_API_KEY
        self.search_url = SEC_API_SEARCH_URL
        self.edgar_url = SEC_EDGAR_BASE_URL
        self.forms_url = SEC_FORMS_URL
        self.session = requests.Session()
        self.rate_limit_delay = 0.1  # 10 requests per second
        
        if not self.api_key:
            print("Warning: SEC_API_KEY not found. Using fallback methods.")
        
    def search_filings(self, ticker: str, filing_type: str,
                      start_date: str = "2022-01-01",
                      end_date: str = "2024-01-01") -> List[Dict]:
        """Search for SEC filings for a specific ticker and filing type."""

        # Correct sec-api.io query format
        query = {
            "query": f"ticker:{ticker} AND formType:\"{filing_type}\" AND filedAt:[{start_date} TO {end_date}]",
            "from": "0",
            "size": "10",
            "sort": [{"filedAt": {"order": "desc"}}]
        }

        # Correct authentication method for sec-api.io
        headers = {
            "Authorization": self.api_key,  # sec-api.io uses direct API key, not Bearer
            "Content-Type": "application/json"
        }

        try:
            print(f"Searching with query: {query['query']}")
            response = self.session.post(
                self.search_url,
                headers=headers,
                json=query
            )

            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response text: {response.text}")

            response.raise_for_status()

            data = response.json()
            filings = data.get("filings", [])
            print(f"Found {len(filings)} filings for {ticker} {filing_type}")
            return filings

        except requests.exceptions.RequestException as e:
            print(f"Error searching filings for {ticker} {filing_type}: {e}")
            return []

        finally:
            time.sleep(self.rate_limit_delay)
    
    def download_filing(self, filing_url: str, ticker: str,
                       filing_type: str, filing_date: str) -> Optional[str]:
        """Download a specific SEC filing."""

        try:
            # Add headers for SEC EDGAR access
            headers = {
                'User-Agent': 'SEC Filing QA Agent research@example.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'www.sec.gov'
            }

            # First, get the filing detail page
            response = self.session.get(filing_url, headers=headers)
            response.raise_for_status()

            # Parse the detail page to find the actual filing document link
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for the actual filing document link
            # SEC filing detail pages have links to the actual documents
            document_link = None

            # Try to find the primary document link
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                # Look for links that end with .htm or .html and contain the filing
                if ('.htm' in href and
                    not href.endswith('-index.htm') and
                    not 'FilingSummary' in href and
                    '/Archives/edgar/data/' in href):
                    document_link = href
                    break

            if not document_link:
                # Fallback: use the original URL if we can't find a better one
                print(f"Warning: Could not find document link for {filing_url}, using original")
                document_content = response.text
            else:
                # Download the actual document
                if document_link.startswith('/'):
                    document_url = f"https://www.sec.gov{document_link}"
                else:
                    document_url = document_link

                doc_response = self.session.get(document_url, headers=headers)
                doc_response.raise_for_status()
                document_content = doc_response.text

            # Create filename
            safe_date = filing_date.replace("-", "").replace("T", "_").split("_")[0]
            filename = f"{ticker}_{filing_type}_{safe_date}.html"
            filepath = os.path.join(RAW_DATA_DIR, filename)

            # Ensure directory exists
            os.makedirs(RAW_DATA_DIR, exist_ok=True)

            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(document_content)

            print(f"Downloaded: {filename}")
            return filepath

        except requests.exceptions.RequestException as e:
            print(f"Error downloading filing {filing_url}: {e}")
            return None

        finally:
            time.sleep(self.rate_limit_delay)
    
    def get_company_filings(self, ticker: str, filing_types: List[str], 
                           max_filings_per_type: int = 5) -> List[Dict]:
        """Get recent filings for a company across multiple filing types."""
        
        all_filings = []
        
        for filing_type in filing_types:
            print(f"Searching {filing_type} filings for {ticker}...")
            
            filings = self.search_filings(ticker, filing_type)
            
            # Limit number of filings per type
            limited_filings = filings[:max_filings_per_type]
            
            for filing in limited_filings:
                # Use correct field names from sec-api.io response
                filing_info = {
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "filing_date": filing.get("filedAt", ""),
                    "filing_url": filing.get("linkToHtml", filing.get("linkToFilingDetails", "")),
                    "company_name": filing.get("companyName", ""),
                    "form_type": filing.get("formType", ""),
                    "accession_number": filing.get("accessionNo", ""),
                    "cik": filing.get("cik", "")
                }
                all_filings.append(filing_info)
        
        return all_filings
    
    def download_company_filings(self, ticker: str, filing_types: List[str]) -> List[str]:
        """Download all filings for a specific company."""
        
        filings = self.get_company_filings(ticker, filing_types)
        downloaded_files = []
        
        for filing in filings:
            if filing["filing_url"]:
                filepath = self.download_filing(
                    filing["filing_url"],
                    filing["ticker"],
                    filing["filing_type"],
                    filing["filing_date"]
                )
                if filepath:
                    downloaded_files.append(filepath)
        
        return downloaded_files