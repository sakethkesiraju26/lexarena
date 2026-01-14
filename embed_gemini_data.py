#!/usr/bin/env python3
"""Embed Gemini evaluation results into cases.html"""

import json
import re

def main():
    # Read Gemini results
    with open('data/processed/evaluation_results_google.json', 'r') as f:
        gemini_data = json.load(f)
    
    # Read cases.html
    with open('cases.html', 'r') as f:
        html = f.read()
    
    # First, remove any existing geminiData blocks
    # Pattern matches from "// Gemini evaluation data" to before "function formatMoney" or similar
    pattern = r'        // Gemini evaluation data\n        const geminiData = \{[\s\S]*?\};\s*\n\s*// Create lookup map for Gemini predictions by case_id\n        const geminiPredictions = \{\};\n        geminiData\.predictions\.forEach\(p => \{\n            geminiPredictions\[p\.case_id\] = p;\n        \}\);\n\n'
    html = re.sub(pattern, '', html)
    
    # Serialize Gemini data
    gemini_json = json.dumps(gemini_data, indent=4, ensure_ascii=False)
    
    # Find where to insert (after claudeData if it exists, or after getScoreClass function, before formatMoney)
    # Try to find after claudeData first
    if 'const claudePredictions = {};' in html:
        insert_marker = "        function formatMoney(amount) {"
        gemini_insert = f"""        // Gemini evaluation data
        const geminiData = {gemini_json};
        
        // Create lookup map for Gemini predictions by case_id
        const geminiPredictions = {{}};
        geminiData.predictions.forEach(p => {{
            geminiPredictions[p.case_id] = p;
        }});

        {insert_marker}"""
    else:
        # If no claudeData, insert after getScoreClass
        insert_marker = "        function formatMoney(amount) {"
        gemini_insert = f"""        // Gemini evaluation data
        const geminiData = {gemini_json};
        
        // Create lookup map for Gemini predictions by case_id
        const geminiPredictions = {{}};
        geminiData.predictions.forEach(p => {{
            geminiPredictions[p.case_id] = p;
        }});

        {insert_marker}"""
    
    # Replace
    new_html = html.replace(insert_marker, gemini_insert)
    
    # Also enable the Gemini model card (remove disabled class)
    new_html = re.sub(
        r'<div class="model-card gemini disabled"',
        '<div class="model-card gemini"',
        new_html
    )
    
    # Update Gemini card with actual score if available
    if 'score' in gemini_data and 'overall_score' in gemini_data['score']:
        overall_score = gemini_data['score']['overall_score']
        total_cases = gemini_data['score'].get('scorable_counts', {}).get('total_cases', 0)
        
        # Find and update Gemini card score
        gemini_card_pattern = r'(<div class="model-card gemini[^>]*>[\s\S]*?<div class="model-score">)[^<]*(</div>)'
        def replace_gemini_score(match):
            return match.group(1) + f"{overall_score:.1f}%" + match.group(2)
        
        new_html = re.sub(gemini_card_pattern, replace_gemini_score, new_html, count=1)
        
        # Update "Coming Soon" label
        new_html = re.sub(
            r'(<div class="model-card gemini[^>]*>[\s\S]*?<div class="model-label">)Coming Soon(</div>)',
            r'\1Overall Accuracy\2',
            new_html,
            count=1
        )
        
        # Add model meta with case count
        if '<div class="model-meta">' not in new_html.split('model-card gemini')[1].split('</div>')[0]:
            new_html = re.sub(
                r'(<div class="model-card gemini[^>]*>[\s\S]*?</div>\s*</div>\s*</div>)',
                f'\\1\n                    <div class="model-meta">{total_cases} cases evaluated</div>',
                new_html,
                count=1
            )
    
    # Write back
    with open('cases.html', 'w') as f:
        f.write(new_html)
    
    print(f"✓ Embedded Gemini data: {len(gemini_data['predictions'])} predictions")
    print(f"✓ Enabled Gemini model card in cases.html")
    print(f"✓ Updated cases.html")

if __name__ == '__main__':
    main()
