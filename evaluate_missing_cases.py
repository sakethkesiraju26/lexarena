#!/usr/bin/env python3
"""
Script to evaluate only the missing cases that haven't been evaluated yet.
This filters by case_id rather than array index to avoid duplicates.
"""

import json
import os
import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from evaluation.llm_runner import GoogleProvider, LLMRunner
from evaluation.score_calculator import ScoreCalculator, PredictionResult


def main():
    # Configuration
    dataset_file = 'data/processed/evaluation_dataset.json'
    results_file = 'data/processed/evaluation_results_google.json'
    output_dir = 'data/processed'
    
    # Get API key from environment
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it before running this script:")
        print("  export GOOGLE_API_KEY=your_key_here")
        sys.exit(1)
    
    print("=" * 70)
    print("Evaluating Missing Cases Only")
    print("=" * 70)
    print()
    
    # Load dataset
    print(f"Loading dataset from {dataset_file}...")
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
    
    all_cases = dataset.get('cases', [])
    all_case_ids = {case['case_id'] for case in all_cases}
    print(f"Total cases in dataset: {len(all_case_ids)}")
    
    # Load existing results to find evaluated cases
    print(f"Loading existing results from {results_file}...")
    if os.path.exists(results_file):
        with open(results_file, 'r') as f:
            existing_results = json.load(f)
        existing_predictions = existing_results.get('predictions', [])
        evaluated_ids = {p.get('case_id') for p in existing_predictions if p.get('success')}
        print(f"Already evaluated: {len(evaluated_ids)} cases")
    else:
        existing_results = None
        existing_predictions = []
        evaluated_ids = set()
        print("No existing results file found")
    
    # Find missing cases
    missing_ids = all_case_ids - evaluated_ids
    print(f"Missing cases to evaluate: {len(missing_ids)}")
    
    if not missing_ids:
        print("\n✓ All cases have been evaluated!")
        return
    
    # Filter dataset to only missing cases
    missing_cases = [case for case in all_cases if case['case_id'] in missing_ids]
    missing_cases.sort(key=lambda x: x['case_id'])  # Sort for consistent ordering
    
    print(f"\nCases to evaluate: {[case['case_id'] for case in missing_cases[:10]]}")
    if len(missing_cases) > 10:
        print(f"... and {len(missing_cases) - 10} more")
    print()
    
    # Initialize provider and runner
    provider = GoogleProvider(
        model='gemini-3-flash-preview',
        api_key=api_key
    )
    runner = LLMRunner(provider)
    model_name = provider.get_model_name()
    
    print(f"Running evaluation with {model_name} on {len(missing_cases)} cases...")
    print("Saving after each case for live updates...")
    print()
    
    # Run evaluation with incremental saving (similar to run_evaluation.py append mode)
    predictions = []
    comparison_results = []
    start_time = time.time()
    
    for i, case in enumerate(missing_cases):
        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{len(missing_cases)}")
        
        # Run single case
        result = runner.run_single(case)
        predictions.append(result)
        
        # Add to comparison if successful
        if result['success']:
            comp = result['comparison']
            pr = PredictionResult(
                case_id=result['case_id'],
                resolution_type_correct=comp['resolution_type_correct'],
                disgorgement_correct=comp['disgorgement_correct'],
                penalty_correct=comp['penalty_correct'],
                interest_correct=comp['interest_correct'],
                injunction_correct=comp['injunction_correct'],
                officer_bar_correct=comp['officer_bar_correct'],
                conduct_restriction_correct=comp['conduct_restriction_correct'],
                predicted=result['predicted'],
                ground_truth=result['ground_truth']
            )
            comparison_results.append(pr)
        
        # Save incrementally after each case
        all_predictions = existing_predictions + predictions
        calculator = ScoreCalculator()
        
        # Need to combine comparison results from existing and new
        # Load existing comparison results
        if existing_results:
            existing_comparison = []
            for pred in existing_predictions:
                if pred.get('success') and pred.get('comparison'):
                    comp = pred['comparison']
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
                    existing_comparison.append(pr)
            all_comparison_results = existing_comparison + comparison_results
        else:
            all_comparison_results = comparison_results
        
        score = calculator.calculate_model_score(model_name, all_comparison_results)
        
        # Update results
        if existing_results:
            updated = existing_results.copy()
            updated['predictions'] = all_predictions
            updated['score'] = score.to_dict()
            updated['timestamp'] = datetime.now().isoformat()
        else:
            from evaluation.llm_runner import EvaluationResult
            temp_result = EvaluationResult(
                model_name=model_name,
                model_config=provider.get_config(),
                score=score,
                predictions=predictions,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time
            )
            updated = temp_result.to_dict()
            updated['predictions'] = all_predictions
        
        with open(results_file, 'w') as f:
            json.dump(updated, f, indent=2, default=str)
        
        if (i + 1) % 10 == 0:
            unique_count = len(set(p.get('case_id') for p in all_predictions if p.get('success')))
            print(f"  ✓ Saved {i + 1} new cases (total unique: {unique_count})")
    
    # Final summary
    duration = time.time() - start_time
    final_unique = len(set(p.get('case_id') for p in all_predictions if p.get('success')))
    
    print()
    print("=" * 70)
    print("Evaluation Complete!")
    print("=" * 70)
    print(f"New cases evaluated: {len(missing_cases)}")
    print(f"Total unique cases: {final_unique}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Overall Score: {score.overall_score:.1f}%")
    print(f"Results saved to: {results_file}")
    print("=" * 70)


if __name__ == '__main__':
    main()
