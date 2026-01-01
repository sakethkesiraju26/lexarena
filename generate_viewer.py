#!/usr/bin/env python3
"""
Generate HTML viewer with embedded results data.
"""

import json
import os
import webbrowser

def generate_viewer(results_file='data/processed/evaluation_results_openai.json', 
                   dataset_file='data/processed/evaluation_dataset.json',
                   template_file='results_viewer.html',
                   output_file='data/processed/results_viewer.html'):
    """Generate HTML viewer with embedded results."""
    
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Load dataset to get metadata
    metadata_lookup = {}
    if os.path.exists(dataset_file):
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
        for case in dataset.get('cases', []):
            metadata_lookup[case['case_id']] = case.get('metadata', {})
    
    # Enrich predictions with metadata if not already present
    for pred in results.get('predictions', []):
        if 'metadata' not in pred or not pred['metadata']:
            case_id = pred.get('case_id')
            if case_id in metadata_lookup:
                pred['metadata'] = metadata_lookup[case_id]
    
    # Load template
    with open(template_file, 'r') as f:
        template = f.read()
    
    # Embed data
    results_json = json.dumps(results, indent=2)
    html = template.replace('RESULTS_DATA_PLACEHOLDER', results_json)
    
    # Write output
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Generated viewer: {output_file}")
    return output_file


if __name__ == '__main__':
    output = generate_viewer()
    abs_path = os.path.abspath(output)
    print(f"\nOpening in browser: file://{abs_path}")
    webbrowser.open(f'file://{abs_path}')

