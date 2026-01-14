#!/bin/bash
# Simple script to update HTML when evaluation completes

cd "$(dirname "$0")"

echo "Waiting for evaluation to complete..."
echo "Will update cases.html automatically when done."
echo ""

# Wait for file to be updated (when evaluation completes)
while true; do
    # Check if file was updated in last 2 minutes
    if [ -f "data/processed/evaluation_results_google.json" ]; then
        FILE_AGE=$(find data/processed/evaluation_results_google.json -mmin -2 2>/dev/null)
        if [ ! -z "$FILE_AGE" ]; then
            # Check if we have 500 cases
            COUNT=$(python3 -c "
import json
with open('data/processed/evaluation_results_google.json', 'r') as f:
    data = json.load(f)
preds = [p for p in data.get('predictions', []) if p.get('success')]
unique = len(set(p.get('case_id') for p in preds))
print(unique)
" 2>/dev/null)
            
            if [ "$COUNT" -ge 500 ]; then
                echo "Evaluation complete! Updating HTML..."
                python3 generate_viewer.py
                echo ""
                echo "✓ HTML updated with Google results!"
                echo "✓ All 500 cases evaluated!"
                exit 0
            fi
        fi
    fi
    
    # Check if process is still running
    if ! ps -p 18172 > /dev/null 2>&1; then
        echo "Process completed. Updating HTML..."
        python3 generate_viewer.py
        echo ""
        echo "✓ HTML updated!"
        exit 0
    fi
    
    sleep 30
done
