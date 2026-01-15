#!/usr/bin/env python3
"""
OpenAI Batch API Evaluation for GPT-5.2

Creates a batch job for evaluating all SEC cases. 
Batch API is 50% cheaper and processes within 24 hours.

Usage:
  # Step 1: Create batch
  python run_batch_evaluation.py --create-batch --model gpt-5.2
  
  # Step 2: Check status (run periodically)
  python run_batch_evaluation.py --check-status --batch-id <batch_id>
  
  # Step 3: Download results when complete
  python run_batch_evaluation.py --download-results --batch-id <batch_id>
"""

import argparse
import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

SYSTEM_PROMPT = """You are a legal analyst evaluating SEC enforcement cases.

Read the following SEC complaint and predict the likely outcome.

Predict the following outcomes for this case:

1. Resolution Type: Choose one of:
   - settled (defendant will agree to terms - includes consent judgments and settled actions)
   - litigated (case will go to trial/judgment - court makes final decision)

2. Disgorgement Amount: The amount in dollars the defendant must return (ill-gotten gains). Enter a number or null if none expected.

3. Civil Penalty Amount: The civil penalty in dollars. Enter a number or null if none expected.

4. Prejudgment Interest: Interest on disgorgement in dollars. Enter a number or null if none expected.

5. Has Injunction: Will there be injunctive relief? (yes/no)

6. Has Officer/Director Bar: Will the defendant be barred from serving as an officer or director? (yes/no)

7. Has Conduct Restriction: Will there be conduct-based restrictions (e.g., trading restrictions, industry bar)? (yes/no)

Respond in JSON format with your predictions and reasoning."""


def create_batch_file(model: str, max_cases: int = None):
    """Create JSONL file for batch processing."""
    from evaluation.llm_prompt_formatter import format_prompt
    
    # Load evaluation dataset
    dataset_file = 'data/processed/evaluation_dataset.json'
    with open(dataset_file, 'r') as f:
        data = json.load(f)
    
    cases = data.get('cases', [])
    if max_cases:
        cases = cases[:max_cases]
    
    print(f"Creating batch file for {len(cases)} cases...")
    
    # Create JSONL batch input
    batch_file = f'batch_input_{model.replace(".", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'
    
    seen_ids = set()
    with open(batch_file, 'w') as f:
        for idx, case in enumerate(cases):
            # Ensure unique custom_id by adding index
            base_id = case['case_id']
            custom_id = f"{base_id}_{idx}" if base_id in seen_ids else base_id
            seen_ids.add(base_id)
            
            prompt = format_prompt(case['complaint_text'], short_format=False)
            
            request = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": model,
                    "input": f"{SYSTEM_PROMPT}\n\n{prompt}"
                }
            }
            f.write(json.dumps(request) + '\n')
    
    print(f"✓ Batch file created: {batch_file}")
    print(f"  Cases: {len(cases)}")
    return batch_file


def upload_and_create_batch(batch_file: str):
    """Upload file and create batch job."""
    import openai
    
    client = openai.OpenAI()
    
    # Upload file
    print(f"Uploading {batch_file}...")
    with open(batch_file, 'rb') as f:
        file_response = client.files.create(
            file=f,
            purpose="batch"
        )
    
    file_id = file_response.id
    print(f"✓ File uploaded: {file_id}")
    
    # Create batch
    print("Creating batch job...")
    batch = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/responses",
        completion_window="24h"
    )
    
    print(f"\n{'='*60}")
    print(f"✓ BATCH CREATED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"  Batch ID: {batch.id}")
    print(f"  Status: {batch.status}")
    print(f"  Created: {datetime.now().isoformat()}")
    print(f"\nTo check status:")
    print(f"  python run_batch_evaluation.py --check-status --batch-id {batch.id}")
    print(f"\nResults will be ready within 24 hours.")
    
    # Save batch info
    with open('batch_info.json', 'w') as f:
        json.dump({
            'batch_id': batch.id,
            'file_id': file_id,
            'input_file': batch_file,
            'created_at': datetime.now().isoformat(),
            'status': batch.status
        }, f, indent=2)
    
    return batch.id


def check_batch_status(batch_id: str):
    """Check status of a batch job."""
    import openai
    
    client = openai.OpenAI()
    batch = client.batches.retrieve(batch_id)
    
    print(f"\n{'='*60}")
    print(f"Batch Status: {batch.id}")
    print(f"{'='*60}")
    print(f"  Status: {batch.status}")
    print(f"  Created: {batch.created_at}")
    
    if hasattr(batch, 'request_counts') and batch.request_counts:
        rc = batch.request_counts
        print(f"  Completed: {rc.completed}/{rc.total}")
        print(f"  Failed: {rc.failed}")
    
    if batch.status == 'completed':
        print(f"\n✓ Batch complete! Output file: {batch.output_file_id}")
        print(f"\nTo download results:")
        print(f"  python run_batch_evaluation.py --download-results --batch-id {batch_id}")
    elif batch.status == 'failed':
        print(f"\n✗ Batch failed!")
        if hasattr(batch, 'errors') and batch.errors:
            print(f"  Errors: {batch.errors}")
    
    return batch


def download_results(batch_id: str):
    """Download and process batch results."""
    import openai
    from evaluation.score_calculator import ScoreCalculator, PredictionResult, parse_llm_response
    
    client = openai.OpenAI()
    batch = client.batches.retrieve(batch_id)
    
    if batch.status != 'completed':
        print(f"Batch not complete yet. Status: {batch.status}")
        return None
    
    # Download output file
    print(f"Downloading results from {batch.output_file_id}...")
    file_response = client.files.content(batch.output_file_id)
    
    # Parse results
    results = []
    for line in file_response.text.strip().split('\n'):
        result = json.loads(line)
        results.append(result)
    
    print(f"✓ Downloaded {len(results)} results")
    
    # Load original cases for ground truth
    with open('data/processed/evaluation_dataset.json', 'r') as f:
        dataset = json.load(f)
    
    cases_by_id = {c['case_id']: c for c in dataset.get('cases', [])}
    
    # Process results
    calculator = ScoreCalculator()
    predictions = []
    comparison_results = []
    
    for result in results:
        case_id = result['custom_id']
        case = cases_by_id.get(case_id, {})
        ground_truth = case.get('ground_truth', {})
        metadata = case.get('metadata', {})
        
        if result.get('error'):
            predictions.append({
                'case_id': case_id,
                'success': False,
                'error': result['error'],
                'ground_truth': ground_truth,
                'metadata': metadata
            })
            continue
        
        # Extract response text from nested structure
        response_body = result.get('response', {}).get('body', {})
        raw_response = ''
        
        # New Responses API format: output[0].content[0].text
        output = response_body.get('output', [])
        if output and len(output) > 0:
            content = output[0].get('content', [])
            if content and len(content) > 0:
                raw_response = content[0].get('text', '')
        
        # Parse prediction
        predicted = parse_llm_response(raw_response)
        
        # Compare to ground truth
        comparison = calculator.compare_single(case_id, predicted, ground_truth)
        
        pred_result = {
            'case_id': case_id,
            'success': True,
            'predicted': predicted,
            'ground_truth': ground_truth,
            'metadata': metadata,
            'raw_response': raw_response,
            'comparison': {
                'resolution_type_correct': comparison.resolution_type_correct,
                'disgorgement_correct': comparison.disgorgement_correct,
                'penalty_correct': comparison.penalty_correct,
                'interest_correct': comparison.interest_correct,
                'injunction_correct': comparison.injunction_correct,
                'officer_bar_correct': comparison.officer_bar_correct,
                'conduct_restriction_correct': comparison.conduct_restriction_correct,
                'errors': comparison.errors
            }
        }
        predictions.append(pred_result)
        comparison_results.append(comparison)
    
    # Calculate score
    model_name = f"OpenAI/gpt-5.2"
    score = calculator.calculate_model_score(model_name, comparison_results)
    
    # Save results
    output = {
        'model_name': model_name,
        'model_config': {'provider': 'openai', 'model': 'gpt-5.2', 'batch_api': True},
        'score': score.to_dict(),
        'timestamp': datetime.now().isoformat(),
        'batch_id': batch_id,
        'predictions': predictions
    }
    
    output_file = 'data/processed/evaluation_results_gpt52.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ EVALUATION COMPLETE!")
    print(f"{'='*60}")
    print(f"  Model: {model_name}")
    print(f"  Cases: {len(predictions)}")
    print(f"  Overall Score: {score.overall_score:.1f}%")
    print(f"\n  Results saved to: {output_file}")
    
    return output


def main():
    parser = argparse.ArgumentParser(description='OpenAI Batch API Evaluation')
    parser.add_argument('--create-batch', action='store_true', help='Create batch job')
    parser.add_argument('--check-status', action='store_true', help='Check batch status')
    parser.add_argument('--download-results', action='store_true', help='Download completed results')
    parser.add_argument('--batch-id', type=str, help='Batch ID for status/download')
    parser.add_argument('--model', type=str, default='gpt-5.2', help='Model to use')
    parser.add_argument('--max-cases', type=int, help='Limit number of cases')
    
    args = parser.parse_args()
    
    if args.create_batch:
        batch_file = create_batch_file(args.model, args.max_cases)
        upload_and_create_batch(batch_file)
    
    elif args.check_status:
        if not args.batch_id:
            # Try to load from saved file
            try:
                with open('batch_info.json', 'r') as f:
                    info = json.load(f)
                args.batch_id = info['batch_id']
            except:
                print("Error: --batch-id required")
                return
        check_batch_status(args.batch_id)
    
    elif args.download_results:
        if not args.batch_id:
            try:
                with open('batch_info.json', 'r') as f:
                    info = json.load(f)
                args.batch_id = info['batch_id']
            except:
                print("Error: --batch-id required")
                return
        download_results(args.batch_id)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
