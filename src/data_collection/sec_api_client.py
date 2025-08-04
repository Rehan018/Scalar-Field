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
        self.request_count = 0
        self.max_requests_per_day = 95  # Stay under 100 limit
        
        # Enhanced headers for SEC EDGAR access
        self.session.headers.update({
            'User-Agent': 'SEC Filing QA Agent research@example.com',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        
        if not self.api_key:
            print("Warning: SEC_API_KEY not found. Using fallback methods.")
            
        # Load request count from cache if available
        self._load_request_count()
        
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
        """Download a specific SEC filing with enhanced document detection."""

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

            # Enhanced document link detection
            document_link = self._find_actual_filing_document(soup, filing_type)
            
            if document_link:
                # Download the actual document
                document_url = self._construct_document_url(document_link)
                print(f"Downloading actual filing from: {document_url}")
                
                doc_response = self.session.get(document_url, headers=headers)
                doc_response.raise_for_status()
                document_content = doc_response.text
                
                # Validate that we got actual filing content
                if self._validate_filing_content(document_content, filing_type):
                    print(f"✅ Successfully downloaded actual {filing_type} filing")
                else:
                    print(f"⚠️  Downloaded content may not be actual filing - using anyway")
                    
            else:
                print(f"❌ Could not find actual filing document for {filing_url}")
                # Try alternative approach - look for text version
                text_link = self._find_text_version(soup)
                if text_link:
                    document_url = self._construct_document_url(text_link)
                    doc_response = self.session.get(document_url, headers=headers)
                    doc_response.raise_for_status()
                    document_content = doc_response.text
                else:
                    # Last resort - use the detail page content
                    document_content = response.text

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
    
    def _find_actual_filing_document(self, soup, filing_type: str) -> Optional[str]:
        """Find the actual filing document link using multiple strategies."""
        
        # Strategy 1: Look for primary document based on filing type
        primary_patterns = {
            '10-K': ['10-k', 'annual report', 'form 10-k'],
            '10-Q': ['10-q', 'quarterly report', 'form 10-q'],
            '8-K': ['8-k', 'current report', 'form 8-k'],
            'DEF 14A': ['def 14a', 'proxy statement', 'definitive proxy'],
            '3': ['form 3', 'initial statement'],
            '4': ['form 4', 'statement of changes'],
            '5': ['form 5', 'annual statement']
        }
        
        patterns = primary_patterns.get(filing_type, [filing_type.lower()])
        
        # Look for links with filing-specific text
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            
            if ('.htm' in href and '/Archives/edgar/data/' in href and
                not href.endswith('-index.htm') and
                not 'FilingSummary' in href and
                not 'xslF345X03' in href):
                
                # Check if link text matches filing type patterns
                if any(pattern in link_text for pattern in patterns):
                    return href
                
                # Check for "complete submission text file" which is often the main document
                if 'complete submission text file' in link_text:
                    return href
        
        # Strategy 2: Look for the first substantial .htm document
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            
            if ('.htm' in href and '/Archives/edgar/data/' in href and
                not href.endswith('-index.htm') and
                not 'FilingSummary' in href and
                not 'xslF345X03' in href and
                not 'R1.htm' in href and  # Skip exhibits
                not 'R2.htm' in href):
                return href
        
        return None
    
    def _find_text_version(self, soup) -> Optional[str]:
        """Find text version of the filing as fallback."""
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            link_text = link.get_text(strip=True).lower()
            
            if ('.txt' in href and '/Archives/edgar/data/' in href and
                ('complete submission text file' in link_text or 'text' in link_text)):
                return href
        
        return None
    
    def _construct_document_url(self, document_link: str) -> str:
        """Construct full document URL from relative link."""
        
        if document_link.startswith('http'):
            return document_link
        elif document_link.startswith('/'):
            return f"https://www.sec.gov{document_link}"
        else:
            return f"https://www.sec.gov/{document_link}"
    
    def _validate_filing_content(self, content: str, filing_type: str) -> bool:
        """Validate that content is actual SEC filing, not XBRL viewer page."""
        
        content_lower = content.lower()
        
        # Check for XBRL viewer indicators (bad signs)
        xbrl_indicators = [
            'xbrl viewer',
            'ixviewer',
            'loadviewer',
            'javascript',
            'iframe',
            'this page uses javascript'
        ]
        
        xbrl_count = sum(1 for indicator in xbrl_indicators if indicator in content_lower)
        
        # If too many XBRL indicators and short content, likely a viewer page
        if xbrl_count >= 3 and len(content.split()) < 1000:
            return False
        
        # Check for actual filing content indicators (good signs)
        filing_indicators = {
            '10-K': ['annual report', 'business overview', 'risk factors', 'management discussion'],
            '10-Q': ['quarterly report', 'financial statements', 'condensed consolidated'],
            '8-K': ['current report', 'item 1', 'item 2', 'signature'],
            'DEF 14A': ['proxy statement', 'annual meeting', 'executive compensation'],
            '3': ['initial statement', 'beneficial ownership'],
            '4': ['statement of changes', 'securities acquired'],
            '5': ['annual statement', 'securities beneficially owned']
        }
        
        expected_indicators = filing_indicators.get(filing_type, ['sec filing', 'securities'])
        filing_content_count = sum(1 for indicator in expected_indicators if indicator in content_lower)
        
        # Good content should have filing-specific indicators and reasonable length
        return filing_content_count > 0 and len(content.split()) > 500
    
    def _load_request_count(self):
        """Load request count from cache file."""
        cache_file = os.path.join(RAW_DATA_DIR, '.request_cache.json')
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    today = datetime.now().strftime('%Y-%m-%d')
                    if cache_data.get('date') == today:
                        self.request_count = cache_data.get('count', 0)
                        print(f"Loaded request count: {self.request_count}/{self.max_requests_per_day}")
            except Exception as e:
                print(f"Error loading request cache: {e}")
    
    def _save_request_count(self):
        """Save request count to cache file."""
        cache_file = os.path.join(RAW_DATA_DIR, '.request_cache.json')
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        try:
            cache_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': self.request_count
            }
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving request cache: {e}")
    
    def _can_make_request(self) -> bool:
        """Check if we can make another API request."""
        return self.request_count < self.max_requests_per_day
    
    def search_filings_with_fallback(self, ticker: str, filing_type: str,
                                   start_date: str = "2022-01-01",
                                   end_date: str = "2024-01-01") -> List[Dict]:
        """Search for SEC filings with fallback to direct EDGAR access."""
        
        # Try API first if we have requests left
        if self.api_key and self._can_make_request():
            try:
                filings = self.search_filings(ticker, filing_type, start_date, end_date)
                if filings:
                    self.request_count += 1
                    self._save_request_count()
                    return filings
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"API rate limit reached. Switching to fallback method.")
                    self.request_count = self.max_requests_per_day
                    self._save_request_count()
                else:
                    print(f"API error: {e}")
        
        # Fallback to direct EDGAR RSS feeds or existing data
        print(f"Using fallback method for {ticker} {filing_type}")
        return self._fallback_search_filings(ticker, filing_type, start_date, end_date)
    
    def _fallback_search_filings(self, ticker: str, filing_type: str,
                               start_date: str, end_date: str) -> List[Dict]:
        """Fallback method to search filings using direct EDGAR access."""
        
        # Check if we already have downloaded files for this company/filing type
        existing_files = self._find_existing_files(ticker, filing_type)
        if existing_files:
            print(f"Found {len(existing_files)} existing files for {ticker} {filing_type}")
            return existing_files
        
        # Try to construct filing URLs based on known patterns
        # This is a simplified fallback - in production you might use RSS feeds
        fallback_filings = []
        
        # For major companies, we can try some common filing patterns
        if ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']:
            # This is a simplified example - you'd need more sophisticated logic
            base_url = "https://www.sec.gov/Archives/edgar/data"
            
            # Try to find recent filings (this is very basic)
            for year in ['2023', '2022']:
                filing_info = {
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "filing_date": f"{year}-12-31",
                    "filing_url": f"{base_url}/example/{ticker}_{filing_type}_{year}.html",
                    "company_name": f"{ticker} Inc.",
                    "form_type": filing_type,
                    "accession_number": f"0000000000-{year}-000001",
                    "cik": "0000000000"
                }
                fallback_filings.append(filing_info)
        
        return fallback_filings[:3]  # Limit to 3 fallback filings
    
    def _find_existing_files(self, ticker: str, filing_type: str) -> List[Dict]:
        """Find existing downloaded files for a company/filing type."""
        
        existing_files = []
        
        if os.path.exists(RAW_DATA_DIR):
            for filename in os.listdir(RAW_DATA_DIR):
                # Handle both underscore and dash patterns in filing types
                pattern1 = f"{ticker}_{filing_type}_"
                pattern2 = f"{ticker}_{filing_type.replace('-', '')}_"  # Handle 10K vs 10-K
                
                if ((filename.startswith(pattern1) or filename.startswith(pattern2)) and 
                    filename.endswith('.html')):
                    
                    # Extract date from filename
                    parts = filename.replace('.html', '').split('_')
                    if len(parts) >= 3:
                        date_part = parts[-1]  # Last part should be the date
                        
                        # Validate date format (YYYYMMDD)
                        if len(date_part) == 8 and date_part.isdigit():
                            filing_info = {
                                "ticker": ticker,
                                "filing_type": filing_type,
                                "filing_date": f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}",
                                "filing_url": f"file://{os.path.join(RAW_DATA_DIR, filename)}",
                                "company_name": f"{ticker} Inc.",
                                "form_type": filing_type,
                                "accession_number": "existing",
                                "cik": "existing",
                                "local_file": True
                            }
                            existing_files.append(filing_info)
        
        return existing_files
    
    def download_filing_enhanced(self, filing_url: str, ticker: str,
                               filing_type: str, filing_date: str) -> Optional[str]:
        """Enhanced filing download with multiple strategies."""
        
        # If it's a local file, just return the path
        if filing_url.startswith('file://'):
            local_path = filing_url.replace('file://', '')
            if os.path.exists(local_path):
                print(f"Using existing local file: {local_path}")
                return local_path
        
        # Try multiple download strategies
        strategies = [
            self._download_via_direct_link,
            self._download_via_text_version,
            self._download_via_rss_feed
        ]
        
        for strategy in strategies:
            try:
                result = strategy(filing_url, ticker, filing_type, filing_date)
                if result:
                    return result
            except Exception as e:
                print(f"Strategy failed: {e}")
                continue
        
        print(f"All download strategies failed for {ticker} {filing_type}")
        return None
    
    def _download_via_direct_link(self, filing_url: str, ticker: str,
                                filing_type: str, filing_date: str) -> Optional[str]:
        """Download via direct link (original method)."""
        return self.download_filing(filing_url, ticker, filing_type, filing_date)
    
    def _download_via_text_version(self, filing_url: str, ticker: str,
                                 filing_type: str, filing_date: str) -> Optional[str]:
        """Try to download text version of filing."""
        
        try:
            # Convert HTML URL to text URL
            if '.htm' in filing_url:
                text_url = filing_url.replace('.htm', '.txt')
                
                headers = {
                    'User-Agent': 'SEC Filing QA Agent research@example.com',
                    'Accept': 'text/plain'
                }
                
                response = self.session.get(text_url, headers=headers)
                response.raise_for_status()
                
                # Create filename
                safe_date = filing_date.replace("-", "").replace("T", "_").split("_")[0]
                filename = f"{ticker}_{filing_type}_{safe_date}.txt"
                filepath = os.path.join(RAW_DATA_DIR, filename)
                
                os.makedirs(RAW_DATA_DIR, exist_ok=True)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                print(f"Downloaded text version: {filename}")
                return filepath
                
        except Exception as e:
            print(f"Text version download failed: {e}")
            return None
    
    def _download_via_rss_feed(self, filing_url: str, ticker: str,
                             filing_type: str, filing_date: str) -> Optional[str]:
        """Try to download via RSS feed lookup (placeholder)."""
        
        # This would implement RSS feed lookup
        # For now, just return None to indicate this strategy failed
        print("RSS feed strategy not implemented yet")
        return None