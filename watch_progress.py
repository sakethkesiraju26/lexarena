#!/usr/bin/env python3
"""Watch evaluation progress with live updates"""

import json
import os
import time
from datetime import datetime

results_file = 'data/processed/evaluation_results_google.json'

print("=" * 70)
print("WATCHING EVALUATION PROGRESS - Live Updates")
print("=" * 70)
print("Press Ctrl+C to stop")
print()

last_count = 0
if os.path.exists(results_file):
    with open(results_file, 'r') as f:
        results = json.load(f)
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    last_count = len(set(p.get('case_id') for p in successful))

start_time = time.time()

while True:
    time.sleep(5)  # Check every 5 seconds
    
    if not os.path.exists(results_file):
        print("Waiting for results file...")
        continue
    
    mtime = os.path.getmtime(results_file)
    age_seconds = time.time() - mtime
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    current_count = len(set(p.get('case_id') for p in successful))
    
    elapsed = time.time() - start_time
    
    if current_count > last_count:
        new_cases = current_count - last_count
        rate = current_count / elapsed if elapsed > 0 else 0
        remaining = 500 - current_count
        eta_seconds = remaining / rate if rate > 0 else 0
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ {current_count}/500 cases ({current_count/500*100:.1f}%)")
        print(f"         +{new_cases} new | File updated {age_seconds:.0f}s ago | ETA: {eta_seconds/60:.1f} min")
        last_count = current_count
    elif age_seconds < 30:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing... ({current_count}/500) - File updated {age_seconds:.0f}s ago")
    
    if current_count >= 500:
        print("\n" + "=" * 70)
        print("✓✓✓ ALL 500 CASES COMPLETE! ✓✓✓")
        print("=" * 70)
        break
