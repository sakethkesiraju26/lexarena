#!/usr/bin/env python3
"""Embed Claude evaluation results into cases.html"""

import json
import re

def main():
    # Read Claude results
    with open('data/processed/evaluation_results_anthropic.json', 'r') as f:
        claude_data = json.load(f)
    
    # Read cases.html
    with open('cases.html', 'r') as f:
        html = f.read()
    
    # First, remove any existing claudeData blocks
    # Pattern matches from "// Claude evaluation data" to before "function formatMoney"
    pattern = r'        // Claude evaluation data\n        const claudeData = \{[\s\S]*?\};\s*\n\s*// Create lookup map for Claude predictions by case_id\n        const claudePredictions = \{\};\n        claudeData\.predictions\.forEach\(p => \{\n            claudePredictions\[p\.case_id\] = p;\n        \}\);\n\n'
    html = re.sub(pattern, '', html)
    
    # Serialize Claude data
    claude_json = json.dumps(claude_data, indent=4, ensure_ascii=False)
    
    # Find where to insert (after getScoreClass function, before formatMoney)
    insert_marker = "        function formatMoney(amount) {"
    claude_insert = f"""        // Claude evaluation data
        const claudeData = {claude_json};
        
        // Create lookup map for Claude predictions by case_id
        const claudePredictions = {{}};
        claudeData.predictions.forEach(p => {{
            claudePredictions[p.case_id] = p;
        }});

        {insert_marker}"""
    
    # Replace
    new_html = html.replace(insert_marker, claude_insert)
    
    # Write back
    with open('cases.html', 'w') as f:
        f.write(new_html)
    
    print(f"✓ Embedded Claude data: {len(claude_data['predictions'])} predictions")
    print(f"✓ Updated cases.html")

if __name__ == '__main__':
    main()
