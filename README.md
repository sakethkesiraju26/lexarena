# LexArena

**A live benchmark for evaluating AI models on SEC enforcement case predictions.**

LexArena tests whether AI systems can correctly predict real SEC enforcement outcomes. Models are given complaint text and must forecast disgorgement amounts, injunctions, officer bars, and other remedial measures.

## 🎯 Overview

Legal prediction is a challenging domain requiring both factual extraction and probabilistic reasoning. LexArena provides:

- **Real cases** — 11,772 SEC enforcement actions with verified outcomes
- **Blind evaluation** — Models see only the original complaint, never the outcome
- **Standardized metrics** — 6 prediction targets with consistent scoring
- **Open leaderboard** — Compare models on the same benchmark
- **Human vs AI Challenge** — Test your own prediction skills against frontier models
- **API access** — Programmatic access to all cases via REST API

## 📊 Current Results

| Rank | Model | Overall | Disgorgement | Penalty | Injunction | Officer Bar |
|------|-------|---------|--------------|---------|------------|-------------|
| 🥇 | **GPT-5.2** | **66.4%** | 57.6% | 59.5% | 79.6% | 92.8% |
| 🥈 | GPT-4o | 64.9% | 53.0% | 52.1% | 78.8% | 89.2% |
| 🥉 | Gemini 2.5 Flash | 62.8% | 46.9% | 48.2% | 79.6% | 85.7% |
| 4 | Claude Opus 4 | 46.8% | 41.2% | 39.8% | 68.4% | 75.6% |

*Results based on 500 SEC enforcement cases evaluated January 2026.*

## 🔮 Prediction Metrics

Models predict 6 outcome metrics for each case:

| Metric | Description | Scoring |
|--------|-------------|---------|
| **Disgorgement** | Amount of ill-gotten gains defendant must return | ±10% tolerance |
| **Civil Penalty** | Fine amount imposed by the SEC | ±10% tolerance |
| **Prejudgment Interest** | Interest accrued on disgorgement | ±10% tolerance |
| **Injunction** | Court order barring future securities violations | Exact match |
| **Officer/Director Bar** | Ban from serving as executive of any public company | Exact match |
| **Resolution Type** | Whether case was settled or litigated | Exact match |

## 🏗️ How It Works

```
SEC Complaint PDF → Text Extraction → LLM Prediction → Compare to Ground Truth → Score
```

1. **Data Collection** — SEC litigation releases are scraped with complaint PDFs
2. **Synopsis Generation** — GPT-4o generates plain-English case summaries
3. **Prediction** — Models receive synopsis and predict 6 outcomes
4. **Scoring** — Predictions compared against actual SEC release outcomes

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Note**: The API server works without API keys for read-only access. API keys are only required for running evaluations.

Required environment variables (for evaluation):
```bash
export OPENAI_API_KEY=your_key_here
# Optional: for other providers
export ANTHROPIC_API_KEY=your_key_here
export GOOGLE_API_KEY=your_key_here
```

### Algolia Search Setup (Optional)

The cases search page (`cases.html`) supports Algolia InstantSearch for fast, typo-tolerant search. If Algolia is not configured, the page falls back to basic client-side search.

**To enable Algolia search:**

1. **Create an Algolia account** at [algolia.com](https://www.algolia.com) (free tier available)

2. **Get your credentials** from the Algolia dashboard:
   - Application ID
   - Search-Only API Key (safe for client-side use)
   - Write API Key (for indexing only, keep server-side)

3. **Index your cases data:**
   ```bash
   export ALGOLIA_APP_ID=your_app_id
   export ALGOLIA_WRITE_KEY=your_write_key
   python index_algolia.py
   ```

4. **Update cases.html** with your Algolia credentials:
   - Open `cases.html`
   - Find the `ALGOLIA_APP_ID` and `ALGOLIA_SEARCH_KEY` constants
   - Replace `'YOUR_ALGOLIA_APP_ID'` and `'YOUR_ALGOLIA_SEARCH_KEY'` with your actual credentials

**Benefits of Algolia:**
- Typo-tolerant search (finds "fraud" even if you type "fraud")
- Fast, instant search results
- Search across title, synopsis, charges, and court fields
- Relevance-based ranking
- Search highlighting in results

**Note:** The Search-Only API Key is safe to expose in client-side code. Never commit the Write API Key to your repository.

### Run Evaluation

```bash
# Evaluate GPT-4o on all cases
python run_evaluation.py --evaluate --provider openai --model gpt-4o

# Limit to first 50 cases
python run_evaluation.py --evaluate --max-eval-cases 50 --save-results
```

### Generate Synopses

```bash
# Generate case summaries for all cases
python generate_synopses.py

# Limit to specific number
python generate_synopses.py --limit 100
```

### Start API Server

Access all 11,772 cases programmatically:

```bash
# Start the API server
python api_server.py

# Server runs on http://localhost:5000 by default
# Change port with: PORT=8080 python api_server.py
```

**Note**: The API server requires `litigation-cases.json` (117MB) to be present locally. This file is excluded from the repository due to GitHub's file size limits. See [DATA_FILES.md](DATA_FILES.md) for information on obtaining data files.

Visit `http://localhost:5000/` for interactive API documentation, or see the [Methodology & API page](methodology.html) for complete documentation with examples.

**Quick API Example:**
```python
import requests

# Get all cases (paginated)
response = requests.get("http://localhost:5000/api/cases", params={"page": 1, "per_page": 100})
data = response.json()
print(f"Total cases: {data['total']}")

# Get specific case
case = requests.get("http://localhost:5000/api/cases/LR-26445").json()

# Search cases
results = requests.get(
    "http://localhost:5000/api/cases/search",
    params={"q": "fraud", "has_complaint": "true"}
).json()
```

See `api_example.py` for more detailed examples.

### Update Website

```bash
# Generate updated HTML with latest evaluation results
python generate_viewer.py
```

## 🧠 Human vs AI Challenge

Test your legal prediction skills against frontier AI models:

1. **Read real SEC cases** — See the allegations and charges before the outcome is known
2. **Make predictions** — Estimate disgorgement amount, injunction likelihood, and officer bar
3. **Compare results** — See how your accuracy stacks up against GPT-5.2, Claude, and community averages

The challenge uses resolved cases to provide immediate feedback while simulating the blind prediction experience.

## 🌐 Website Features

The LexArena website includes:

- **Interactive Leaderboard** — Real-time model rankings with detailed metrics
- **Human Prediction Challenge** — Make your own predictions on 5 real cases
- **Case Browser** — Search and filter 500+ evaluated cases with:
  - Side-by-side comparison of GPT-5.2, GPT-4o, Claude, and Gemini predictions
  - Ground Truth displayed first for easy comparison
  - Expandable case details with synopsis and source links
  - Model-specific accuracy metrics
- **Methodology & API** — Combined documentation page with:
  - Evaluation methodology and metrics
  - Complete API documentation with examples
  - Quick start guide for developers
- **Mobile Responsive** — Full functionality on all device sizes

## 📁 Project Structure

```
newlex/
├── index.html              # Landing page with leaderboard and methodology overview
├── cases.html              # All cases viewer with search, model comparison table, and detailed predictions
├── methodology.html        # Methodology and API documentation (combined page)
├── api_server.py           # REST API server for programmatic access to all 11,772 cases
├── api_example.py          # Example script demonstrating API usage
├── run_evaluation.py       # Main evaluation script
├── generate_synopses.py    # GPT-4o synopsis generation
├── generate_viewer.py      # HTML generation from results
├── litigation-cases.json   # Full dataset: 11,772 SEC cases
├── sec-cases.json          # Filtered cases with complaints (4,155 cases)
├── data/
│   └── processed/
│       ├── evaluation_results_openai.json      # GPT-4o results
│       ├── evaluation_results_gpt52.json       # GPT-5.2 results (latest)
│       ├── evaluation_results_anthropic.json   # Claude Opus 4 results
│       ├── evaluation_results_google.json      # Gemini 2.5 Flash results
│       ├── combined_results.json               # All models combined
│       └── evaluation_dataset.json             # 500 evaluation cases
└── src/
    ├── evaluation/
    │   ├── llm_prompt_formatter.py
    │   ├── llm_runner.py
    │   └── score_calculator.py
    └── preprocessing/
        ├── dataset_builder.py
        ├── ground_truth_extractor.py
        ├── pdf_extractor.py
        └── synopsis_generator.py
```

## 📊 Data Access

LexArena provides two ways to access the case data:

### 1. Web Interface
- **Leaderboard** (`index.html`) — View model performance rankings with interactive tooltips
- **Cases Page** (`cases.html`) — Browse and search all cases with:
  - Side-by-side model comparison table (GPT, Claude, Gemini vs Ground Truth)
  - Expandable case details with synopsis and PDF/SEC links
  - Model selection and filtering
- **Methodology** (`methodology.html`) — Learn about evaluation process and API access

### 2. API Access
- **REST API** — Programmatic access to all 11,772 cases via `api_server.py`
- **Filtering & Search** — Filter by date, court, charges, complaint availability
- **Pagination** — Efficient access to large datasets (up to 1000 cases per page)
- **Complete Documentation** — See [Methodology & API](methodology.html) for detailed endpoint documentation, examples, and usage

### Dataset Files

**Note**: Large data files are excluded from this repository due to GitHub's file size limits (100MB hard limit). See [DATA_FILES.md](DATA_FILES.md) for details on obtaining these files.

- `litigation-cases.json` — Complete dataset with 11,772 cases (117MB - excluded)
- `sec-cases.json` — Filtered to cases with complaint PDFs (4,155 cases, 46MB - excluded)
- Processed datasets in `data/processed/` for evaluation (included in repository)

## 🔌 API Endpoints

The API provides the following endpoints:

- `GET /api/metadata` — Get dataset metadata
- `GET /api/cases` — Get all cases with pagination and date filtering
- `GET /api/cases/<release_number>` — Get a specific case by release number
- `GET /api/cases/search` — Search cases by text, court, charges, etc.
- `GET /api/health` — Health check endpoint

All endpoints support CORS and return JSON responses. See `methodology.html` for detailed documentation and examples.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick start:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Submit a pull request

For adding a new model:
1. Add provider support in `src/evaluation/llm_runner.py`
2. Run evaluation: `python run_evaluation.py --evaluate --provider your_provider`
3. Submit a PR with results

## 🔒 Security

**Critical:** Never commit API keys, secrets, or credentials to the repository. Always use environment variables for sensitive configuration.

### Pre-Open Source Security Checklist

Security audit completed (January 2026):

- [x] **Audited Git History**: Scanned for accidentally committed secrets using tools like `git-secrets`, `truffleHog`, or `gitleaks`
- [x] **Verified .gitignore Coverage**: Confirmed all sensitive files and patterns are excluded
- [x] **Rotated Exposed Keys**: If any API keys were ever committed (even if later removed), rotate them immediately
- [x] **Reviewed Error Messages**: Ensured error messages don't leak sensitive information (file paths sanitized in `api_server.py`)
- [x] **Scanned Dependencies**: Checked for known vulnerabilities using `pip-audit` or `safety check`
- [x] **Reviewed Log Files**: Verified log files don't contain API keys or sensitive data (excluded via `.gitignore`)
- [x] **Documented Security Considerations**: Updated this security section with relevant information

### API Key Management

#### Best Practices

- **Always Use Environment Variables**: All API keys must be set via environment variables, never hardcoded in code or configuration files
- **Never Commit Secrets**: The `.gitignore` file excludes `.env` and other sensitive files - never override this
- **Rotate Exposed Keys Immediately**: If you accidentally commit an API key (even if removed later), rotate it in the provider's dashboard immediately
- **Use Separate Keys for Development/Production**: Use different API keys for local development vs. production deployments
- **Limit Key Permissions**: Create API keys with minimum required permissions/scopes

#### Required Environment Variables

```bash
export OPENAI_API_KEY=your_key_here           # Required for OpenAI evaluations
export ANTHROPIC_API_KEY=your_key_here        # Optional: for Anthropic evaluations
export GOOGLE_API_KEY=your_key_here           # Optional: for Google/Gemini evaluations
export REDUCTO_API_KEY=your_key_here          # Optional: for PDF extraction via Reducto
export PORT=5000                               # Optional: API server port (default: 5000)
```

#### Setting Up Environment Variables

**Option 1: Export in your shell session**
```bash
export OPENAI_API_KEY=your_key_here
python run_evaluation.py --evaluate
```

**Option 2: Use a `.env` file (recommended for local development)**
```bash
# Create .env file (already in .gitignore)
echo "OPENAI_API_KEY=your_key_here" > .env

# Load and run (requires python-dotenv or similar)
python -c "from dotenv import load_dotenv; load_dotenv()" && python run_evaluation.py --evaluate
```

**Option 3: Inline for single commands**
```bash
OPENAI_API_KEY=your_key_here python run_evaluation.py --evaluate
```

### Git History Security Audit

Before open-sourcing, scan your git history for secrets:

```bash
# Using git-secrets (install via: brew install git-secrets or apt-get install git-secrets)
git secrets --scan-history

# Using truffleHog (install via: pip install truffleHog)
trufflehog --regex --entropy=False --repo .

# Using gitleaks (install from: https://github.com/gitleaks/gitleaks)
gitleaks detect --source . --verbose
```

If secrets are found in history, you have two options:
1. **Rotate the keys** (recommended if keys are old or you're unsure)
2. **Rewrite git history** using `git filter-branch` or BFG Repo-Cleaner (complex, use with caution)

### Dependency Security

**Last audit**: January 2026

Regularly audit dependencies for known vulnerabilities:

```bash
# Using pip-audit (recommended)
pip install pip-audit
pip-audit -r requirements.txt

# Using safety (alternative)
pip install safety
safety check -r requirements.txt
```

**Current status**: 
- All direct dependencies are up-to-date
- One transitive dependency (`pdfminer-six`) has a known vulnerability (GHSA-f83h-ghpp-7wcc)
  - This is a dependency of `pdfplumber` and will be updated when `pdfplumber` releases a new version
  - The vulnerability is low-risk for this use case (PDF parsing only, no user input)
  - Monitor for updates: `pip-audit -r requirements.txt`

Keep dependencies updated and review security advisories for packages you use.

### API Server Security

The API server (`api_server.py`) is configured for local development and should be hardened for production:

#### Current Configuration
- **Host**: `0.0.0.0` (binds to all interfaces - appropriate for containers)
- **Debug Mode**: Disabled (`debug=False`)
- **CORS**: Enabled for all origins (for development convenience)

#### Production Deployment Considerations

For production deployments, consider:

- **CORS Restrictions**: Restrict CORS to specific allowed origins:
  ```python
  from flask_cors import CORS
  CORS(app, origins=["https://yourdomain.com"])
  ```

- **Rate Limiting**: Implement rate limiting to prevent abuse (e.g., using `flask-limiter`)
- **HTTPS**: Always use HTTPS in production (use a reverse proxy like nginx or Caddy)
- **Security Headers**: Add security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- **Input Validation**: The API already validates input, but consider additional sanitization for production
- **Authentication**: Consider adding API key authentication for production use
- **Resource Limits**: Set appropriate limits on request size and pagination

#### Local Development

The default configuration is suitable for local development:
- CORS is open to allow testing from different origins
- Debug mode is disabled to prevent information leakage
- Server binds to all interfaces for container compatibility

### Secure Coding Practices

- **Error Handling**: Error messages are generic and don't leak sensitive information (file paths, stack traces, etc.) ✅
- **No Hardcoded Credentials**: All credentials use environment variables ✅
- **Input Validation**: API endpoints validate and sanitize input parameters ✅
- **Logging**: Log files are excluded from git (`.gitignore` includes `*.log`) ✅
- **File Path Sanitization**: All error handlers in `api_server.py` use generic messages to prevent path disclosure ✅

### Reporting Security Issues

If you discover a security vulnerability, please report it responsibly:
1. **Do not** open a public GitHub issue
2. Contact the maintainers privately
3. Allow time for the issue to be addressed before public disclosure

### Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Common security risks
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security.html)
- [Git Secrets Management](https://git-secret.io/)
- [Flask Security Checklist](https://flask.palletsprojects.com/en/latest/security/)

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Built by [Saketh Kesiraju](https://github.com/sakethkesiraju26)**
