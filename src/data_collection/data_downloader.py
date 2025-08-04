import asyncio
import os
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import json

from .sec_api_client import SECAPIClient
from config.settings import COMPANIES, FILING_TYPES, MAX_CONCURRENT_DOWNLOADS, RAW_DATA_DIR


class DataDownloader:
    def __init__(self):
        self.sec_client = SECAPIClient()
        self.max_workers = MAX_CONCURRENT_DOWNLOADS
        
    def download_single_company(self, ticker: str) -> Dict:
        """Download filings for a single company."""
        
        print(f"Starting download for {ticker} - {COMPANIES[ticker]['name']}")
        
        try:
            downloaded_files = self.download_company_filings_enhanced(
                ticker, FILING_TYPES
            )
            
            result = {
                "ticker": ticker,
                "company_name": COMPANIES[ticker]["name"],
                "sector": COMPANIES[ticker]["sector"],
                "downloaded_files": downloaded_files,
                "total_files": len(downloaded_files),
                "status": "success"
            }
            
            print(f"Completed {ticker}: {len(downloaded_files)} files downloaded")
            return result
            
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")
            return {
                "ticker": ticker,
                "company_name": COMPANIES[ticker]["name"],
                "sector": COMPANIES[ticker]["sector"],
                "downloaded_files": [],
                "total_files": 0,
                "status": "error",
                "error": str(e)
            }
    
    def download_all_companies(self) -> Dict:
        """Download filings for all companies using thread pool."""
        
        print(f"Starting download for {len(COMPANIES)} companies...")
        print(f"Filing types: {', '.join(FILING_TYPES)}")
        
        # Ensure raw data directory exists
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_ticker = {
                executor.submit(self.download_single_company, ticker): ticker 
                for ticker in COMPANIES.keys()
            }
            
            # Collect results as they complete
            for future in future_to_ticker:
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Exception for {ticker}: {e}")
                    results.append({
                        "ticker": ticker,
                        "status": "error",
                        "error": str(e)
                    })
        
        # Generate summary
        summary = self._generate_summary(results)
        
        # Save download log
        self._save_download_log(results, summary)
        
        return {
            "results": results,
            "summary": summary
        }
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate download summary statistics."""
        
        total_companies = len(results)
        successful_companies = len([r for r in results if r["status"] == "success"])
        total_files = sum(r.get("total_files", 0) for r in results)
        
        sector_breakdown = {}
        for result in results:
            sector = result.get("sector", "Unknown")
            if sector not in sector_breakdown:
                sector_breakdown[sector] = {"companies": 0, "files": 0}
            sector_breakdown[sector]["companies"] += 1
            sector_breakdown[sector]["files"] += result.get("total_files", 0)
        
        return {
            "total_companies": total_companies,
            "successful_companies": successful_companies,
            "failed_companies": total_companies - successful_companies,
            "total_files_downloaded": total_files,
            "sector_breakdown": sector_breakdown,
            "success_rate": f"{(successful_companies/total_companies)*100:.1f}%"
        }
    
    def _save_download_log(self, results: List[Dict], summary: Dict):
        """Save download results and summary to JSON file."""
        
        log_data = {
            "download_timestamp": asyncio.get_event_loop().time(),
            "summary": summary,
            "detailed_results": results
        }
        
        log_file = os.path.join(RAW_DATA_DIR, "download_log.json")
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"Download log saved to: {log_file}")
    
    def download_company_filings_enhanced(self, ticker: str, filing_types: List[str]) -> List[str]:
        """Enhanced download method with fallback strategies."""
        
        downloaded_files = []
        
        for filing_type in filing_types:
            print(f"Processing {filing_type} filings for {ticker}...")
            
            # Use enhanced search with fallback
            filings = self.sec_client.search_filings_with_fallback(
                ticker, filing_type, "2022-01-01", "2024-01-01"
            )
            
            # Limit to 3 filings per type to manage API usage
            limited_filings = filings[:3]
            
            for filing in limited_filings:
                if filing.get("filing_url"):
                    # Use enhanced download method
                    filepath = self.sec_client.download_filing_enhanced(
                        filing["filing_url"],
                        filing["ticker"],
                        filing["filing_type"],
                        filing["filing_date"]
                    )
                    if filepath:
                        downloaded_files.append(filepath)
        
        return downloaded_files
    
    def get_download_status(self) -> Dict:
        """Get status of previous downloads."""
        
        log_file = os.path.join(RAW_DATA_DIR, "download_log.json")
        
        if not os.path.exists(log_file):
            return {"status": "no_previous_downloads"}
        
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"status": "error", "error": str(e)}