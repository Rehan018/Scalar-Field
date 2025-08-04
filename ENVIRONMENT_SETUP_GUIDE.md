# Environment Setup Guide

**Project Repository:** https://github.com/Rehan018/Scalar-Field.git

This comprehensive guide covers all aspects of environment configuration for the SEC Filings QA Agent, from basic setup to advanced performance tuning.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file with your specific values:**
   ```bash
   nano .env
   # or
   code .env
   ```

3. **Required Configuration:**
   - Set your `SEC_API_KEY` (get from https://sec-api.io/)
   - Configure `OLLAMA_URL` to point to your Ollama server
   - Verify `OLLAMA_MODEL` matches your installed model

## Environment Variables Reference

### 🔑 API Keys & Authentication

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SEC_API_KEY` | ✅ Yes | SEC API key from sec-api.io | `your_api_key_here` |
| `GEMINI_API_KEY` | ❌ No | Legacy Gemini API key (optional) | `your_gemini_key` |

### 🤖 Local LLM Configuration

| Variable | Default | Description | Options |
|----------|---------|-------------|---------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL | Any valid URL |
| `OLLAMA_MODEL` | `llama3.1:8b` | Model to use | `llama3.1:8b`, `llama3.1:70b`, `mistral` |

### ⚙️ LLM Generation Settings

| Variable | Default | Description | Range |
|----------|---------|-------------|-------|
| `MAX_TOKENS` | `2000` | Maximum response tokens | `1000-4000` |
| `TEMPERATURE` | `0.1` | Response creativity | `0.0-1.0` |

### 📄 Document Processing

| Variable | Default | Description | Recommended |
|----------|---------|-------------|-------------|
| `CHUNK_SIZE` | `1000` | Text chunk size (words) | `800-1500` |
| `CHUNK_OVERLAP` | `200` | Chunk overlap (words) | `10-20% of chunk size` |
| `MAX_CONCURRENT_DOWNLOADS` | `5` | Concurrent downloads | `3-10` |

### 🔍 Search & Retrieval

| Variable | Default | Description | Range |
|----------|---------|-------------|-------|
| `MIN_SIMILARITY_THRESHOLD` | `0.05` | Minimum search similarity | `0.03-0.1` |
| `TFIDF_SEMANTIC_WEIGHT` | `0.4` | Semantic search weight | `0.0-1.0` |
| `TFIDF_KEYWORD_WEIGHT` | `0.6` | Keyword search weight | `0.0-1.0` |

### 🗄️ Database & Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_DB_PATH` | `./data/vector_db` | Vector database path |
| `CHROMA_PERSIST_DIRECTORY` | `./data/chroma_db` | ChromaDB storage |
| `EMBEDDINGS_DIR` | `./src/data/embeddings` | Embeddings storage |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |

### 🌐 Network & Requests

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUEST_TIMEOUT` | `120` | HTTP timeout (seconds) |
| `MAX_RETRIES` | `3` | Max retry attempts |
| `BACKOFF_MAX_TIME` | `120` | Max backoff time (seconds) |

### 🔧 System Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG_MODE` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_LOG_SIZE` | `100` | Max log file size (MB) |

## Configuration Examples

### Development Environment
```env
# Development setup - more verbose logging, local services
OLLAMA_URL=http://localhost:11434
MAX_CONCURRENT_DOWNLOADS=3
MIN_SIMILARITY_THRESHOLD=0.03
DEBUG_MODE=true
LOG_LEVEL=DEBUG
CHUNK_SIZE=800
TEMPERATURE=0.2
```

### Production Environment
```env
# Production setup - optimized for performance and stability
OLLAMA_URL=http://production-llm-server:11434
MAX_CONCURRENT_DOWNLOADS=10
MIN_SIMILARITY_THRESHOLD=0.1
DEBUG_MODE=false
LOG_LEVEL=INFO
CHUNK_SIZE=1200
TEMPERATURE=0.1
REQUEST_TIMEOUT=180
```

### High-Performance Setup
```env
# High-performance setup - larger model, bigger chunks
OLLAMA_MODEL=llama3.1:70b
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
MAX_TOKENS=4000
EMBEDDING_MODEL=all-mpnet-base-v2
MIN_SIMILARITY_THRESHOLD=0.08
```

### Resource-Constrained Setup
```env
# Lightweight setup - smaller model, smaller chunks
OLLAMA_MODEL=llama3.1:8b
CHUNK_SIZE=600
CHUNK_OVERLAP=100
MAX_TOKENS=1500
MAX_CONCURRENT_DOWNLOADS=2
REQUEST_TIMEOUT=60
```

## Tuning Guidelines

### 🎯 Search Quality Tuning

**For more precise results:**
```env
MIN_SIMILARITY_THRESHOLD=0.1
TFIDF_SEMANTIC_WEIGHT=0.7
TFIDF_KEYWORD_WEIGHT=0.3
```

**For broader coverage:**
```env
MIN_SIMILARITY_THRESHOLD=0.03
TFIDF_SEMANTIC_WEIGHT=0.4
TFIDF_KEYWORD_WEIGHT=0.6
```

### 🚀 Performance Tuning

**For faster processing:**
```env
CHUNK_SIZE=800
CHUNK_OVERLAP=100
MAX_TOKENS=1500
OLLAMA_MODEL=llama3.1:8b
```

**For better quality:**
```env
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
MAX_TOKENS=3000
OLLAMA_MODEL=llama3.1:70b
```

### 💾 Memory Optimization

**For limited memory:**
```env
CHUNK_SIZE=600
MAX_CONCURRENT_DOWNLOADS=2
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

**For high memory systems:**
```env
CHUNK_SIZE=2000
MAX_CONCURRENT_DOWNLOADS=15
EMBEDDING_MODEL=all-mpnet-base-v2
```

## Troubleshooting

### Common Issues

1. **"Connection refused" error:**
   - Check `OLLAMA_URL` is correct
   - Ensure Ollama server is running
   - Verify firewall settings

2. **"Model not found" error:**
   - Verify `OLLAMA_MODEL` is installed: `ollama list`
   - Pull the model: `ollama pull llama3.1:8b`

3. **"API key invalid" error:**
   - Check `SEC_API_KEY` is correct
   - Verify API key hasn't expired
   - Check API usage limits

4. **Slow performance:**
   - Reduce `CHUNK_SIZE` and `MAX_TOKENS`
   - Increase `MAX_CONCURRENT_DOWNLOADS`
   - Use faster model like `llama3.1:8b`

5. **Out of memory errors:**
   - Reduce `CHUNK_SIZE`
   - Lower `MAX_CONCURRENT_DOWNLOADS`
   - Use smaller embedding model

### Validation Commands

```bash
# Test Ollama connection
curl $OLLAMA_URL/api/tags

# Test SEC API key
curl -H "Authorization: $SEC_API_KEY" https://api.sec-api.io/

# Check disk space for data directories
du -sh ./src/data/

# Validate environment variables
python -c "from src.config.settings import *; print('Config loaded successfully')"
```

## Security Best Practices

1. **Never commit .env files to version control**
2. **Use different API keys for different environments**
3. **Regularly rotate API keys**
4. **Restrict file permissions on .env:**
   ```bash
   chmod 600 .env
   ```
5. **Use environment-specific .env files:**
   - `.env.development`
   - `.env.staging`
   - `.env.production`

## Environment Migration

### From Development to Production

1. **Copy and modify .env:**
   ```bash
   cp .env.development .env.production
   ```

2. **Update production-specific values:**
   - Change `OLLAMA_URL` to production server
   - Set `DEBUG_MODE=false`
   - Increase `REQUEST_TIMEOUT` for stability
   - Optimize `CHUNK_SIZE` for your data

3. **Test configuration:**
   ```bash
   python -c "from src.config.settings import *; print(f'Ollama: {OLLAMA_URL}, Debug: {DEBUG_MODE}')"
   ```

## Advanced Configuration

### Custom Embedding Models

```env
# For better semantic understanding (slower)
EMBEDDING_MODEL=all-mpnet-base-v2

# For multilingual support
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# For domain-specific embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Load Balancing Multiple Ollama Servers

```env
# Primary server
OLLAMA_URL=http://ollama-1:11434

# For high availability, implement round-robin in code
# OLLAMA_BACKUP_URLS=http://ollama-2:11434,http://ollama-3:11434
```

### Custom Data Paths for Different Environments

```env
# Development
RAW_DATA_DIR=./dev-data/raw
CHROMA_PERSIST_DIRECTORY=./dev-data/chroma

# Production
RAW_DATA_DIR=/var/lib/sec-qa/raw
CHROMA_PERSIST_DIRECTORY=/var/lib/sec-qa/chroma
```