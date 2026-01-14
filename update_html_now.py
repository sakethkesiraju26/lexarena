#!/usr/bin/env python3
import json
import re
import sys
sys.path.insert(0, 'src')
from generate_viewer import load_all_provider_results

# Load all results
all_results = load_all_provider_results()

# Create combined results
primary_provider = 'openai' if 'openai' in all_results else list(all_results.keys())[0]
combined_results = all_results[primary_provider].copy()
combined_results['all_providers'] = all_results

# Create JSON
results_json = json.dumps(combined_results, indent=12)

# Load HTML
with open('cases.html', 'r') as f:
    content = f.read()

# Find start
start_marker = 'const resultsData = '
start_idx = content.find(start_marker)

if start_idx == -1:
    print("Error: Could not find start marker")
    sys.exit(1)

# Find closing }; - search in chunks
search_start = start_idx + len(start_marker)
search_end = min(start_idx + 3000000, len(content))  # Search up to 3MB
search_region = content[search_start:search_end]

# Find all }; occurrences
semicolon_positions = []
pos = 0
while True:
    pos = search_region.find('};', pos)
    if pos == -1:
        break
    semicolon_positions.append(pos)
    pos += 1

if not semicolon_positions:
    print("Error: Could not find closing };")
    sys.exit(1)

# Use a position that's far enough (the JSON is huge, at least 50k chars)
valid_positions = [p for p in semicolon_positions if p > 50000]
if valid_positions:
    end_pos = start_idx + len(start_marker) + valid_positions[0] + 2
else:
    # Fallback: use the last one
    end_pos = start_idx + len(start_marker) + semicolon_positions[-1] + 2

# Replace
new_data = f'const resultsData = {results_json};'
new_html = content[:start_idx] + new_data + content[end_pos:]

# Enable Gemini card
if 'google' in all_results:
    new_html = re.sub(
        r'<div class="model-card gemini disabled"',
        '<div class="model-card gemini"',
        new_html
    )
    if 'onclick="selectModel(\'gemini\')"' not in new_html:
        new_html = re.sub(
            r'(<div class="model-card gemini"[^>]*)>',
            r'\1 onclick="selectModel(\'gemini\')">',
            new_html
        )

# Write
with open('cases.html', 'w') as f:
    f.write(new_html)

google_count = len(set(p.get('case_id') for p in all_results.get('google', {}).get('predictions', []) if p.get('success')))

print(f"✓ Updated cases.html")
print(f"  - {len(all_results)} providers")
print(f"  - Google: {google_count} cases")
print(f"  - Gemini card enabled")
