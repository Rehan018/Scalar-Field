# SEC Filings QA Agent - Example Queries

This document provides comprehensive examples of queries that demonstrate the system's capabilities for financial research and analysis.

## Query Categories

### 1. Financial Performance Analysis

#### Revenue and Growth Metrics
```python
# Query: Revenue growth analysis
query = "What was Apple's revenue growth rate in fiscal year 2023?"

# Expected Response:
{
    'answer': 'Apple reported total net sales of $383.3 billion in fiscal 2023, representing a decline of 3% compared to fiscal 2022 net sales of $394.3 billion. This decline was primarily attributed to challenging macroeconomic conditions and foreign exchange headwinds.',
    'sources': [
        {
            'company': 'AAPL',
            'filing_type': '10-K',
            'filing_date': '2023-11-02',
            'section': 'Management Discussion and Analysis',
            'relevance_score': 0.95
        }
    ],
    'confidence': 0.92
}
```

#### Profitability Analysis
```python
# Query: Margin analysis
query = "Compare the operating margins of Microsoft and Apple in 2023"

# Expected insights:
# - Microsoft's operating margin trends
# - Apple's operating margin performance
# - Comparative analysis with industry context
# - Factors affecting margin differences
```

#### Cash Flow Analysis
```python
# Query: Cash flow assessment
query = "What were JPMorgan's operating cash flows in Q3 2023?"

# System will retrieve:
# - Specific cash flow statement data
# - Year-over-year comparisons
# - Management commentary on cash flow drivers
# - Regulatory capital impacts
```

### 2. Risk Assessment Queries

#### Business Risk Factors
```python
# Query: Risk identification
query = "What are the main risk factors facing Boeing in 2023?"

# Expected analysis:
# - Regulatory risks and compliance issues
# - Manufacturing and supply chain risks
# - Market competition and demand risks
# - Financial and liquidity risks
```

#### Market Risk Analysis
```python
# Query: Market exposure assessment
query = "How is Exxon Mobil exposed to oil price volatility?"

# System provides:
# - Commodity price sensitivity analysis
# - Hedging strategies and derivatives usage
# - Geographic exposure breakdown
# - Historical impact of price changes
```

#### Credit Risk Evaluation
```python
# Query: Credit risk assessment
query = "What is Bank of America's approach to credit risk management?"

# Response includes:
# - Credit risk policies and procedures
# - Loan loss provisions and allowances
# - Portfolio composition and quality metrics
# - Stress testing and scenario analysis
```

### 3. Strategic Analysis

#### Business Strategy Assessment
```python
# Query: Strategic direction analysis
query = "What is Amazon's strategy for cloud computing growth?"

# Expected insights:
# - AWS strategic initiatives and investments
# - Competitive positioning and market share
# - Technology innovation and R&D focus
# - Geographic expansion plans
```

#### Merger and Acquisition Activity
```python
# Query: M&A analysis
query = "What acquisitions did Microsoft announce in 2023?"

# System retrieves:
# - Announced transactions and deal values
# - Strategic rationale and synergies
# - Integration plans and timelines
# - Regulatory approval status
```

#### Capital Allocation Strategy
```python
# Query: Capital allocation assessment
query = "How does Chevron allocate capital between growth and returns to shareholders?"

# Response covers:
# - Capital expenditure priorities and allocation
# - Dividend policy and share repurchase programs
# - Investment in renewable energy and transition
# - Debt management and capital structure optimization
```

### 4. Regulatory and Compliance

#### Regulatory Environment
```python
# Query: Regulatory impact analysis
query = "How do new banking regulations affect Wells Fargo's operations?"

# Expected analysis:
# - Specific regulatory changes and requirements
# - Compliance costs and implementation timelines
# - Impact on business operations and strategy
# - Management's assessment of regulatory risks
```

#### Environmental and Social Governance
```python
# Query: ESG assessment
query = "What are Johnson & Johnson's sustainability initiatives?"

# System provides:
# - Environmental impact reduction goals
# - Social responsibility programs and metrics
# - Governance structure and board composition
# - ESG reporting and transparency measures
```

### 5. Comparative Analysis

#### Cross-Company Comparisons
```python
# Query: Peer comparison
query = "Compare the debt-to-equity ratios of JPMorgan, Bank of America, and Wells Fargo"

# Expected output:
# - Current debt-to-equity ratios for each bank
# - Historical trends and changes over time
# - Regulatory capital requirements and compliance
# - Management commentary on capital structure
```

#### Sector Analysis
```python
# Query: Industry comparison
query = "How do technology companies' R&D spending compare as a percentage of revenue?"

# Response includes:
# - R&D spending ratios for Apple, Microsoft, Amazon, Google
# - Industry benchmarks and trends
# - Innovation focus areas and strategic priorities
# - Impact on competitive positioning
```

### 6. Temporal Analysis

#### Trend Identification
```python
# Query: Historical trend analysis
query = "What has been the trend in Pfizer's pharmaceutical revenue over the past two years?"

# System analyzes:
# - Quarterly and annual revenue progression
# - Product portfolio performance and changes
# - Market dynamics and competitive factors
# - Management guidance and outlook
```

#### Seasonal Patterns
```python
# Query: Seasonality assessment
query = "Does Walmart show seasonal patterns in its quarterly performance?"

# Expected insights:
# - Quarterly revenue and earnings patterns
# - Holiday season impact and performance
# - Inventory management and working capital cycles
# - Management discussion of seasonal factors
```

## Advanced Query Techniques

### 1. Multi-Dimensional Filtering

```python
# Query with specific filters
response = qa_system.query(
    "What were the key financial highlights?",
    company_filter="AAPL",
    filing_type_filter="10-Q",
    date_filter="2023-Q3"
)
```

### 2. Cross-Reference Analysis

```python
# Query requiring multiple document synthesis
query = "How do Apple's capital expenditures in 2023 compare to their guidance provided in 2022?"

# System will:
# - Retrieve actual capex from 2023 filings
# - Find guidance statements from 2022 filings
# - Compare actual vs. guidance
# - Provide variance analysis and explanations
```

### 3. Quantitative Extraction

```python
# Query for specific financial metrics
query = "Extract the quarterly revenue figures for Microsoft in 2023"

# Expected structured output:
{
    'Q1_2023': '$52.9 billion',
    'Q2_2023': '$56.2 billion', 
    'Q3_2023': '$61.9 billion',
    'Q4_2023': '$56.5 billion',
    'sources': [...],
    'methodology': 'Extracted from quarterly 10-Q filings'
}
```

## Query Optimization Tips

### 1. Specificity Improves Accuracy
- **Good**: "What was Apple's iPhone revenue in Q4 2023?"
- **Better**: "What was Apple's iPhone revenue in the fourth quarter of fiscal 2023?"

### 2. Use Company Filters for Focused Analysis
```python
# More efficient and accurate
response = qa_system.query(
    "What are the main revenue segments?",
    company_filter="MSFT"
)
```

### 3. Leverage Filing Type Knowledge
- **10-K**: Annual comprehensive analysis, risk factors, business overview
- **10-Q**: Quarterly updates, recent performance, management discussion
- **8-K**: Material events, acquisitions, management changes
- **DEF 14A**: Executive compensation, governance, shareholder proposals

### 4. Time-Specific Queries
```python
# Specify time periods for better context
query = "How did the COVID-19 pandemic impact airline industry performance in 2022?"
```

## Expected Response Quality

### High-Quality Responses Include:
1. **Specific Data Points**: Exact figures with proper context
2. **Source Attribution**: Clear references to specific filings
3. **Contextual Analysis**: Industry and historical perspective
4. **Confidence Indicators**: Reliability scores for answers

### Response Limitations:
1. **Calculation Boundaries**: System provides data but may not perform complex calculations
2. **Forward-Looking Statements**: Limited to what's explicitly stated in filings
3. **Cross-Document Synthesis**: Complex multi-step reasoning may require clarification

## Sample Evaluation Questions

These queries test the system's capabilities across different dimensions:

### 1. Factual Retrieval
"What was Amazon's total revenue in 2023?"

### 2. Analytical Reasoning
"Why did General Electric's operating margin improve in 2023?"

### 3. Comparative Analysis
"Which company has higher R&D intensity: Apple or Microsoft?"

### 4. Risk Assessment
"What are Caterpillar's main operational risks?"

### 5. Strategic Understanding
"How is Exxon Mobil positioning for the energy transition?"

### 6. Financial Health
"What is JPMorgan's capital adequacy ratio?"

### 7. Market Position
"How does Walmart describe its competitive advantages?"

### 8. Regulatory Impact
"How do new regulations affect Pfizer's drug development?"

### 9. Operational Efficiency
"What cost reduction initiatives has Boeing implemented?"

### 10. Future Outlook
"What is Microsoft's guidance for cloud computing growth?"

## Best Practices for Query Formulation

1. **Be Specific**: Include company names, time periods, and specific metrics
2. **Use Financial Terminology**: Leverage domain-specific language for better results
3. **Consider Context**: Frame questions within appropriate business context
4. **Iterate and Refine**: Use follow-up queries to drill down into specific areas
5. **Validate Sources**: Always review source attributions for accuracy

This comprehensive query framework demonstrates the system's ability to handle sophisticated financial research questions across multiple dimensions and use cases.
