#!/bin/bash
# Run remaining batches: 150->200, 200->250, 250->300, 300->350, 350->400, 400->450, 450->500

cd "$(dirname "$0")"

# Check for API key in environment
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable not set"
    echo "Please set it before running this script:"
    echo "  export GOOGLE_API_KEY=your_key_here"
    exit 1
fi

echo "Running remaining 4 batches (300->500) with LIVE updates"
echo ""

for skip in 300 350 400 450; do
    batch_num=$(( (skip - 150) / 50 + 1 ))
    echo "============================================================"
    echo "Batch $batch_num/10: Processing & Saving cases $skip to $((skip + 49))"
    echo "============================================================"
    
    python3 run_evaluation.py \
        --evaluate \
        --provider google \
        --model gemini-3-flash-preview \
        --save-results \
        --append-results \
        --skip-cases $skip \
        --max-eval-cases 50
    
    if [ $? -ne 0 ]; then
        echo "Error in batch. Stopping."
        exit 1
    fi
    
    # Check progress
    CURRENT=$(python3 -c "
import json
with open('data/processed/evaluation_results_google.json', 'r') as f:
    results = json.load(f)
preds = [p for p in results.get('predictions', []) if p.get('success')]
unique = len(set(p.get('case_id') for p in preds))
print(unique)
" 2>/dev/null)
    
    echo ""
    echo "✓ Progress: $CURRENT/500 cases saved"
    echo ""
    sleep 2
done

echo "============================================================"
echo "✓ All batches complete! Updating HTML..."
echo "============================================================"
python3 finalize_google_evaluation.py

echo ""
echo "✓ Done! HTML updated with all 500 Google cases!"
