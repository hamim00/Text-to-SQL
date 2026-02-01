# 🔍 Text to SQL

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![LLM](https://img.shields.io/badge/LLM-Ollama%20%7C%20Groq-blue?style=for-the-badge)

**A safe, schema-aware natural language to SQL converter powered by LLMs**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Usage](#-usage) • [Deployment](#-deployment) • [Configuration](#-configuration) • [Architecture](#-architecture)

</div>

---

## 📸 Demo

<div align="center">
<img src="./assets/demo-screenshot.png" alt="Text to SQL Demo" width="800"/>
</div>

Transform natural language questions into safe, optimized SQL queries instantly.

---

## ✨ Features

### 🔒 Security First
- **SELECT-only queries** - Only read operations allowed, no data modification
- **SQL injection prevention** - Queries are parsed and validated using `sqlglot`
- **Automatic LIMIT injection** - Prevents runaway queries with auto-added LIMIT clauses
- **Rate limiting** - Configurable per-client rate limits to prevent abuse
- **Input length validation** - Guards against prompt injection attacks

### 🧠 Intelligent SQL Generation
- **Schema-aware prompting** - LLM receives actual database schema for accurate queries
- **Multi-provider support** - Works with both **Ollama** (local) and **Groq** (cloud)
- **SQL cleaning pipeline** - Extracts clean SQL from LLM responses (handles markdown, code blocks, etc.)
- **Dialect support** - Currently supports SQLite with extensible architecture

### 📊 Production Ready
- **Query history** - Full logging with execution time, row counts, and errors
- **CSV export** - Download query results as CSV files
- **Streaming mode** - Debug mode to watch SQL generation in real-time
- **Modern UI** - Clean, responsive Streamlit interface with dark theme

---

## 🏗️ Architecture

```
Text-to-SQL/
├── 📁 data/                    # Database files (auto-created)
│   ├── student.db              # Sample SQLite database
│   └── t2s_log.db              # Query history logs
│
├── 📁 scripts/                 # Utility scripts
│   └── seed_student_db.py      # Create sample database
│
├── 📁 t2s/                     # Core library
│   ├── 📁 db/                  # Database operations
│   │   ├── __init__.py
│   │   └── runner.py           # Query execution (read-only)
│   │
│   ├── 📁 logging/             # Query logging
│   │   ├── __init__.py
│   │   └── query_log.py        # History tracking
│   │
│   ├── 📁 providers/           # LLM integrations
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract provider interface
│   │   ├── factory.py          # Provider factory
│   │   ├── groq.py             # Groq API provider
│   │   └── ollama.py           # Ollama provider
│   │
│   ├── 📁 security/            # Security features
│   │   ├── __init__.py
│   │   └── rate_limit.py       # Sliding window rate limiter
│   │
│   ├── 📁 sql/                 # SQL processing
│   │   ├── __init__.py
│   │   ├── prompting.py        # LLM prompt templates
│   │   ├── safety.py           # SQL validation & rewriting
│   │   └── schema.py           # Schema extraction
│   │
│   ├── __init__.py
│   └── config.py               # Configuration management
│
├── 📁 tests/                   # Test suite
│   └── test_safety.py          # Safety module tests
│
├── 📁 ui/                      # Streamlit application
│   └── app.py                  # Main UI application
│
├── .env.example                # Environment template
├── .gitignore
├── requirements.txt            # Python dependencies
└── README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- One of:
  - [Ollama](https://ollama.ai/) installed locally (for local inference)
  - [Groq API key](https://console.groq.com/) (for cloud inference)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/hamim00/Text-to-SQL.git
   cd Text-to-SQL
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Seed the sample database**
   ```bash
   python scripts/seed_student_db.py
   ```

6. **Run the application**
   ```bash
   streamlit run ui/app.py
   ```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# ===========================================
# Provider Configuration
# ===========================================
# Options: "ollama" (local) or "groq" (cloud)
T2S_PROVIDER=groq

# ===========================================
# Database Configuration
# ===========================================
T2S_DB_PATH=./data/student.db
T2S_DB_DIALECT=sqlite
T2S_LOG_DB_PATH=./data/t2s_log.db
T2S_HISTORY_LIMIT=20

# ===========================================
# Guardrails
# ===========================================
T2S_MAX_OUTPUT_TOKENS=256
T2S_MAX_INPUT_CHARS=500
T2S_RATE_LIMIT_MAX_REQUESTS=15
T2S_RATE_LIMIT_WINDOW_SEC=60

# ===========================================
# Groq Configuration (if using Groq)
# ===========================================
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com

# ===========================================
# Ollama Configuration (if using Ollama)
# ===========================================
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `T2S_PROVIDER` | `ollama` | LLM provider (`ollama` or `groq`) |
| `T2S_DB_PATH` | `./data/student.db` | Path to SQLite database |
| `T2S_DB_DIALECT` | `sqlite` | SQL dialect for parsing |
| `T2S_MAX_OUTPUT_TOKENS` | `256` | Maximum tokens in LLM response |
| `T2S_MAX_INPUT_CHARS` | `500` | Maximum characters in user input |
| `T2S_RATE_LIMIT_MAX_REQUESTS` | `15` | Max requests per window |
| `T2S_RATE_LIMIT_WINDOW_SEC` | `60` | Rate limit window in seconds |

---

## 📖 Usage

### Basic Usage

1. **Start the application**
   ```bash
   streamlit run ui/app.py
   ```

2. **Ask questions in natural language**
   - "Show all students"
   - "Find students in class 10 with marks above 80"
   - "What is the average marks for each class?"
   - "List top 5 students by marks"

### Example Queries

| Natural Language | Generated SQL |
|------------------|---------------|
| "Show all students" | `SELECT * FROM STUDENT LIMIT 100;` |
| "Students in class 10" | `SELECT * FROM STUDENT WHERE CLASS = '10' LIMIT 100;` |
| "Average marks by class" | `SELECT CLASS, AVG(MARKS) FROM STUDENT GROUP BY CLASS LIMIT 100;` |
| "Top 3 students" | `SELECT * FROM STUDENT ORDER BY MARKS DESC LIMIT 3;` |

### Using with Your Own Database

1. Replace `./data/student.db` with your SQLite database
2. Update `T2S_DB_PATH` in `.env`
3. The schema is auto-detected and sent to the LLM

---

## 🌐 Deployment

### Deploy to Streamlit Cloud

Streamlit Cloud is the easiest way to deploy this application for free.

#### Step 1: Prepare Your Repository

1. **Fork or push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/Text-to-SQL.git
   git push -u origin main
   ```

2. **Create `requirements.txt`** (if not exists)
   ```txt
   streamlit>=1.28.0
   httpx>=0.25.0
   sqlglot>=19.0.0
   python-dotenv>=1.0.0
   ```

3. **Create `.streamlit/config.toml`** for theme settings:
   ```bash
   mkdir -p .streamlit
   ```
   
   Create `.streamlit/config.toml`:
   ```toml
   [theme]
   base = "dark"
   primaryColor = "#e94560"
   backgroundColor = "#0e1117"
   secondaryBackgroundColor = "#1a1a2e"
   textColor = "#ffffff"
   
   [server]
   headless = true
   port = 8501
   enableCORS = false
   ```

4. **Ensure database exists in repo**
   ```bash
   # Run seed script first
   python scripts/seed_student_db.py
   
   # Add database to git
   git add data/student.db
   git commit -m "Add sample database"
   git push
   ```

#### Step 2: Deploy on Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io/)**

2. **Click "New app"**

3. **Connect your GitHub repository**
   - Repository: `YOUR_USERNAME/Text-to-SQL`
   - Branch: `main`
   - Main file path: `ui/app.py`

4. **Configure Secrets** (⚙️ Advanced settings → Secrets)
   ```toml
   # Secrets for Streamlit Cloud
   T2S_PROVIDER = "groq"
   GROQ_API_KEY = "your_groq_api_key_here"
   GROQ_MODEL = "llama-3.3-70b-versatile"
   T2S_DB_PATH = "./data/student.db"
   T2S_DB_DIALECT = "sqlite"
   T2S_LOG_DB_PATH = "./data/t2s_log.db"
   T2S_MAX_OUTPUT_TOKENS = "256"
   T2S_MAX_INPUT_CHARS = "500"
   T2S_RATE_LIMIT_MAX_REQUESTS = "15"
   T2S_RATE_LIMIT_WINDOW_SEC = "60"
   ```

5. **Click "Deploy!"**

#### Step 3: Verify Deployment

1. Wait for the build to complete (usually 2-5 minutes)
2. Your app will be available at: `https://YOUR_APP_NAME.streamlit.app`

### Important Notes for Streamlit Cloud

⚠️ **Provider Limitation**: Streamlit Cloud cannot run Ollama (requires local installation). You **must use Groq** as the provider.

⚠️ **Database Persistence**: SQLite databases on Streamlit Cloud are ephemeral. For persistent data:
- Use a cloud database (PostgreSQL, MySQL)
- Or accept that query logs reset on each deployment

⚠️ **Secrets Management**: Never commit API keys. Always use Streamlit Secrets.

### Alternative Deployment Options

<details>
<summary><b>🐳 Docker Deployment</b></summary>

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed the database
RUN python scripts/seed_student_db.py

EXPOSE 8501

CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t text-to-sql .
docker run -p 8501:8501 --env-file .env text-to-sql
```
</details>

<details>
<summary><b>☁️ Railway Deployment</b></summary>

1. Connect your GitHub repo to [Railway](https://railway.app/)
2. Set environment variables in Railway dashboard
3. Railway auto-detects Streamlit and deploys
</details>

<details>
<summary><b>🔷 Heroku Deployment</b></summary>

Create `Procfile`:
```
web: streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0
```

Create `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml
```

Deploy:
```bash
heroku create your-app-name
heroku config:set GROQ_API_KEY=your_key
git push heroku main
```
</details>

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=t2s --cov-report=html

# Run specific test file
pytest tests/test_safety.py -v
```

### Test Coverage

The safety module includes tests for:
- SQL extraction from various LLM response formats
- Multi-statement detection and blocking
- Non-SELECT query blocking
- LIMIT injection
- Edge cases and malformed inputs

---

## 🔐 Security Features

### SQL Safety Pipeline

```
User Question
     ↓
LLM Generation
     ↓
┌─────────────────────────────┐
│   SQL Extraction            │  ← Handles markdown, code blocks
│   (extract_sql_candidate)   │
└─────────────────────────────┘
     ↓
┌─────────────────────────────┐
│   Multi-Statement Check     │  ← Blocks ; in middle
│                             │
└─────────────────────────────┘
     ↓
┌─────────────────────────────┐
│   Statement Type Check      │  ← Only SELECT allowed
│   (sqlglot parsing)         │
└─────────────────────────────┘
     ↓
┌─────────────────────────────┐
│   LIMIT Injection           │  ← Auto-add LIMIT 100
│                             │
└─────────────────────────────┘
     ↓
┌─────────────────────────────┐
│   Read-Only Execution       │  ← SQLite URI mode=ro
│                             │
└─────────────────────────────┘
     ↓
Safe Results
```

### Rate Limiting

Sliding window algorithm prevents abuse:
- Default: 15 requests per 60 seconds per client
- Tracks by IP address or session ID
- Configurable via environment variables

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Text-to-SQL.git
cd Text-to-SQL

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black isort

# Run tests
pytest tests/ -v

# Format code
black .
isort .
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Amazing framework for data apps
- [sqlglot](https://github.com/tobymao/sqlglot) - SQL parser and transpiler
- [Groq](https://groq.com/) - Fast LLM inference
- [Ollama](https://ollama.ai/) - Run LLMs locally

---

## 📬 Contact

**Mahmudul Hasan**

- GitHub: [@hamim00](https://github.com/hamim00)
- Project Link: [https://github.com/hamim00/Text-to-SQL](https://github.com/hamim00/Text-to-SQL)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

</div>