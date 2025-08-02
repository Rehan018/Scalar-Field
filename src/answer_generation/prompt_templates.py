from typing import Dict, List


class PromptTemplates:
    
    @staticmethod
    def single_company_analysis(query: str, company_name: str, ticker: str, 
                               context_chunks: List[Dict]) -> str:
        """Template for single company analysis."""
        
        context_text = "\n\n".join([
            f"Source {i+1} ({chunk['metadata'].get('filing_type', 'Unknown')} - {chunk['metadata'].get('filing_date', 'Unknown')}):\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks[:5])
        ])
        
        return f"""
You are a financial analyst specializing in SEC filings analysis. Please answer the following question about {company_name} ({ticker}) based on the provided SEC filing excerpts.

Question: {query}

Relevant SEC Filing Excerpts:
{context_text}

Please provide a comprehensive answer that:
1. Directly addresses the question
2. Uses specific information from the SEC filings
3. Cites the relevant filing types and dates
4. Provides quantitative data when available
5. Acknowledges any limitations or uncertainties

Answer:
"""
    
    @staticmethod
    def multi_company_comparison(query: str, companies: List[str], 
                               context_chunks: List[Dict]) -> str:
        """Template for multi-company comparison."""
        
        # Group chunks by company
        company_contexts = {}
        for chunk in context_chunks:
            ticker = chunk['metadata'].get('ticker', 'Unknown')
            if ticker not in company_contexts:
                company_contexts[ticker] = []
            company_contexts[ticker].append(chunk)
        
        context_sections = []
        for ticker, chunks in company_contexts.items():
            company_text = "\n".join([
                f"- {chunk['metadata'].get('filing_type', 'Unknown')} ({chunk['metadata'].get('filing_date', 'Unknown')}): {chunk['text'][:500]}..."
                for chunk in chunks[:3]
            ])
            context_sections.append(f"{ticker}:\n{company_text}")
        
        context_text = "\n\n".join(context_sections)
        
        return f"""
You are a financial analyst comparing multiple companies based on their SEC filings. Please provide a comparative analysis for the following question.

Question: {query}

Companies to Compare: {', '.join(companies)}

Relevant SEC Filing Information:
{context_text}

Please provide a comparative analysis that:
1. Compares and contrasts the companies on the requested dimension
2. Uses specific data from SEC filings
3. Identifies key similarities and differences
4. Provides quantitative comparisons when possible
5. Cites specific filing sources
6. Concludes with key insights

Comparative Analysis:
"""
    
    @staticmethod
    def temporal_analysis(query: str, ticker: str, time_periods: List[str],
                         context_chunks: List[Dict]) -> str:
        """Template for temporal/trend analysis."""
        
        # Sort chunks by date
        sorted_chunks = sorted(
            context_chunks,
            key=lambda x: x['metadata'].get('filing_date', ''),
            reverse=True
        )
        
        context_text = "\n\n".join([
            f"Period {chunk['metadata'].get('filing_date', 'Unknown')} ({chunk['metadata'].get('filing_type', 'Unknown')}):\n{chunk['text']}"
            for chunk in sorted_chunks[:6]
        ])
        
        return f"""
You are a financial analyst conducting temporal analysis of SEC filings. Please analyze trends and changes over time for the following question.

Question: {query}

Company: {ticker}
Time Periods of Interest: {', '.join(time_periods) if time_periods else 'Multiple periods'}

Chronological SEC Filing Information:
{context_text}

Please provide a temporal analysis that:
1. Identifies trends and patterns over time
2. Highlights significant changes or developments
3. Uses specific data points from different time periods
4. Explains potential causes for observed trends
5. Cites specific filing dates and types
6. Provides forward-looking insights when appropriate

Temporal Analysis:
"""
    
    @staticmethod
    def cross_sectional_analysis(query: str, financial_concepts: List[str],
                               context_chunks: List[Dict]) -> str:
        """Template for cross-sectional industry analysis."""
        
        # Group by sector if available
        sector_contexts = {}
        for chunk in context_chunks:
            # This would need sector mapping from company metadata
            ticker = chunk['metadata'].get('ticker', 'Unknown')
            sector = "General"  # Simplified for now
            
            if sector not in sector_contexts:
                sector_contexts[sector] = []
            sector_contexts[sector].append(chunk)
        
        context_text = "\n\n".join([
            f"Company {chunk['metadata'].get('ticker', 'Unknown')} ({chunk['metadata'].get('filing_type', 'Unknown')}):\n{chunk['text'][:400]}..."
            for chunk in context_chunks[:8]
        ])
        
        return f"""
You are a financial analyst conducting cross-sectional analysis across multiple companies and sectors. Please analyze the following question across the industry.

Question: {query}

Financial Concepts: {', '.join(financial_concepts)}

Cross-Company SEC Filing Information:
{context_text}

Please provide a cross-sectional analysis that:
1. Identifies common patterns across companies
2. Highlights industry-wide trends and practices
3. Compares different approaches by companies
4. Uses specific examples from multiple companies
5. Identifies outliers or unique approaches
6. Provides industry-level insights and implications

Cross-Sectional Analysis:
"""
    
    @staticmethod
    def risk_factor_analysis(query: str, context_chunks: List[Dict]) -> str:
        """Template specifically for risk factor analysis."""
        
        context_text = "\n\n".join([
            f"{chunk['metadata'].get('ticker', 'Unknown')} Risk Factors ({chunk['metadata'].get('filing_date', 'Unknown')}):\n{chunk['text']}"
            for chunk in context_chunks[:5]
        ])
        
        return f"""
You are a financial analyst specializing in risk assessment based on SEC filings. Please analyze the risk factors for the following question.

Question: {query}

Risk Factor Disclosures from SEC Filings:
{context_text}

Please provide a risk analysis that:
1. Identifies and categorizes the main risk factors
2. Assesses the potential impact and likelihood of risks
3. Compares risk profiles across companies (if applicable)
4. Identifies emerging or evolving risks
5. Provides specific examples from the filings
6. Offers insights on risk management implications

Risk Factor Analysis:
"""
    
    @staticmethod
    def financial_metrics_analysis(query: str, context_chunks: List[Dict]) -> str:
        """Template for financial metrics and performance analysis."""
        
        context_text = "\n\n".join([
            f"{chunk['metadata'].get('ticker', 'Unknown')} Financial Data ({chunk['metadata'].get('filing_type', 'Unknown')} - {chunk['metadata'].get('filing_date', 'Unknown')}):\n{chunk['text']}"
            for chunk in context_chunks[:6]
        ])
        
        return f"""
You are a financial analyst conducting quantitative analysis of financial metrics from SEC filings. Please analyze the following question with focus on numerical data and financial performance.

Question: {query}

Financial Information from SEC Filings:
{context_text}

Please provide a financial metrics analysis that:
1. Extracts and presents relevant financial data
2. Calculates key financial ratios when possible
3. Identifies trends in financial performance
4. Compares metrics across time periods or companies
5. Provides context for the financial numbers
6. Offers insights on financial health and performance

Financial Metrics Analysis:
"""
    
    @staticmethod
    def general_qa_template(query: str, context_chunks: List[Dict]) -> str:
        """General template for any SEC filing question."""
        
        context_text = "\n\n".join([
            f"Source {i+1} - {chunk['metadata'].get('ticker', 'Unknown')} ({chunk['metadata'].get('filing_type', 'Unknown')}, {chunk['metadata'].get('filing_date', 'Unknown')}):\n{chunk['text']}"
            for i, chunk in enumerate(context_chunks[:5])
        ])
        
        return f"""
You are an expert financial analyst with deep knowledge of SEC filings and financial markets. Please answer the following question based on the provided SEC filing excerpts.

Question: {query}

Relevant SEC Filing Excerpts:
{context_text}

Please provide a comprehensive answer that:
1. Directly addresses the question asked
2. Uses specific information and data from the SEC filings
3. Provides proper attribution to filing sources (company, filing type, date)
4. Acknowledges any limitations in the available information
5. Offers professional insights based on the financial data
6. Uses clear, professional language appropriate for financial analysis

Answer:
"""