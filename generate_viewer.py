#!/usr/bin/env python3
"""
Generate HTML viewer with embedded results data.
"""

import json
import os
import re
import webbrowser

def generate_viewer(results_file='data/processed/evaluation_results_openai.json', 
                   dataset_file='data/processed/evaluation_dataset.json',
                   template_file='results_viewer.html',
                   output_file='data/processed/results_viewer.html'):
    """Generate HTML viewer with embedded results."""
    
    # Load results
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Load dataset to get metadata and reducto_fields
    case_lookup = {}
    if os.path.exists(dataset_file):
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
        for case in dataset.get('cases', []):
            case_lookup[case['case_id']] = {
                'metadata': case.get('metadata', {}),
                'reducto_fields': case.get('reducto_fields', {}),
                'complaint_text': case.get('complaint_text', '')[:500]  # First 500 chars
            }
    
    # Enrich predictions with metadata and reducto_fields
    for pred in results.get('predictions', []):
        case_id = pred.get('case_id')
        if case_id in case_lookup:
            if 'metadata' not in pred or not pred['metadata']:
                pred['metadata'] = case_lookup[case_id]['metadata']
            pred['reducto_fields'] = case_lookup[case_id]['reducto_fields']
            pred['complaint_excerpt'] = case_lookup[case_id]['complaint_text']
    
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


def load_all_provider_results(results_dir='data/processed'):
    """Load results from all available providers."""
    providers = {
        'openai': 'evaluation_results_openai.json',
        'anthropic': 'evaluation_results_anthropic.json',
        'google': 'evaluation_results_google.json'
    }
    
    all_results = {}
    
    for provider, filename in providers.items():
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    all_results[provider] = json.load(f)
                print(f"Loaded {provider} results: {len(all_results[provider].get('predictions', []))} predictions")
            except Exception as e:
                print(f"Warning: Could not load {provider} results: {e}")
        else:
            print(f"Warning: {filepath} not found")
    
    return all_results


def update_cases_html(results_dir='data/processed',
                      cases_html='cases.html',
                      dataset_file='data/processed/evaluation_dataset.json'):
    """Update cases.html with latest evaluation results from all providers."""
    
    # Load all provider results
    all_results = load_all_provider_results(results_dir)
    
    if not all_results:
        print("Error: No provider results found")
        return cases_html
    
    # Load dataset to get metadata
    case_lookup = {}
    if os.path.exists(dataset_file):
        with open(dataset_file, 'r') as f:
            dataset = json.load(f)
        for case in dataset.get('cases', []):
            case_lookup[case['case_id']] = {
                'metadata': case.get('metadata', {}),
                'reducto_fields': case.get('reducto_fields', {}),
            }
    
    # Enrich predictions with metadata
    for provider, results in all_results.items():
        for pred in results.get('predictions', []):
            case_id = pred.get('case_id')
            if case_id in case_lookup:
                if 'metadata' not in pred or not pred['metadata']:
                    pred['metadata'] = case_lookup[case_id]['metadata']
                pred['reducto_fields'] = case_lookup[case_id]['reducto_fields']
    
    # Create combined results structure
    # Use OpenAI as default/primary, but include all providers
    primary_provider = 'openai' if 'openai' in all_results else list(all_results.keys())[0]
    combined_results = all_results[primary_provider].copy()
    combined_results['all_providers'] = all_results
    
    # Load current cases.html
    with open(cases_html, 'r') as f:
        html = f.read()
    
    # Create new results JSON
    results_json = json.dumps(combined_results, indent=12)
    
    # Try to find and replace the placeholder first
    if 'RESULTS_PLACEHOLDER' in html:
        new_html = html.replace('RESULTS_PLACEHOLDER', results_json)
        with open(cases_html, 'w') as f:
            f.write(new_html)
        print(f"Updated {cases_html} with {len(combined_results.get('predictions', []))} cases (placeholder)")
        return cases_html
    
    # Otherwise try regex pattern for existing data
    # Match from 'const resultsData = ' to the closing '};'
    # Use a more permissive pattern that handles large nested JSON
    pattern = r'const resultsData = (\{.*?\});'
    match = re.search(pattern, html, re.DOTALL)
    
    # If that doesn't work, find manually by counting braces
    if not match:
        start_marker = 'const resultsData = '
        start_idx = html.find(start_marker)
        if start_idx != -1:
            # Find the closing }; by counting braces
            pos = start_idx + len(start_marker)
            brace_count = 0
            in_string = False
            escape = False
            
            if pos < len(html) and html[pos] == '{':
                brace_count = 1
                pos += 1
            
            while pos < len(html) and brace_count > 0:
                char = html[pos]
                
                if escape:
                    escape = False
                    pos += 1
                    continue
                
                if char == '\\\\':
                    escape = True
                    pos += 1
                    continue
                
                if char == '\"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                
                pos += 1
            
            # Find semicolon
            while pos < len(html) and html[pos] != ';':
                pos += 1
            
            if pos < len(html):
                # Create a match-like object
                class Match:
                    def __init__(self, start, end):
                        self.start_pos = start
                        self.end_pos = end
                match = Match(start_idx, pos + 1)
    
    if match:
        # Replace the matched section with new data
        new_data = f'const resultsData = {results_json};'
        if hasattr(match, 'start_pos'):
            # Manual match
            new_html = html[:match.start_pos] + new_data + html[match.end_pos:]
        else:
            # Regex match
        new_html = html[:match.start()] + new_data + html[match.end():]
        
        # Also enable Google/Gemini model card if Google results exist
        if 'google' in all_results:
            # Remove disabled class from gemini card
            new_html = re.sub(
                r'<div class="model-card gemini disabled"',
                '<div class="model-card gemini"',
                new_html
            )
        
        # Write updated file
        with open(cases_html, 'w') as f:
            f.write(new_html)
        
        total_cases = sum(len(r.get('predictions', [])) for r in all_results.values())
        print(f"Updated {cases_html} with results from {len(all_results)} providers ({total_cases} total predictions)")
    else:
        print(f"Warning: Could not find resultsData or placeholder in {cases_html}")
    
    return cases_html


if __name__ == '__main__':
    # Generate the results viewer
    output = generate_viewer()
    abs_path = os.path.abspath(output)
    print(f"\nGenerated: file://{abs_path}")
    
    # Also update cases.html with all providers
    update_cases_html()
    
    # Open in browser
    cases_path = os.path.abspath('cases.html')
    print(f"Opening cases.html in browser: file://{cases_path}")
    webbrowser.open(f'file://{cases_path}')

