#!/bin/bash
# Monitor and notify when first new prediction is detected

cd "$(dirname "$0")"

echo "======================================================================"
echo "Monitoring for First New Prediction"
echo "======================================================================"
echo ""

# Get initial state
INITIAL_COUNT=$(python3 -c "
import json
import os
f = 'data/processed/evaluation_results_google.json'
if os.path.exists(f):
    with open(f, 'r') as file:
        data = json.load(file)
    preds = [p for p in data.get('predictions', []) if p.get('success')]
    print(len(set(p.get('case_id') for p in preds)))
else:
    print(0)
" 2>/dev/null)

echo "Initial case count: $INITIAL_COUNT"
echo "Monitoring for changes..."
echo ""

# Monitor loop
while true; do
    # Check results file
    CURRENT_COUNT=$(python3 -c "
import json
import os
f = 'data/processed/evaluation_results_google.json'
if os.path.exists(f):
    with open(f, 'r') as file:
        data = json.load(file)
    preds = [p for p in data.get('predictions', []) if p.get('success')]
    print(len(set(p.get('case_id') for p in preds)))
else:
    print(0)
" 2>/dev/null)
    
    # Check log for progress
    if [ -f "google_eval_output.log" ]; then
        PROGRESS=$(tail -100 google_eval_output.log | grep -o "Progress: [0-9]*/[0-9]*" | tail -1)
        if [ ! -z "$PROGRESS" ]; then
            echo "[$(date +%H:%M:%S)] Log shows: $PROGRESS"
        fi
    fi
    
    # Check if count increased
    if [ "$CURRENT_COUNT" -gt "$INITIAL_COUNT" ]; then
        echo ""
        echo "======================================================================"
        echo "🎉 FIRST NEW PREDICTION DETECTED!"
        echo "======================================================================"
        echo "Time: $(date +%H:%M:%S)"
        echo "Previous count: $INITIAL_COUNT"
        echo "Current count: $CURRENT_COUNT"
        echo "New predictions: $((CURRENT_COUNT - INITIAL_COUNT))"
        echo ""
        echo "✓ Evaluation is working! New predictions detected!"
        echo "======================================================================"
        # Make a sound notification (if available)
        if command -v say >/dev/null 2>&1; then
            say "First new prediction detected"
        fi
        exit 0
    fi
    
    # Check if file was recently modified (within last 2 minutes)
    if [ -f "data/processed/evaluation_results_google.json" ]; then
        FILE_AGE=$(find data/processed/evaluation_results_google.json -mmin -2 2>/dev/null)
        if [ ! -z "$FILE_AGE" ]; then
            echo "[$(date +%H:%M:%S)] ⚠ File was recently modified! Checking for new cases..."
        fi
    fi
    
    sleep 10
done
