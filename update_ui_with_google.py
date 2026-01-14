#!/usr/bin/env python3
"""
Update cases.html to include Google results and enable Gemini model card.
"""

import json
import os
import re

def update_cases_html():
    """Update cases.html with Google results."""
    
    # Load all provider results
    results_dir = 'data/processed'
    providers = {
        'openai': 'evaluation_results_openai.json',
        'anthropic': 'evaluation_results_anthropic.json',
        'google': 'evaluation_results_google.json'
    }
    
    all_results = {}
    for provider, filename in providers.items():
        filepath = os.path.join(results_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                all_results[provider] = json.load(f)
            print(f"Loaded {provider}: {len(all_results[provider].get('predictions', []))} predictions")
    
    if not all_results:
        print("Error: No provider results found")
        return
    
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
    
    # Find and replace resultsData
    # Use a more robust pattern that finds the start and handles large data
    pattern = r'(const resultsData = )\{[^}]*"model_name"[^}]*\{[^}]*"predictions"[^}]*\[.*?\];'
    
    # Try simpler approach: find the start of const resultsData and replace everything until the closing };
    # Since the data is huge, we'll find the start position and manually construct
    start_marker = 'const resultsData = '
    start_idx = html.find(start_marker)
    
    if start_idx == -1:
        print("Error: Could not find 'const resultsData = ' in cases.html")
        return
    
    # Find the matching closing brace and semicolon
    # We need to find the closing }; after the start
    brace_count = 0
    in_string = False
    escape_next = False
    end_idx = start_idx + len(start_marker)
    
    # Skip the opening brace
    if html[end_idx] == '{':
        brace_count = 1
        end_idx += 1
    
    # Find matching closing brace
    while end_idx < len(html) and brace_count > 0:
        char = html[end_idx]
        
        if escape_next:
            escape_next = False
            end_idx += 1
            continue
        
        if char == '\\':
            escape_next = True
            end_idx += 1
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
        elif not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
        
        end_idx += 1
    
    # Find the semicolon
    while end_idx < len(html) and html[end_idx] != ';':
        end_idx += 1
    
    if end_idx >= len(html):
        print("Error: Could not find closing '};' for resultsData")
        return
    
    # Replace the resultsData section
    results_json = json.dumps(combined_results, indent=12)
    new_data = f'const resultsData = {results_json};'
    new_html = html[:start_idx] + new_data + html[end_idx + 1:]
    
    # Enable Gemini model card if Google results exist
    if 'google' in all_results:
        # Remove disabled class
        new_html = re.sub(
            r'<div class="model-card gemini disabled"',
            '<div class="model-card gemini"',
            new_html
        )
        # Add onclick handler
        new_html = re.sub(
            r'(<div class="model-card gemini"[^>]*>[\s\S]*?<div class="model-card-header">[\s\S]*?<span class="model-name">Gemini[^<]*</span>[\s\S]*?</div>[\s\S]*?<div class="model-score">)—</div>',
            r'\1' + f"{all_results['google']['score']['overall_score']:.1f}%</div>",
            new_html
        )
        # Update model label
        new_html = re.sub(
            r'(<div class="model-card gemini"[^>]*>[\s\S]*?<div class="model-label">)Coming Soon</div>',
            r'\1Overall Accuracy</div>',
            new_html
        )
        # Add model details if needed
        google_score = all_results['google']['score']
        if '<div class="model-details">' not in new_html.split('model-label">Overall Accuracy</div>')[1].split('</div>')[0]:
            # Find the gemini card and add details
            gemini_match = re.search(r'(<div class="model-card gemini"[^>]*>.*?<div class="model-label">Overall Accuracy</div>)(.*?)(</div>\s*</div>)', new_html, re.DOTALL)
            if gemini_match:
                details = f'''
                    <div class="model-details">
                        <div class="detail-row"><span>Resolution</span><span>{google_score['individual_scores']['resolution_type']:.1f}%</span></div>
                        <div class="detail-row"><span>Monetary</span><span>{google_score['individual_scores']['monetary_average']:.1f}%</span></div>
                        <div class="detail-row"><span>Injunction</span><span>{google_score['individual_scores']['has_injunction']:.1f}%</span></div>
                        <div class="detail-row"><span>Officer Bar</span><span>{google_score['individual_scores']['has_officer_director_bar']:.1f}%</span></div>
                    </div>
                    <div class="model-meta">{len(all_results['google'].get('predictions', []))} cases evaluated</div>'''
                new_html = new_html[:gemini_match.end(2)] + details + new_html[gemini_match.end(2):]
    
    # Write updated file
    with open(cases_html, 'w') as f:
        f.write(new_html)
    
    print(f"\n✓ Updated {cases_html}")
    print(f"  - Added results from {len(all_results)} providers")
    if 'google' in all_results:
        print(f"  - Enabled Gemini model card with {len(all_results['google'].get('predictions', []))} predictions")

if __name__ == '__main__':
    update_cases_html()
