#!/usr/bin/env python3
"""
Verify Google evaluation results - check completeness and deduplicate if needed.
"""

import json
import os
from collections import defaultdict

def verify_and_deduplicate(results_file='data/processed/evaluation_results_google.json',
                          dataset_file='data/processed/evaluation_dataset.json'):
    """Verify all cases are evaluated and remove duplicates."""
    
    # Load dataset
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
    all_case_ids = {case['case_id'] for case in dataset.get('cases', [])}
    print(f"Total cases in dataset: {len(all_case_ids)}")
    
    # Load results
    if not os.path.exists(results_file):
        print(f"Error: {results_file} not found")
        return False
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    
    print(f"\nCurrent results:")
    print(f"  Total predictions: {len(predictions)}")
    print(f"  Successful predictions: {len(successful)}")
    
    # Check for duplicates
    case_counts = defaultdict(int)
    for pred in successful:
        case_counts[pred.get('case_id')] += 1
    
    duplicates = {case_id: count for case_id, count in case_counts.items() if count > 1}
    if duplicates:
        print(f"\n  Duplicates found: {len(duplicates)} cases have multiple predictions")
        print(f"  Total duplicate entries: {sum(count - 1 for count in duplicates.values())}")
    
    # Get evaluated case IDs
    evaluated_case_ids = {pred.get('case_id') for pred in successful}
    missing = all_case_ids - evaluated_case_ids
    
    print(f"\nEvaluation status:")
    print(f"  Evaluated cases: {len(evaluated_case_ids)}")
    print(f"  Missing cases: {len(missing)}")
    
    if missing:
        print(f"\n  First 10 missing case IDs:")
        for case_id in sorted(list(missing))[:10]:
            print(f"    - {case_id}")
    
    # Deduplicate if needed
    if duplicates:
        print(f"\nDeduplicating results...")
        # Group by case_id, keeping the most recent (last in list)
        case_predictions = defaultdict(list)
        for idx, pred in enumerate(predictions):
            case_id = pred.get('case_id')
            if case_id:
                case_predictions[case_id].append((idx, pred))
        
        deduplicated = []
        for case_id, pred_list in case_predictions.items():
            if len(pred_list) > 1:
                # Keep the last one (most recent)
                pred_list.sort(key=lambda x: x[0])
                deduplicated.append(pred_list[-1][1])
            else:
                deduplicated.append(pred_list[0][1])
        
        results['predictions'] = deduplicated
        successful_dedup = [p for p in deduplicated if p.get('success')]
        
        # Update score counts
        if 'score' in results and 'scorable_counts' in results['score']:
            results['score']['scorable_counts']['total_cases'] = len(successful_dedup)
        
        # Save
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"  Deduplicated: {len(deduplicated)} predictions ({len(successful_dedup)} successful)")
        print(f"  Removed: {len(predictions) - len(deduplicated)} duplicate entries")
    
    # Final status
    if len(missing) == 0 and len(duplicates) == 0:
        print(f"\n✓ All cases evaluated! No duplicates found.")
        return True
    elif len(missing) == 0:
        print(f"\n✓ All cases evaluated! (Duplicates were removed)")
        return True
    else:
        print(f"\n⚠ Still missing {len(missing)} cases")
        return False

if __name__ == '__main__':
    verify_and_deduplicate()
