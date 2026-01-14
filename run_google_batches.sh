#!/bin/bash
# Run Google evaluation in 10 batches of 50 cases each

cd "$(dirname "$0")"

# Check for API key in environment
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable not set"
    echo "Please set it before running this script:"
    echo "  export GOOGLE_API_KEY=your_key_here"
    exit 1
fi

echo "======================================================================"
echo "Running Google Gemini Evaluation in 10 Batches of 50 Cases"
echo "======================================================================"
echo ""

# Get already evaluated cases
EVALUATED=$(python3 -c "
import json
with open('data/processed/evaluation_results_google.json', 'r') as f:
    results = json.load(f)
preds = [p for p in results.get('predictions', []) if p.get('success')]
evaluated = set(p.get('case_id') for p in preds)
print(len(evaluated))
" 2>/dev/null)

START_SKIP=$EVALUATED
BATCH_SIZE=50
NUM_BATCHES=10

echo "Starting from case: $START_SKIP"
echo "Batch size: $BATCH_SIZE"
echo "Number of batches: $NUM_BATCHES"
echo ""

for i in $(seq 1 $NUM_BATCHES); do
    SKIP=$((START_SKIP + (i - 1) * BATCH_SIZE))
    
    echo "======================================================================"
    echo "Batch $i/$NUM_BATCHES: Cases $SKIP to $((SKIP + BATCH_SIZE - 1))"
    echo "======================================================================"
    
    python3 run_evaluation.py \
        --evaluate \
        --provider google \
        --model gemini-3-flash-preview \
        --save-results \
        --append-results \
        --skip-cases $SKIP \
        --max-eval-cases $BATCH_SIZE
    
    if [ $? -ne 0 ]; then
        echo "Error in batch $i. Stopping."
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
    echo "Progress: $CURRENT/500 cases evaluated"
    echo ""
    
    # Small delay between batches
    sleep 2
done

echo "======================================================================"
echo "✓ All batches complete!"
echo "======================================================================"
echo ""
echo "Updating HTML..."
python3 finalize_google_evaluation.py

echo ""
echo "✓ Evaluation complete and HTML updated!"
