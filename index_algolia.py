#!/usr/bin/env python3
"""
Index SEC cases data to Algolia for fast, typo-tolerant search.

This script:
1. Loads combined_results.json with all model predictions
2. Transforms data into Algolia records
3. Indexes records to Algolia

Usage:
    export ALGOLIA_APP_ID=your_app_id
    export ALGOLIA_WRITE_KEY=your_write_key
    python index_algolia.py
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from algoliasearch.search.client import SearchClientSync


def calculate_accuracy(comparison: Dict[str, Any]) -> Optional[float]:
    """Calculate accuracy percentage from comparison results."""
    if not comparison:
        return None
    
    fields = [
        comparison.get('resolution_type_correct'),
        comparison.get('disgorgement_correct'),
        comparison.get('penalty_correct'),
        comparison.get('interest_correct'),
        comparison.get('injunction_correct'),
        comparison.get('officer_bar_correct'),
    ]
    
    correct = sum(1 for f in fields if f is True)
    total = sum(1 for f in fields if f is not None)
    
    if total == 0:
        return None
    
    return round((correct / total) * 100, 1)


def get_prediction_for_provider(case_id: str, provider: str, all_providers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get prediction for a specific provider from all_providers dict."""
    provider_map = {'gpt': 'openai', 'claude': 'anthropic', 'gemini': 'google'}
    provider_key = provider_map.get(provider, provider)
    
    # Find the results for this provider in all_providers
    provider_data = all_providers.get(provider_key)
    if provider_data and 'predictions' in provider_data:
        for pred in provider_data['predictions']:
            if pred.get('case_id') == case_id and pred.get('success'):
                return pred
    return None


def transform_to_algolia_record(
    pred: Dict[str, Any],
    all_providers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Transform a prediction record into an Algolia record.
    
    Args:
        pred: Prediction record from combined_results.json
        all_providers: All providers data to look up other model predictions
        
    Returns:
        Algolia record dictionary
    """
    meta = pred.get('metadata', {})
    ground_truth = pred.get('ground_truth', {})
    comparison = pred.get('comparison', {})
    
    # Calculate accuracies for each model
    gpt_pred = get_prediction_for_provider(pred['case_id'], 'gpt', all_providers)
    claude_pred = get_prediction_for_provider(pred['case_id'], 'claude', all_providers)
    gemini_pred = get_prediction_for_provider(pred['case_id'], 'gemini', all_providers)
    
    accuracy_gpt = calculate_accuracy(gpt_pred.get('comparison', {})) if gpt_pred else None
    accuracy_claude = calculate_accuracy(claude_pred.get('comparison', {})) if claude_pred else None
    accuracy_gemini = calculate_accuracy(gemini_pred.get('comparison', {})) if gemini_pred else None
    
    # Get synopsis
    synopsis = ''
    if meta.get('reducto_fields', {}).get('case_synopsis'):
        synopsis = meta['reducto_fields']['case_synopsis']
    elif meta.get('summary'):
        synopsis = meta['summary']
    
    # Build Algolia record
    record = {
        'objectID': pred['case_id'],
        'case_id': pred['case_id'],
        'title': meta.get('title', ''),
        'synopsis': synopsis,
        'charges': meta.get('charges', ''),
        'court': meta.get('court', ''),
        'release_date': meta.get('release_date', ''),
        'resolution_type': ground_truth.get('resolution_type', 'unknown'),
        'accuracy_gpt': accuracy_gpt,
        'accuracy_claude': accuracy_claude,
        'accuracy_gemini': accuracy_gemini,
        'has_complaint': bool(meta.get('complaint_url')),
        'complaint_url': meta.get('complaint_url', ''),
        'case_url': meta.get('case_url', ''),
    }
    
    # Add accuracy range for faceting
    max_accuracy = max([a for a in [accuracy_gpt, accuracy_claude, accuracy_gemini] if a is not None] or [0])
    if max_accuracy >= 80:
        record['accuracy_range'] = 'high'
    elif max_accuracy >= 50:
        record['accuracy_range'] = 'medium'
    else:
        record['accuracy_range'] = 'low'
    
    return record


def load_combined_results(file_path: str = 'data/processed/combined_results.json') -> Dict[str, Any]:
    """Load combined results from JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Combined results file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def index_to_algolia(
    records: List[Dict[str, Any]],
    app_id: str,
    write_key: str,
    index_name: str = 'cases'
) -> None:
    """Index records to Algolia."""
    client = SearchClientSync(app_id, write_key)
    
    print(f"Indexing {len(records)} cases to Algolia index '{index_name}'...")
    
    # Save all records
    response = client.save_objects(
        index_name=index_name,
        objects=records,
    )
    
    print(f"✓ Successfully indexed {len(records)} cases")
    
    # Configure index settings
    print("Configuring index settings...")
    
    client.set_settings(index_name, {
        'searchableAttributes': [
            'title',
            'case_id',
            'synopsis',
            'charges',
            'court',
        ],
        'attributesForFaceting': [
            'resolution_type',
            'accuracy_range',
            'has_complaint',
            'searchable(court)',
        ],
        'customRanking': [
            'desc(accuracy_gpt)',
            'desc(accuracy_claude)',
            'desc(accuracy_gemini)',
        ],
        'typoTolerance': True,
        'highlightPreTag': '<mark>',
        'highlightPostTag': '</mark>',
    })
    
    print("✓ Index settings configured")


def main():
    """Main function to index cases to Algolia."""
    # Get Algolia credentials from environment
    app_id = os.environ.get('ALGOLIA_APP_ID')
    write_key = os.environ.get('ALGOLIA_WRITE_KEY')
    
    if not app_id or not write_key:
        print("Error: Algolia credentials not found in environment variables")
        print("Please set:")
        print("  export ALGOLIA_APP_ID=your_app_id")
        print("  export ALGOLIA_WRITE_KEY=your_write_key")
        sys.exit(1)
    
    # Load combined results
    print("Loading combined results...")
    try:
        all_results = load_combined_results()
    except Exception as e:
        print(f"Error loading combined results: {e}")
        sys.exit(1)
    
    # Get predictions from the main predictions array
    predictions = all_results.get('predictions', [])
    all_providers = all_results.get('all_providers', {})
    
    # Find all unique case IDs
    all_case_ids = set()
    for pred in predictions:
        if pred.get('success'):
            all_case_ids.add(pred['case_id'])
    
    print(f"Found {len(all_case_ids)} unique cases")
    
    # Transform to Algolia records
    print("Transforming data to Algolia records...")
    records = []
    for case_id in sorted(all_case_ids):
        # Find the prediction for this case (use first successful one from main predictions)
        pred = None
        for p in predictions:
            if p.get('case_id') == case_id and p.get('success'):
                pred = p
                break
        
        if pred:
            record = transform_to_algolia_record(pred, all_providers)
            records.append(record)
    
    print(f"Transformed {len(records)} cases")
    
    # Index to Algolia
    try:
        index_to_algolia(records, app_id, write_key)
        print("\n✓ Indexing complete!")
        print(f"\nNext steps:")
        print(f"1. Get your Search-Only API Key from Algolia dashboard")
        print(f"2. Add it to cases.html as ALGOLIA_SEARCH_KEY")
        print(f"3. Update cases.html to use Algolia InstantSearch")
    except Exception as e:
        print(f"Error indexing to Algolia: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
