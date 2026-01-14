#!/bin/bash
# Script to run Google Gemini evaluation for all 500 cases
# Usage: ./run_google_evaluation.sh [API_KEY]
# Or set GOOGLE_API_KEY environment variable

set -e

cd "$(dirname "$0")"

# Check if API key is provided as argument or in environment
if [ -n "$1" ]; then
    export GOOGLE_API_KEY="$1"
elif [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY not set"
    echo "Usage: $0 [API_KEY]"
    echo "Or set GOOGLE_API_KEY environment variable"
    exit 1
fi

echo "Running Google Gemini evaluation for all 500 cases..."
echo "Using append mode to preserve existing 150 evaluations..."
echo ""

python3 run_evaluation.py --evaluate \
  --provider google \
  --model gemini-3-flash-preview \
  --save-results \
  --append-results \
  --max-eval-cases 500

echo ""
echo "Evaluation complete! Results saved to data/processed/evaluation_results_google.json"
