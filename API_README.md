# SEC Cases API

A RESTful API for programmatically accessing all 11,772 SEC litigation cases.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
python api_server.py
```

The server will start on `http://localhost:5000` by default. You can change the port by setting the `PORT` environment variable:

```bash
PORT=8080 python api_server.py
```

### 3. Test the API

Visit `http://localhost:5000/` for API documentation, or use the example script:

```bash
python api_example.py
```

## API Endpoints

### `GET /api/metadata`

Get metadata about the dataset.

**Response:**
```json
{
  "scrapedAt": "2025-12-18T02:11:23.296Z",
  "totalCases": 11772,
  "source": "https://www.sec.gov/enforcement-litigation/litigation-releases"
}
```

### `GET /api/cases`

Get all cases with pagination and optional date filtering.

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 100, max: 1000) - Items per page
- `release_date_from` (string, optional) - Filter cases from this date (YYYY-MM-DD)
- `release_date_to` (string, optional) - Filter cases to this date (YYYY-MM-DD)

**Example:**
```bash
curl "http://localhost:5000/api/cases?page=1&per_page=100"
curl "http://localhost:5000/api/cases?release_date_from=2024-01-01&release_date_to=2024-12-31"
```

**Response:**
```json
{
  "total": 11772,
  "page": 1,
  "per_page": 100,
  "total_pages": 118,
  "cases": [...]
}
```

### `GET /api/cases/<release_number>`

Get a specific case by release number.

**Example:**
```bash
curl "http://localhost:5000/api/cases/LR-26445"
curl "http://localhost:5000/api/cases/26445"  # Works with or without LR- prefix
```

**Response:**
```json
{
  "releaseNumber": "LR-26445",
  "releaseDate": "2025-12-16",
  "title": "Artur Khachatryan",
  "url": "https://www.sec.gov/...",
  "features": {...},
  "supportingDocuments": [...]
}
```

### `GET /api/cases/search`

Search cases by various criteria.

**Query Parameters:**
- `q` (string, optional) - Text search in title and fullText
- `title` (string, optional) - Filter by title (partial match)
- `court` (string, optional) - Filter by court name
- `charges` (string, optional) - Filter by charges (partial match)
- `has_complaint` (boolean, optional) - Filter cases that have complaint PDFs
- `page` (int, default: 1) - Page number
- `per_page` (int, default: 100, max: 1000) - Items per page

**Examples:**
```bash
# Search for "fraud" in title or text
curl "http://localhost:5000/api/cases/search?q=fraud&page=1"

# Find cases with complaints
curl "http://localhost:5000/api/cases/search?has_complaint=true"

# Search by court
curl "http://localhost:5000/api/cases/search?court=California"

# Combine filters
curl "http://localhost:5000/api/cases/search?q=fraud&has_complaint=true&court=California"
```

### `GET /api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "total_cases": 11772,
  "metadata": {...}
}
```

## Programmatic Usage

### Python Example

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Get all cases (paginated)
response = requests.get(f"{BASE_URL}/cases", params={"page": 1, "per_page": 100})
data = response.json()
print(f"Total cases: {data['total']}")
print(f"Cases on this page: {len(data['cases'])}")

# Get a specific case
case = requests.get(f"{BASE_URL}/cases/LR-26445").json()
print(case['title'])

# Search cases
results = requests.get(
    f"{BASE_URL}/cases/search",
    params={"q": "fraud", "has_complaint": "true", "page": 1}
).json()
print(f"Found {results['total']} cases")
```

See `api_example.py` for more detailed examples.

### Download All Cases

To download all 11,772 cases to a JSON file:

```python
from api_example import download_all_cases

download_all_cases("all_cases.json")
```

Or use the example script:

```bash
python -c "from api_example import download_all_cases; download_all_cases('all_cases.json')"
```

## Case Data Structure

Each case contains:

```json
{
  "releaseNumber": "LR-26445",
  "releaseDate": "2025-12-16",
  "title": "Case Title",
  "url": "https://www.sec.gov/...",
  "features": {
    "summary": "...",
    "caseName": "...",
    "respondents": "...",
    "charges": "...",
    "court": "...",
    "fullText": "...",
    "originalSummary": "..."
  },
  "supportingDocuments": [
    {
      "title": "SEC Complaint",
      "url": "https://www.sec.gov/files/...",
      "type": "complaint"
    }
  ]
}
```

## Performance Notes

- Cases are loaded into memory on first request and cached for subsequent requests
- Maximum `per_page` is 1000 to prevent excessive memory usage
- For large downloads, use pagination to fetch all cases incrementally

## CORS

CORS is enabled by default, so you can call the API from web browsers or any origin.
