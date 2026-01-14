#!/usr/bin/env python3
"""
Finalize Google evaluation: Update HTML when evaluation completes.
Run this after evaluation finishes.
"""

import json
import os
import sys
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from generate_viewer import load_all_provider_results

def update_cases_html():
    """Update cases.html with all provider results including Google."""
    
    print("=" * 70)
    print("Updating cases.html with Google Results")
    print("=" * 70)
    
    # Load all provider results
    all_results = load_all_provider_results()
    
    if not all_results:
        print("Error: No provider results found")
        return False
    
    if 'google' not in all_results:
        print("Error: Google results not found")
        return False
    
    google_results = all_results['google']
    google_predictions = google_results.get('predictions', [])
    successful = [p for p in google_predictions if p.get('success')]
    unique_cases = len(set(p.get('case_id') for p in successful))
    
    print(f"Google results: {unique_cases} unique cases")
    
    if unique_cases < 500:
        print(f"⚠ Warning: Only {unique_cases}/500 cases evaluated")
        print("  Continuing anyway to update HTML with current results...")
    
    # Load dataset for metadata
    case_lookup = {}
    dataset_file = 'data/processed/evaluation_dataset.json'
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
    primary_provider = 'openai' if 'openai' in all_results else list(all_results.keys())[0]
    combined_results = all_results[primary_provider].copy()
    combined_results['all_providers'] = all_results
    
    # Load cases.html
    cases_html = 'cases.html'
    with open(cases_html, 'r') as f:
        html = f.read()
    
    # Find resultsData - use line-based approach since it's more reliable
    start_marker = 'const resultsData = '
    start_idx = html.find(start_marker)
    
    if start_idx == -1:
        print("Error: Could not find 'const resultsData = ' in cases.html")
        return False
    
    # Find the end - look for the closing }; on a new line
    # Find the line number of start
    lines = html.split('\n')
    start_line = html[:start_idx].count('\n')
    
    # Find the closing }; - it should be on its own line
    end_line = start_line
    brace_count = 0
    in_string = False
    escape_next = False
    
    # Reconstruct to find end
    search_text = html[start_idx:]
    end_pos = 0
    
    # Simple approach: find the pattern "};" that closes the object
    # Look for }; that's likely at the end of the resultsData
    # Since it's a large JSON, find the last }; before the next major section
    pattern = r'const resultsData = (\{.*?\});'
    match = re.search(pattern, html, re.DOTALL)
    
    if not match:
        # Try finding by counting braces
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
            
            if char == '\\':
                escape = True
                pos += 1
                continue
            
            if char == '"' and not escape:
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
            end_pos = pos + 1
        else:
            print("Error: Could not find end of resultsData")
            return False
    else:
        end_pos = match.end()
    
    # Replace
    results_json = json.dumps(combined_results, indent=12)
    new_data = f'const resultsData = {results_json};'
    new_html = html[:start_idx] + new_data + html[end_pos:]
    
    # Enable Gemini card if Google results exist
    if 'google' in all_results:
        new_html = re.sub(
            r'<div class="model-card gemini disabled"',
            '<div class="model-card gemini"',
            new_html
        )
        # Add onclick if missing
        if 'onclick="selectModel(\'gemini\')"' not in new_html:
            new_html = re.sub(
                r'(<div class="model-card gemini"[^>]*)>',
                r'\1 onclick="selectModel(\'gemini\')">',
                new_html
            )
        
        # Update Gemini card with actual scores
        google_score = google_results.get('score', {})
        overall = google_score.get('overall_score', 0)
        individual = google_score.get('individual_scores', {})
        
        # Update score in card
        new_html = re.sub(
            r'(<div class="model-card gemini"[^>]*>.*?<div class="model-score">)—</div>',
            f'\\1{overall:.1f}%</div>',
            new_html,
            flags=re.DOTALL
        )
        
        # Update label
        new_html = re.sub(
            r'(<div class="model-card gemini"[^>]*>.*?<div class="model-label">)Coming Soon</div>',
            r'\1Overall Accuracy</div>',
            new_html,
            flags=re.DOTALL
        )
    
    # Write updated file
    with open(cases_html, 'w') as f:
        f.write(new_html)
    
    print(f"\n✓ Updated {cases_html}")
    print(f"  - Included results from {len(all_results)} providers")
    print(f"  - Google: {unique_cases} cases")
    if 'google' in all_results:
        print(f"  - Gemini card enabled")
    
    return True

if __name__ == '__main__':
    success = update_cases_html()
    if success:
        print("\n✓ HTML update complete!")
        print("  Open cases.html in your browser to see Google results")
    else:
        print("\n✗ HTML update failed")
        sys.exit(1)
