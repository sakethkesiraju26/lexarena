#!/usr/bin/env python3
"""
Deduplicate Google evaluation results by keeping only the most recent prediction for each case.
"""

import json
import os
from collections import defaultdict

def deduplicate_results(results_file='data/processed/evaluation_results_google.json'):
    """Remove duplicate case evaluations, keeping the most recent one."""
    
    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found")
        return
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    predictions = results.get('predictions', [])
    print(f"Original predictions: {len(predictions)}")
    
    # Group by case_id, keeping track of index for tie-breaking
    case_predictions = defaultdict(list)
    for idx, pred in enumerate(predictions):
        case_id = pred.get('case_id')
        if case_id:
            case_predictions[case_id].append((idx, pred))
    
    # For each case, keep the last prediction (highest index)
    deduplicated = []
    duplicates_removed = 0
    
    for case_id, pred_list in case_predictions.items():
        if len(pred_list) > 1:
            # Sort by index (most recent last) and keep the last one
            pred_list.sort(key=lambda x: x[0])
            duplicates_removed += len(pred_list) - 1
            deduplicated.append(pred_list[-1][1])
        else:
            deduplicated.append(pred_list[0][1])
    
    # Update results
    results['predictions'] = deduplicated
    
    # Recalculate scores if needed (the score calculator will handle this on next evaluation)
    # But we can update the count
    if 'score' in results and 'scorable_counts' in results['score']:
        results['score']['scorable_counts']['total_cases'] = len(deduplicated)
    
    # Save deduplicated results
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Deduplicated predictions: {len(deduplicated)}")
    print(f"Duplicates removed: {duplicates_removed}")
    print(f"Results saved to: {results_file}")

if __name__ == '__main__':
    deduplicate_results()
