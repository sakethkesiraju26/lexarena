"""
Example script showing how to use the SEC Cases API programmatically.
"""

import requests
import json
from typing import Dict, List, Any


BASE_URL = "http://localhost:5000/api"


def get_metadata() -> Dict[str, Any]:
    """Get dataset metadata."""
    response = requests.get(f"{BASE_URL}/metadata")
    response.raise_for_status()
    return response.json()


def get_all_cases(page: int = 1, per_page: int = 100) -> Dict[str, Any]:
    """
    Get all cases with pagination.
    
    Args:
        page: Page number (default: 1)
        per_page: Items per page (default: 100, max: 1000)
    
    Returns:
        Dictionary with total, page info, and cases list
    """
    response = requests.get(
        f"{BASE_URL}/cases",
        params={"page": page, "per_page": per_page}
    )
    response.raise_for_status()
    return response.json()


def get_case_by_release_number(release_number: str) -> Dict[str, Any]:
    """
    Get a specific case by release number.
    
    Args:
        release_number: Case release number (e.g., "LR-26445" or "26445")
    
    Returns:
        Case dictionary
    """
    response = requests.get(f"{BASE_URL}/cases/{release_number}")
    response.raise_for_status()
    return response.json()


def search_cases(
    query: str = None,
    title: str = None,
    court: str = None,
    charges: str = None,
    has_complaint: bool = None,
    page: int = 1,
    per_page: int = 100
) -> Dict[str, Any]:
    """
    Search cases by various criteria.
    
    Args:
        query: Text search in title and fullText
        title: Filter by title (partial match)
        court: Filter by court name
        charges: Filter by charges (partial match)
        has_complaint: Filter cases that have complaint PDFs
        page: Page number
        per_page: Items per page
    
    Returns:
        Dictionary with total, page info, and filtered cases list
    """
    params = {"page": page, "per_page": per_page}
    
    if query:
        params["q"] = query
    if title:
        params["title"] = title
    if court:
        params["court"] = court
    if charges:
        params["charges"] = charges
    if has_complaint is not None:
        params["has_complaint"] = str(has_complaint).lower()
    
    response = requests.get(f"{BASE_URL}/cases/search", params=params)
    response.raise_for_status()
    return response.json()


def get_cases_by_date_range(
    date_from: str,
    date_to: str,
    page: int = 1,
    per_page: int = 100
) -> Dict[str, Any]:
    """
    Get cases within a date range.
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        page: Page number
        per_page: Items per page
    
    Returns:
        Dictionary with total, page info, and filtered cases list
    """
    response = requests.get(
        f"{BASE_URL}/cases",
        params={
            "release_date_from": date_from,
            "release_date_to": date_to,
            "page": page,
            "per_page": per_page
        }
    )
    response.raise_for_status()
    return response.json()


def download_all_cases(output_file: str = "all_cases.json"):
    """
    Download all cases and save to a JSON file.
    
    This will paginate through all cases and combine them.
    
    Args:
        output_file: Output file path
    """
    print("Fetching metadata...")
    metadata = get_metadata()
    total_cases = metadata.get("totalCases", 0)
    print(f"Total cases: {total_cases}")
    
    all_cases = []
    page = 1
    per_page = 1000  # Maximum per page
    
    while True:
        print(f"Fetching page {page}...")
        result = get_all_cases(page=page, per_page=per_page)
        cases = result.get("cases", [])
        
        if not cases:
            break
        
        all_cases.extend(cases)
        print(f"  Retrieved {len(cases)} cases (total: {len(all_cases)})")
        
        if len(all_cases) >= total_cases:
            break
        
        page += 1
    
    output_data = {
        "metadata": metadata,
        "cases": all_cases
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(all_cases)} cases to {output_file}")


if __name__ == "__main__":
    # Example usage
    
    print("=== SEC Cases API Examples ===\n")
    
    # 1. Get metadata
    print("1. Getting metadata...")
    metadata = get_metadata()
    print(f"   Total cases: {metadata.get('totalCases')}")
    print(f"   Scraped at: {metadata.get('scrapedAt')}\n")
    
    # 2. Get first page of cases
    print("2. Getting first 10 cases...")
    result = get_all_cases(page=1, per_page=10)
    print(f"   Total: {result['total']}")
    print(f"   Page: {result['page']}/{result['total_pages']}")
    print(f"   First case: {result['cases'][0]['title']}\n")
    
    # 3. Get a specific case
    print("3. Getting specific case (LR-26445)...")
    case = get_case_by_release_number("LR-26445")
    print(f"   Title: {case['title']}")
    print(f"   Release Date: {case['releaseDate']}\n")
    
    # 4. Search cases
    print("4. Searching for cases with 'fraud' in title...")
    search_result = search_cases(query="fraud", per_page=5)
    print(f"   Found {search_result['total']} cases")
    for case in search_result['cases'][:3]:
        print(f"   - {case['title']}")
    print()
    
    # 5. Get cases by date range
    print("5. Getting cases from 2024...")
    date_result = get_cases_by_date_range("2024-01-01", "2024-12-31", per_page=5)
    print(f"   Found {date_result['total']} cases in 2024")
    for case in date_result['cases'][:3]:
        print(f"   - {case['title']} ({case['releaseDate']})")
    print()
    
    # 6. Download all cases (commented out by default - uncomment to use)
    # print("6. Downloading all cases...")
    # download_all_cases("all_cases_download.json")
    # print()
