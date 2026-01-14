#!/bin/bash
# Watch the log file for live progress updates

cd "$(dirname "$0")"

echo "Watching google_eval_fresh.log for live progress..."
echo "Press Ctrl+C to stop"
echo ""

tail -f google_eval_fresh.log | grep --line-buffered -E "Progress:|Running evaluation|cases|Evaluation complete|Error|error" | while read line; do
    echo "[$(date +%H:%M:%S)] $line"
done
