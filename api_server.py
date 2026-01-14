"""
API server for accessing SEC litigation cases programmatically.

Endpoints:
- GET /api/cases - Get all cases (with pagination)
- GET /api/cases/<release_number> - Get a specific case by release number
- GET /api/cases/search - Search cases by query parameters
- GET /api/metadata - Get dataset metadata

Security Considerations:
- CORS is enabled for all origins (suitable for development)
  For production, restrict CORS to specific domains
- Debug mode is disabled to prevent information leakage
- Error messages are generic and don't expose sensitive information
- Input validation is performed on all query parameters
- For production deployments, consider adding:
  - Rate limiting
  - API key authentication
  - HTTPS (via reverse proxy)
  - Security headers
  - Restricted CORS origins
"""

import json
import os
import re
from flask import Flask, jsonify, request
from flask_cors import CORS
from typing import Dict, List, Any, Optional, Tuple

app = Flask(__name__)
# CORS enabled for all origins (development configuration)
# For production: CORS(app, origins=["https://yourdomain.com"])
CORS(app)  # Enable CORS for all routes

# Global variable to cache cases
_cases_cache: Optional[List[Dict[str, Any]]] = None
_metadata_cache: Optional[Dict[str, Any]] = None


@app.after_request
def after_request(response):
    """Add headers to all responses."""
    response.headers['Content-Type'] = 'application/json'
    return response


def load_cases() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load cases from litigation-cases.json file."""
    global _cases_cache, _metadata_cache
    
    if _cases_cache is not None and _metadata_cache is not None:
        return _cases_cache, _metadata_cache
    
    file_path = os.path.join(os.path.dirname(__file__), 'litigation-cases.json')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError("Cases file not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    _metadata_cache = data.get('metadata', {})
    _cases_cache = data.get('cases', [])
    
    return _cases_cache, _metadata_cache


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)."""
    if not date_str:
        return False
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
    try:
        year, month, day = map(int, date_str.split('-'))
        # Basic validation
        if month < 1 or month > 12 or day < 1 or day > 31:
            return False
        return True
    except ValueError:
        return False


def validate_pagination(page: str, per_page: str) -> Tuple[bool, Optional[str], int, int]:
    """
    Validate pagination parameters.
    Returns: (is_valid, error_message, page_int, per_page_int)
    """
    try:
        page_int = int(page) if page else 1
        per_page_int = int(per_page) if per_page else 100
    except ValueError:
        return False, "Pagination parameters must be integers", 1, 100
    
    if page_int < 1:
        return False, "Page number must be greater than 0", 1, 100
    
    if per_page_int < 1:
        return False, "per_page must be greater than 0", 1, 100
    
    if per_page_int > 1000:
        return False, "per_page cannot exceed 1000", 1, 1000
    
    return True, None, page_int, per_page_int


@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Get metadata about the dataset."""
    try:
        _, metadata = load_cases()
        return jsonify(metadata)
    except FileNotFoundError:
        return jsonify({'error': 'Cases file not found'}), 404
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/cases', methods=['GET'])
def get_cases():
    """
    Get all cases with optional pagination.
    
    Query parameters:
    - page: Page number (default: 1, must be > 0)
    - per_page: Items per page (default: 100, max: 1000, must be > 0)
    - release_date_from: Filter cases from this date (YYYY-MM-DD)
    - release_date_to: Filter cases to this date (YYYY-MM-DD)
    """
    try:
        cases, _ = load_cases()
        
        # Validate pagination
        page_str = request.args.get('page', '1')
        per_page_str = request.args.get('per_page', '100')
        is_valid, error_msg, page, per_page = validate_pagination(page_str, per_page_str)
        
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Validate and apply date filters
        date_from = request.args.get('release_date_from')
        date_to = request.args.get('release_date_to')
        
        if date_from and not validate_date(date_from):
            return jsonify({
                'error': 'Invalid date format for release_date_from',
                'expected_format': 'YYYY-MM-DD',
                'received': date_from
            }), 400
        
        if date_to and not validate_date(date_to):
            return jsonify({
                'error': 'Invalid date format for release_date_to',
                'expected_format': 'YYYY-MM-DD',
                'received': date_to
            }), 400
        
        if date_from or date_to:
            filtered_cases = []
            for case in cases:
                release_date = case.get('releaseDate', '')
                if date_from and release_date < date_from:
                    continue
                if date_to and release_date > date_to:
                    continue
                filtered_cases.append(case)
            cases = filtered_cases
        
        # Pagination
        total = len(cases)
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_cases = cases[start:end]
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 0,
            'cases': paginated_cases
        })
    except FileNotFoundError:
        return jsonify({'error': 'Cases file not found'}), 404
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/cases/<release_number>', methods=['GET'])
def get_case(release_number: str):
    """Get a specific case by release number (e.g., LR-26445 or 26445)."""
    try:
        cases, _ = load_cases()
        
        # Normalize release number (handle with or without LR- prefix)
        normalized = release_number.upper().strip()
        if not normalized.startswith('LR-'):
            normalized = f'LR-{normalized}'
        
        for case in cases:
            if case.get('releaseNumber', '').upper() == normalized:
                return jsonify(case)
        
        return jsonify({
            'error': 'Case not found',
            'release_number': release_number,
            'suggestion': 'Check the release number format (e.g., LR-26445 or 26445)'
        }), 404
    except FileNotFoundError:
        return jsonify({'error': 'Cases file not found'}), 404
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/cases/search', methods=['GET'])
def search_cases():
    """
    Search cases by various criteria.
    
    Query parameters:
    - q: Text search in title and fullText
    - title: Exact or partial match in title
    - court: Filter by court name
    - charges: Filter by charges (partial match)
    - has_complaint: Filter cases that have complaint PDFs (true/false)
    - page: Page number (default: 1, must be > 0)
    - per_page: Items per page (default: 100, max: 1000, must be > 0)
    """
    try:
        cases, _ = load_cases()
        
        # Validate pagination
        page_str = request.args.get('page', '1')
        per_page_str = request.args.get('per_page', '100')
        is_valid, error_msg, page, per_page = validate_pagination(page_str, per_page_str)
        
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        # Text search
        query = request.args.get('q', '').lower().strip()
        title_filter = request.args.get('title', '').lower().strip()
        court_filter = request.args.get('court', '').lower().strip()
        charges_filter = request.args.get('charges', '').lower().strip()
        has_complaint = request.args.get('has_complaint')
        
        # Validate has_complaint parameter
        if has_complaint is not None:
            has_complaint_lower = has_complaint.lower().strip()
            if has_complaint_lower not in ('true', 'false'):
                return jsonify({
                    'error': 'Invalid value for has_complaint',
                    'expected': 'true or false',
                    'received': has_complaint
                }), 400
        
        filtered_cases = []
        
        for case in cases:
            # Text search in title and fullText
            if query:
                title = case.get('title', '').lower()
                full_text = case.get('features', {}).get('fullText', '').lower()
                if query not in title and query not in full_text:
                    continue
            
            # Title filter
            if title_filter:
                if title_filter not in case.get('title', '').lower():
                    continue
            
            # Court filter
            if court_filter:
                court = case.get('features', {}).get('court', '').lower()
                if court_filter not in court:
                    continue
            
            # Charges filter
            if charges_filter:
                charges = case.get('features', {}).get('charges', '').lower()
                if charges_filter not in charges:
                    continue
            
            # Complaint filter
            if has_complaint is not None:
                has_complaint_bool = has_complaint.lower().strip() == 'true'
                supporting_docs = case.get('supportingDocuments', [])
                has_complaint_doc = any(
                    doc.get('type') == 'complaint' 
                    for doc in supporting_docs
                )
                if has_complaint_bool != has_complaint_doc:
                    continue
            
            filtered_cases.append(case)
        
        # Pagination
        total = len(filtered_cases)
        start = (page - 1) * per_page
        end = start + per_page
        
        paginated_cases = filtered_cases[start:end]
        
        return jsonify({
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 0,
            'cases': paginated_cases
        })
    except FileNotFoundError:
        return jsonify({'error': 'Cases file not found'}), 404
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        cases, metadata = load_cases()
        return jsonify({
            'status': 'healthy',
            'total_cases': len(cases),
            'metadata': metadata,
            'cache_loaded': _cases_cache is not None
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'error',
            'error': 'Cases file not found'
        }), 404
    except Exception:
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500


@app.route('/', methods=['GET'])
def root():
    """API documentation endpoint."""
    return jsonify({
        'name': 'SEC Litigation Cases API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/metadata': 'Get dataset metadata',
            'GET /api/cases': 'Get all cases (with pagination and date filters)',
            'GET /api/cases/<release_number>': 'Get a specific case by release number',
            'GET /api/cases/search': 'Search cases by various criteria',
            'GET /api/health': 'Health check endpoint'
        },
        'examples': {
            'get_all_cases': '/api/cases?page=1&per_page=100',
            'get_case': '/api/cases/LR-26445',
            'search': '/api/cases/search?q=fraud&has_complaint=true&page=1',
            'date_range': '/api/cases?release_date_from=2024-01-01&release_date_to=2024-12-31'
        }
    })


if __name__ == '__main__':
    # Load cases on startup to verify file exists
    try:
        load_cases()
        print("✓ Cases loaded successfully")
    except FileNotFoundError:
        print("✗ Error: Cases file not found")
        exit(1)
    except Exception:
        print("✗ Error: Failed to load cases")
        exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting API server on port {port}...")
    print(f"API documentation: http://localhost:{port}/")
    app.run(host='0.0.0.0', port=port, debug=False)
