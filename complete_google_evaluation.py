#!/usr/bin/env python3
"""
Complete the Google evaluation process:
1. Verify all 500 cases are evaluated
2. Deduplicate if needed
3. Recalculate scores
4. Update UI
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def verify_and_deduplicate(results_file='data/processed/evaluation_results_google.json',
                          dataset_file='data/processed/evaluation_dataset.json'):
    """Verify completeness and remove duplicates."""
    
    print("=" * 60)
    print("Step 1: Verifying and Deduplicating Results")
    print("=" * 60)
    
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
    case_predictions_map = defaultdict(list)
    for idx, pred in enumerate(predictions):
        case_id = pred.get('case_id')
        if case_id:
            case_counts[case_id] += 1
            case_predictions_map[case_id].append((idx, pred))
    
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
        deduplicated = []
        for case_id, pred_list in case_predictions_map.items():
            if len(pred_list) > 1:
                # Keep the last one (most recent)
                pred_list.sort(key=lambda x: x[0])
                deduplicated.append(pred_list[-1][1])
            else:
                deduplicated.append(pred_list[0][1])
        
        results['predictions'] = deduplicated
        successful_dedup = [p for p in deduplicated if p.get('success')]
        
        print(f"  Deduplicated: {len(deduplicated)} predictions ({len(successful_dedup)} successful)")
        print(f"  Removed: {len(predictions) - len(deduplicated)} duplicate entries")
        
        # Save
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    
    # Final status
    if len(missing) == 0:
        print(f"\n✓ All cases evaluated!")
        return True
    else:
        print(f"\n⚠ Still missing {len(missing)} cases")
        return False


def recalculate_scores(results_file='data/processed/evaluation_results_google.json'):
    """Recalculate scores for all predictions."""
    
    print("\n" + "=" * 60)
    print("Step 2: Recalculating Scores")
    print("=" * 60)
    
    from evaluation.score_calculator import ScoreCalculator, PredictionResult
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    
    print(f"Processing {len(successful)} successful predictions...")
    
    calculator = ScoreCalculator()
    comparison_results = []
    
    for pred in successful:
        comp = pred.get('comparison', {})
        pr = PredictionResult(
            case_id=pred['case_id'],
            resolution_type_correct=comp.get('resolution_type_correct'),
            disgorgement_correct=comp.get('disgorgement_correct'),
            penalty_correct=comp.get('penalty_correct'),
            interest_correct=comp.get('interest_correct'),
            injunction_correct=comp.get('injunction_correct'),
            officer_bar_correct=comp.get('officer_bar_correct'),
            conduct_restriction_correct=comp.get('conduct_restriction_correct'),
            predicted=pred.get('predicted', {}),
            ground_truth=pred.get('ground_truth', {})
        )
        comparison_results.append(pr)
    
    # Calculate model score
    model_name = results.get('model_name', 'Google/gemini-3-flash-preview')
    score = calculator.calculate_model_score(model_name, comparison_results)
    
    # Update results
    results['score'] = {
        'model_name': model_name,
        'overall_score': score.overall_score,
        'individual_scores': {
            'resolution_type': score.resolution_type_accuracy,
            'disgorgement': score.disgorgement_accuracy,
            'penalty': score.penalty_accuracy,
            'prejudgment_interest': score.interest_accuracy,
            'monetary_average': score.monetary_accuracy,
            'has_injunction': score.injunction_accuracy,
            'has_officer_director_bar': score.officer_bar_accuracy,
            'has_conduct_restriction': score.conduct_restriction_accuracy
        },
        'scorable_counts': {
            'total_cases': len(successful),
            'resolution_type': score.scorable_counts.get('resolution_type', 0),
            'disgorgement': score.scorable_counts.get('disgorgement', 0),
            'penalty': score.scorable_counts.get('penalty', 0),
            'interest': score.scorable_counts.get('interest', 0)
        }
    }
    
    # Save updated results
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Scores recalculated:")
    print(f"  Overall Score: {score.overall_score:.1f}%")
    print(f"  Resolution Type: {score.resolution_type_accuracy:.1f}%")
    print(f"  Disgorgement: {score.disgorgement_accuracy:.1f}%")
    print(f"  Penalty: {score.penalty_accuracy:.1f}%")
    print(f"  Interest: {score.interest_accuracy:.1f}%")
    print(f"  Monetary Avg: {score.monetary_accuracy:.1f}%")
    print(f"  Injunction: {score.injunction_accuracy:.1f}%")
    print(f"  Officer Bar: {score.officer_bar_accuracy:.1f}%")
    print(f"  Conduct Restr: {score.conduct_restriction_accuracy:.1f}%")


def update_ui():
    """Update the UI with complete results."""
    
    print("\n" + "=" * 60)
    print("Step 3: Updating UI")
    print("=" * 60)
    
    from generate_viewer import update_cases_html
    
    try:
        update_cases_html()
        print("\n✓ UI updated successfully")
    except Exception as e:
        print(f"\n✗ Error updating UI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("Google Evaluation Completion Script")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Step 1: Verify and deduplicate
    if verify_and_deduplicate():
        # Step 2: Recalculate scores
        recalculate_scores()
        
        # Step 3: Update UI
        update_ui()
        
        print("\n" + "=" * 60)
        print("✓ All steps completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠ Evaluation incomplete - some cases are still missing")
        print("=" * 60)
        print("You may need to run the evaluation again or check for errors.")
        sys.exit(1)
