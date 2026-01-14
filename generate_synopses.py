#!/usr/bin/env python3
"""
Generate case synopses for all evaluated cases using GPT-4o.
Updates evaluation_results_openai.json with generated synopses.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from preprocessing.synopsis_generator import SynopsisGenerator


def load_litigation_cases(path: str = "litigation-cases.json") -> dict:
    """Load litigation cases to get fullText."""
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Create lookup by case ID
    cases_by_id = {}
    for case in data.get('cases', []):
        case_id = case.get('releaseNumber', '')
        if case_id:
            cases_by_id[case_id] = case
    
    return cases_by_id


def load_results(path: str = "data/processed/evaluation_results_openai.json") -> dict:
    """Load existing evaluation results."""
    with open(path, 'r') as f:
        return json.load(f)


def save_results(data: dict, path: str = "data/processed/evaluation_results_openai.json"):
    """Save updated evaluation results."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        print("Run: export OPENAI_API_KEY=your_key")
        sys.exit(1)
    
    print("=" * 60)
    print("Generating Case Synopses with GPT-4o")
    print("=" * 60)
    
    # Load data
    print("\nLoading litigation cases...")
    litigation_cases = load_litigation_cases()
    print(f"  Loaded {len(litigation_cases)} cases")
    
    print("\nLoading evaluation results...")
    results = load_results()
    predictions = results.get('predictions', [])
    print(f"  Found {len(predictions)} predictions")
    
    # Initialize generator
    generator = SynopsisGenerator()
    
    # Track progress
    total = len(predictions)
    generated = 0
    skipped = 0
    errors = 0
    
    # Optional limit for testing (pass --limit N as argument)
    import sys
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    if limit:
        total = min(total, limit)
        predictions = predictions[:total]
    
    print(f"\nGenerating synopses for {total} cases...")
    print("(This will take a few minutes)\n")
    
    for i, pred in enumerate(predictions):
        case_id = pred.get('case_id', '')
        
        # Check if already has synopsis
        metadata = pred.get('metadata', {})
        reducto_fields = metadata.get('reducto_fields', {})
        
        if reducto_fields.get('case_synopsis') and len(reducto_fields.get('case_synopsis', '')) > 200:
            skipped += 1
            print(f"  [{i+1}/{total}] {case_id} - Already has synopsis, skipping")
            continue
        
        # Get fullText from litigation cases
        case_data = litigation_cases.get(case_id, {})
        full_text = case_data.get('features', {}).get('fullText', '')
        
        if not full_text or len(full_text) < 200:
            skipped += 1
            print(f"  [{i+1}/{total}] {case_id} - No fullText available, skipping")
            continue
        
        # Generate synopsis
        print(f"  [{i+1}/{total}] {case_id} - Generating synopsis...", end=" ", flush=True)
        
        try:
            synopsis = generator.generate(full_text)
            
            if synopsis and len(synopsis) > 100:
                # Update the prediction with synopsis
                if 'metadata' not in pred:
                    pred['metadata'] = {}
                if 'reducto_fields' not in pred['metadata']:
                    pred['metadata']['reducto_fields'] = {}
                
                pred['metadata']['reducto_fields']['case_synopsis'] = synopsis
                generated += 1
                print("✓")
            else:
                errors += 1
                print("✗ (empty result)")
                
        except Exception as e:
            errors += 1
            print(f"✗ ({str(e)[:50]})")
        
        # Small delay to avoid rate limits
        time.sleep(0.5)
        
        # Incremental save every 25 cases to preserve progress
        if (i + 1) % 25 == 0:
            save_results(results)
            print(f"    [Checkpoint saved at {i+1} cases]")
    
    # Save updated results
    print("\nSaving updated results...")
    save_results(results)
    
    print("\n" + "=" * 60)
    print("Synopsis Generation Complete!")
    print("=" * 60)
    print(f"  Generated: {generated}")
    print(f"  Skipped:   {skipped}")
    print(f"  Errors:    {errors}")
    print(f"\nResults saved to: data/processed/evaluation_results_openai.json")
    print("\nRun 'python3 generate_viewer.py' to update the website.")


if __name__ == "__main__":
    main()
