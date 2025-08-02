# SEC Filings QA Agent - Complete Setup Guide

This guide provides step-by-step instructions for setting up and running the SEC Filings QA Agent system from scratch.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 5GB free space for data and embeddings
- **Internet**: Stable connection for API access

### Required API Keys
1. **SEC API Key** (sec-api.io)
   - Sign up at: https://sec-api.io/
   - Free tier: 100 requests/day
   - Premium tier recommended for production use

2. **Google Gemini API Key**
   - Sign up at: https://makersuite.google.com/app/apikey
   - Free tier available with generous limits

## Installation Steps

### Step 1: Clone and Navigate to Project
```bash
# If you have the project files
cd "C:\Users\rehan\OneDrive\Desktop\Scalar Field\salar-projet"

# Or if downloading from repository
git clone <repository-url>
cd salar-projet
```

### Step 2: Create Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv in prompt)
which python  # Should point to venv/Scripts/python or venv/bin/python
```

### Step 3: Install Dependencies
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "(requests|beautifulsoup4|chromadb|google-generativeai)"
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root directory:

```bash
# Create .env file
# On Windows:
echo. > .env

# On macOS/Linux:
touch .env
```

Edit the `.env` file with your API keys:
```env
# SEC API Configuration
SEC_API_KEY=your_sec_api_key_here
SEC_API_BASE_URL=https://api.sec-api.io

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# System Configuration (optional)
LOG_LEVEL=INFO
MAX_CONCURRENT_DOWNLOADS=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Step 5: Verify API Connectivity
```bash
# Test SEC API connection
python test_api.py

# Expected output:
# ✅ SEC API connection successful
# ✅ Found X filings for AAPL
# ✅ Sample filing data retrieved
```

### Step 6: Initialize System
```bash
# Run the main application (will setup system on first run)
python src/main.py

# This will:
# 1. Download SEC filings (may take 10-30 minutes)
# 2. Process documents and create embeddings
# 3. Initialize vector database
# 4. Start query interface
```

## Configuration Options

### Company Selection
Edit `src/config/settings.py` to modify company coverage:

```python
COMPANIES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    # Add or remove companies as needed
}
```

### Filing Types
Modify filing types in `src/config/settings.py`:

```python
FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A", "3", "4", "5"]
# Remove types you don't need to reduce download time
```

### Date Range
Adjust the date range for filing collection:

```python
START_DATE = "2022-01-01"
END_DATE = "2024-01-01"
# Shorter ranges = faster setup, less data
```

## Verification and Testing

### Step 1: Run System Validation
```bash
# Run the demonstration script
python Deliverables/demo_script.py

# This will:
# - Validate system components
# - Run sample queries
# - Display performance metrics
```

### Step 2: Manual Testing
```python
# Test basic functionality
from src.main import SECFilingsQA

# Initialize system
qa_system = SECFilingsQA()

# Test simple query
response = qa_system.query("What was Apple's revenue in 2023?")
print(response['answer'])
print(response['sources'])
```

### Step 3: Check Data Quality
```bash
# Verify downloaded files
ls data/raw/*.html | wc -l  # Should show ~298 files

# Check download log
cat data/raw/download_log.json | grep "success_rate"
# Should show 100% success rate
```

## Troubleshooting Common Issues

### Issue 1: API Key Errors
**Symptoms**: 401 Unauthorized or API key invalid errors

**Solutions**:
```bash
# Verify .env file exists and has correct format
cat .env

# Check API key validity
curl -H "Authorization: YOUR_SEC_API_KEY" https://api.sec-api.io/

# Ensure no extra spaces or quotes in .env file
```

### Issue 2: Memory Issues
**Symptoms**: Out of memory errors during processing

**Solutions**:
```python
# Reduce batch size in settings.py
BATCH_SIZE = 5  # Reduce from default 10

# Process fewer companies initially
COMPANIES = {"AAPL": "Apple Inc."}  # Start with one company
```

### Issue 3: Slow Performance
**Symptoms**: Long response times or timeouts

**Solutions**:
```python
# Optimize chunk size
CHUNK_SIZE = 500  # Reduce from 1000
CHUNK_OVERLAP = 100  # Reduce from 200

# Use company filters in queries
response = qa_system.query("Revenue question", company_filter="AAPL")
```

### Issue 4: Network Connectivity
**Symptoms**: Connection timeouts or SSL errors

**Solutions**:
```bash
# Test basic connectivity
ping sec-api.io
ping generativelanguage.googleapis.com

# Check firewall/proxy settings
# Ensure ports 80 and 443 are open
```

### Issue 5: Missing Dependencies
**Symptoms**: Import errors or module not found

**Solutions**:
```bash
# Reinstall dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Check for conflicting packages
pip check

# Use specific versions if needed
pip install chromadb==0.4.15
```

## Performance Optimization

### For Development/Testing
```python
# Quick setup configuration
COMPANIES = {"AAPL": "Apple Inc."}  # Single company
FILING_TYPES = ["10-K", "10-Q"]    # Essential filings only
START_DATE = "2023-01-01"          # Recent data only
```

### For Production Use
```python
# Full configuration
COMPANIES = {/* all 14 companies */}
FILING_TYPES = ["10-K", "10-Q", "8-K", "DEF 14A", "3", "4", "5"]
START_DATE = "2022-01-01"
```

### Memory Optimization
```python
# Reduce memory usage
CHUNK_SIZE = 800
MAX_CONCURRENT_DOWNLOADS = 3
EMBEDDING_BATCH_SIZE = 50
```

## Maintenance and Updates

### Regular Maintenance
```bash
# Update filings (run monthly)
python src/data_collection/update_filings.py

# Clean up old logs
find logs/ -name "*.log" -mtime +30 -delete

# Backup vector database
cp -r data/vector_store data/vector_store_backup_$(date +%Y%m%d)
```

### System Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update API endpoints if needed
# Check src/config/settings.py for any changes
```

## Support and Resources

### Documentation
- `WORKING_SYSTEM.md`: Comprehensive system documentation
- `TECHNICAL_SUMMARY.md`: Technical architecture details
- `EXAMPLE_QUERIES.md`: Query examples and best practices
- `VALIDATION_REPORT.md`: Testing and validation results

### Logs and Debugging
```bash
# Check system logs
tail -f logs/system.log

# Check API logs
tail -f logs/api.log

# Check query logs
tail -f logs/query.log
```

### Getting Help
1. **Check logs** for specific error messages
2. **Review configuration** in `.env` and `settings.py`
3. **Test API connectivity** using `test_api.py`
4. **Run validation** using `demo_script.py`
5. **Check system resources** (memory, disk space)

### Performance Monitoring
```python
# Monitor system performance
from src.utils.monitoring import SystemMonitor

monitor = SystemMonitor()
stats = monitor.get_system_stats()
print(f"Memory usage: {stats['memory_usage']}")
print(f"Query performance: {stats['avg_query_time']}")
```

## Next Steps

After successful setup:

1. **Explore Example Queries**: Try queries from `EXAMPLE_QUERIES.md`
2. **Run Demonstrations**: Execute `demo_script.py` for full system demo
3. **Customize Configuration**: Adjust settings for your specific needs
4. **Integrate with Workflows**: Use the API for your research applications
5. **Monitor Performance**: Set up regular monitoring and maintenance

The system is now ready for quantitative research and financial analysis tasks!
