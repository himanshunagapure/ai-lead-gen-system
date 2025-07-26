# 🚀 Dynamic Travel Lead Generation Intelligence System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.41-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-Internal%20Use%20Only-orange.svg)](LICENSE)

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🎯 Project Overview

This is an **automated lead generation and business intelligence system** specifically designed for travel agencies to discover, qualify, and capture potential business partners and clients from across the internet in real-time.

### Primary Objective
Create an intelligent dynamic web scraping and analysis system that automatically discovers, evaluates, and delivers qualified people, travellers, companies, tour operators, travel bloggers, event organizers, and travel industry leads in real-time, similar to how ChatGPT or Claude can search and analyze web content, but specifically optimized for travel business intelligence.

## ✨ Key Features

### 🔍 **Intelligent Search & Discovery**
- **Multi-Source Search**: Google Search API integration with intelligent query building
- **Travel-Specific Queries**: Optimized search patterns for hotels, restaurants, tour operators
- **Geographic Targeting**: Location-based search with regional relevance scoring
- **Seasonal Intelligence**: Time-aware search patterns for travel industry trends

### 🕷️ **Multi-Tier Web Crawling**
- **Tier 1**: Fast HTTP crawling with httpx for basic content extraction
- **Tier 2**: Advanced Scrapy integration for complex site navigation
- **Tier 3**: Playwright browser automation for JavaScript-heavy sites
- **Robots.txt Compliance**: Respectful crawling with rate limiting and politeness

### 🤖 **AI-Powered Lead Extraction**
- **Google Gemini Integration**: Advanced AI analysis for lead identification
- **Pattern Recognition**: Regex-based extraction for emails, phones, business names
- **Structured Data Processing**: Schema.org and JSON-LD markup extraction
- **Content Classification**: Automatic categorization of travel businesses

### 📊 **Intelligent Lead Scoring**
- **Completeness Scoring**: Based on available contact information
- **Relevance Scoring**: Travel industry keyword matching
- **Freshness Scoring**: Content recency and activity indicators
- **Confidence Scoring**: AI-powered accuracy assessment

### 💾 **Comprehensive Data Management**
- **SQLite Database**: Local storage with SQLAlchemy ORM
- **File Storage**: Raw HTML and processed content archiving
- **Export Capabilities**: CSV, JSON, and Excel export formats
- **Data Normalization**: Standardized formats for all extracted data

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Search Client  │    │  Multi-Tier     │
│   (API Layer)   │◄──►│  (Google API)   │◄──►│  Crawler Engine │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Lead Storage   │    │ Lead Extractor  │    │ Content Manager │
│   (Database)    │◄──►│   (AI + Regex)  │◄──►│  (File System)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Lead Scorer    │    │  Background     │    │  Export System  │
│  (Intelligence) │◄──►│  Task Manager   │◄──►│  (CSV/JSON)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **API Layer** (`app/api/`)
- **FastAPI Application**: RESTful API endpoints
- **Request/Response Models**: Pydantic schemas for data validation
- **Authentication**: API key-based security
- **Background Tasks**: Async job processing

#### 2. **Core Engine** (`app/core/`)
- **Search Client**: Google Search API integration
- **Crawler Manager**: Multi-tier web crawling orchestration
- **Lead Extractor**: AI and pattern-based extraction
- **Lead Scorer**: Intelligent lead qualification
- **Content Manager**: File storage and processing

#### 3. **Data Layer** (`app/db/`, `app/models/`)
- **SQLAlchemy Models**: Database schema definition
- **Session Management**: Database connection handling
- **Migration System**: Alembic for schema evolution

#### 4. **Processing Pipeline**
- **Search → Crawl → Extract → Score → Store → Export**

## 🛠️ Technology Stack

### **Backend Framework**
- **FastAPI 0.116.1**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and settings management

### **Database & ORM**
- **SQLAlchemy 2.0.41**: Python SQL toolkit and ORM
- **Alembic 1.16.4**: Database migration tool
- **SQLite**: Lightweight, serverless database

### **Web Crawling & Scraping**
- **httpx 0.28.1**: Async HTTP client for fast crawling
- **Scrapy 2.13.3**: Advanced web crawling framework
- **Playwright 1.54.0**: Browser automation for JavaScript sites
- **BeautifulSoup4 4.13.4**: HTML parsing and extraction
- **lxml 6.0.0**: Fast XML/HTML processing
- **newspaper3k 0.2.8**: Article extraction and processing

### **AI & Machine Learning**
- **Google Generative AI 0.8.5**: Advanced AI content analysis
- **NLTK 3.9.1**: Natural language processing
- **FuzzyWuzzy 0.18.0**: Fuzzy string matching
- **python-Levenshtein 0.27.1**: String similarity algorithms

### **Data Processing**
- **Pandas 2.3.1**: Data manipulation and analysis
- **NumPy 2.2.6**: Numerical computing
- **Phonenumbers 9.0.10**: Phone number parsing and validation
- **Email Validator 2.2.0**: Email address validation

### **Search & APIs**
- **Google API Python Client 2.177.0**: Google Search API integration
- **Google Auth 2.40.3**: Authentication for Google services
- **Fake UserAgent 2.2.0**: User agent rotation for crawling

### **Utilities & Support**
- **python-dotenv 1.1.1**: Environment variable management
- **aiofiles 24.1.0**: Async file operations
- **python-multipart 0.0.20**: File upload support
- **Rich 14.0.0**: Rich text and beautiful formatting

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.10+**
- **Git**
- **Google API Key** (for search functionality)
- **Google Gemini API Key** (for AI analysis)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd lead-gen
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv leadgen-venv
leadgen-venv\Scripts\activate

# Linux/Mac
python3 -m venv leadgen-venv
source leadgen-venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=sqlite:///./leadgen.db

# Google API Configuration
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Crawling Configuration
MAX_CONCURRENT_REQUESTS=10
CRAWL_DELAY_SECONDS=1
MAX_PAGES_PER_DOMAIN=50

# System Configuration
LOG_LEVEL=INFO
```

### Step 5: Database Setup
```bash
# Initialize database
python setup_database.py

# Run migrations (if needed)
alembic upgrade head
```

### Step 6: Install Playwright Browsers
```bash
playwright install
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Database connection string | `sqlite:///./leadgen.db` | Yes |
| `GOOGLE_API_KEY` | Google Search API key | - | Yes |
| `GOOGLE_SEARCH_ENGINE_ID` | Google Custom Search Engine ID | - | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | - | Yes |
| `MAX_CONCURRENT_REQUESTS` | Maximum concurrent crawler requests | `10` | No |
| `CRAWL_DELAY_SECONDS` | Delay between requests | `1` | No |
| `MAX_PAGES_PER_DOMAIN` | Maximum pages per domain | `50` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### API Keys Setup

#### Google Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Custom Search API"
4. Create credentials (API Key)
5. Create a Custom Search Engine at [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Note the Search Engine ID

#### Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key for Gemini
3. Add to your `.env` file

## 📖 Usage

### Starting the Application

```bash
# Development mode
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### Running Comprehensive Tests

```bash
# Run the full integration test
python run_comprehensive_test.py
```

### Basic API Usage

#### 1. Submit a Search Job
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "luxury hotels Paris contact information",
    "max_results": 10
  }'
```

#### 2. Submit a Crawl Job
```bash
curl -X POST "http://localhost:8000/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "priority": 1
  }'
```

#### 3. Check Job Status
```bash
curl "http://localhost:8000/jobs/{job_id}"
```

#### 4. Export Leads
```bash
# JSON export
curl "http://localhost:8000/export"

# CSV export
curl "http://localhost:8000/export/csv" --output leads.csv
```

## 📚 API Documentation

### Core Endpoints

#### Search Management
- `POST /search` - Submit search job
- `GET /search/history` - Get search history
- `GET /search/{search_id}` - Get specific search results

#### Crawling Management
- `POST /crawl` - Submit crawl job
- `GET /crawl/status` - Get crawling statistics
- `GET /crawl/queue` - View crawl queue

#### Lead Management
- `GET /leads` - Get all leads
- `GET /leads/stats` - Get lead statistics
- `GET /leads/{lead_id}` - Get specific lead
- `POST /leads/process` - Process leads from content

#### Job Management
- `GET /jobs` - List all jobs
- `GET /jobs/{job_id}` - Get job status
- `DELETE /jobs/{job_id}` - Cancel job

#### Export & Data
- `GET /export` - Export leads as JSON
- `GET /export/csv` - Export leads as CSV
- `GET /status` - System status

### Request/Response Examples

#### Search Job Request
```json
{
  "query": "tour operators in India",
  "max_results": 20,
  "location": "India",
  "search_type": "business"
}
```

#### Crawl Job Request
```json
{
  "url": "https://example.com",
  "priority": 1,
  "max_depth": 2,
  "follow_links": true
}
```

#### Lead Export Response
```json
[
  {
    "id": 1,
    "business_name": "Example Hotel",
    "contact_person": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "address": "123 Main St, City, Country",
    "website": "https://example.com",
    "lead_type": "hotel",
    "confidence_score": 0.95,
    "created_at": "2024-01-01T12:00:00Z"
  }
]
```

## 🗄️ Database Schema

### Core Tables

#### `search_queries`
```sql
CREATE TABLE search_queries (
    id INTEGER PRIMARY KEY,
    query_text TEXT NOT NULL,
    search_engine VARCHAR(50) DEFAULT 'google',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    total_results_found INTEGER DEFAULT 0
);
```

#### `urls`
```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255),
    discovered_from VARCHAR(50),
    search_query_id INTEGER,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_crawled TIMESTAMP,
    crawl_status VARCHAR(20) DEFAULT 'pending',
    http_status_code INTEGER,
    content_type VARCHAR(100),
    content_length INTEGER,
    robots_allowed BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (search_query_id) REFERENCES search_queries(id)
);
```

#### `crawled_content`
```sql
CREATE TABLE crawled_content (
    id INTEGER PRIMARY KEY,
    url_id INTEGER,
    raw_html_path TEXT,
    title TEXT,
    meta_description TEXT,
    extracted_text TEXT,
    language VARCHAR(10),
    crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (url_id) REFERENCES urls(id)
);
```

#### `extracted_leads`
```sql
CREATE TABLE extracted_leads (
    id INTEGER PRIMARY KEY,
    content_id INTEGER,
    business_name VARCHAR(255),
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    website VARCHAR(255),
    lead_type VARCHAR(50),
    confidence_score FLOAT,
    extraction_method VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES crawled_content(id)
);
```

#### `lead_scores`
```sql
CREATE TABLE lead_scores (
    id INTEGER PRIMARY KEY,
    lead_id INTEGER,
    completeness_score FLOAT,
    relevance_score FLOAT,
    freshness_score FLOAT,
    final_score FLOAT,
    scoring_factors TEXT,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES extracted_leads(id)
);
```

## 🧪 Testing

### Running Tests

#### Comprehensive Integration Test
```bash
python run_comprehensive_test.py
```

This test:
- ✅ Tests database connection and setup
- ✅ Gets real URLs from Google search
- ✅ Tests crawling each URL
- ✅ Tests lead extraction and processing
- ✅ Tests database storage
- ✅ Tests CSV export
- ✅ Provides comprehensive results summary

#### Individual Component Tests
```bash
# Test database connection
python -c "from app.db.session import test_db_connection; test_db_connection()"

# Test search client
python -c "import asyncio; from app.core.search_client import GoogleSearchClient; asyncio.run(GoogleSearchClient().test_connection())"
```

### Test Coverage
- **Unit Tests**: Core utility functions and data models
- **Integration Tests**: End-to-end workflows
- **API Tests**: All endpoints and request/response validation
- **Database Tests**: CRUD operations and data integrity
- **Crawler Tests**: Multi-tier crawling functionality

## 🚀 Deployment

### Development Deployment
```bash
# Start development server
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment

#### Using Docker (Recommended)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN playwright install

EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Using Systemd (Linux)
```ini
[Unit]
Description=Lead Generation API
After=network.target

[Service]
Type=simple
User=leadgen
WorkingDirectory=/opt/lead-gen
Environment=PATH=/opt/lead-gen/venv/bin
ExecStart=/opt/lead-gen/venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment-Specific Configurations

#### Development
- SQLite database
- Debug logging
- Hot reload enabled
- Local file storage

#### Production
- PostgreSQL database (recommended)
- Structured logging
- Process management
- Cloud storage integration

## 🔧 Troubleshooting

### Common Issues

#### 1. Google API Errors
```
Error: Google API quota exceeded
Solution: Check API quotas in Google Cloud Console
```

#### 2. Database Connection Issues
```
Error: Database locked
Solution: Check for concurrent access, restart application
```

#### 3. Crawling Failures
```
Error: Connection timeout
Solution: Increase timeout settings, check network connectivity
```

#### 4. Memory Issues
```
Error: Out of memory during large crawls
Solution: Reduce MAX_CONCURRENT_REQUESTS, implement pagination
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_comprehensive_test.py
```

### Performance Monitoring
- Monitor crawl success rates
- Track API usage and quotas
- Measure lead extraction accuracy
- Monitor system resource usage

## 📊 Performance Metrics

### System Performance
- **Crawl Speed**: ~100-500 pages/hour (depending on site complexity)
- **Lead Extraction Rate**: ~60-80% accuracy
- **API Response Time**: <200ms for most endpoints
- **Database Performance**: Optimized with proper indexing

### Resource Usage
- **Memory**: ~100-500MB (depending on crawl size)
- **CPU**: Moderate usage during crawling
- **Disk**: ~1-10GB for large datasets
- **Network**: Respectful crawling with rate limiting

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the comprehensive test suite
6. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Write comprehensive tests

### Testing Guidelines
- All new features must have tests
- Maintain >80% code coverage
- Run integration tests before submitting

## 📄 License

This project is for **internal use and research purposes** only. Please contact the author for licensing details.

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the comprehensive test output
- Examine the logs in `data/logs/`
- Contact the development team

---

**Built with ❤️ for the travel industry**

*Last updated: January 2025* 