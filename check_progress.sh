#!/bin/bash
# Quick progress check script

cd "$(dirname "$0")"

python3 -c "
import json
import os
import subprocess
from datetime import datetime

print('=' * 70)
print('Google Gemini Evaluation - Quick Status Check')
print('=' * 70)
print(f'Time: {datetime.now().strftime(\"%H:%M:%S\")}\n')

# Check process
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
# Better pattern matching
running = False
for line in result.stdout.split('\n'):
    if 'run_evaluation.py' in line and 'google' in line and 'grep' not in line:
        running = True
        # Extract PID
        parts = line.split()
        if len(parts) > 1:
            print(f'Process: ✓ RUNNING (PID: {parts[1]})')
            break
if not running:
    print(f'Process: ✗ STOPPED')

# Check log progress
log_file = 'google_eval_fresh.log'
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        lines = f.readlines()
    progress_lines = [l for l in lines if 'Progress:' in l]
    if progress_lines:
        last = progress_lines[-1]
        import re
        match = re.search(r'Progress:\s*(\d+)/(\d+)', last)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            pct = current/total*100
            print(f'Log Progress: {current}/{total} cases ({pct:.1f}%)')
            # Show progress bar
            bar_width = 50
            filled = int(bar_width * current / total)
            bar = '█' * filled + '░' * (bar_width - filled)
            print(f'            [{bar}] {pct:.1f}%')
    else:
        print('Log Progress: Starting up...')
else:
    print('Log Progress: No log file yet')

# Check results file
results_file = 'data/processed/evaluation_results_google.json'
if os.path.exists(results_file):
    mtime = os.path.getmtime(results_file)
    mod_time = datetime.fromtimestamp(mtime)
    age = (datetime.now() - mod_time).total_seconds()
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    unique = len(set(p.get('case_id') for p in successful))
    
    print(f'\nResults File: {unique}/500 cases ({unique/500*100:.1f}%)')
    if age < 60:
        print(f'Last Modified: {mod_time.strftime(\"%H:%M:%S\")} ({age:.0f}s ago) ⬆ UPDATING!')
    else:
        print(f'Last Modified: {mod_time.strftime(\"%H:%M:%S\")} ({age/60:.1f}m ago)')
    
    if results.get('score', {}).get('overall_score'):
        print(f'Overall Score: {results[\"score\"][\"overall_score\"]:.1f}%')
else:
    print('\nResults File: Will be created when evaluation completes')

print('=' * 70)
"
