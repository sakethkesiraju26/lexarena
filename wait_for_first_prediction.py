#!/usr/bin/env python3
"""
Monitor and notify when first new prediction is completed.
"""

import json
import os
import time
from datetime import datetime
from collections import defaultdict

def get_current_case_count(results_file='data/processed/evaluation_results_google.json'):
    """Get current number of unique cases evaluated."""
    if not os.path.exists(results_file):
        return 0, set()
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    predictions = results.get('predictions', [])
    successful = [p for p in predictions if p.get('success')]
    unique_cases = set(p.get('case_id') for p in successful)
    
    return len(unique_cases), unique_cases

def monitor_for_new_prediction():
    """Monitor until first new prediction appears."""
    results_file = 'data/processed/evaluation_results_google.json'
    
    print("=" * 70)
    print("Monitoring for First New Prediction")
    print("=" * 70)
    
    # Get baseline
    initial_count, initial_cases = get_current_case_count(results_file)
    print(f"Initial state: {initial_count} unique cases")
    print(f"Monitoring for new predictions...")
    print(f"Will notify when count increases or file is updated")
    print()
    
    last_mtime = os.path.getmtime(results_file) if os.path.exists(results_file) else 0
    check_count = 0
    
    try:
        while True:
            check_count += 1
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Check if file was modified
            if os.path.exists(results_file):
                current_mtime = os.path.getmtime(results_file)
                file_modified = current_mtime > last_mtime
                
                if file_modified:
                    current_count, current_cases = get_current_case_count(results_file)
                    new_cases = current_cases - initial_cases
                    
                    if new_cases or current_count > initial_count:
                        print()
                        print("=" * 70)
                        print("🎉 FIRST NEW PREDICTION DETECTED!")
                        print("=" * 70)
                        print(f"Time: {current_time}")
                        print(f"Previous count: {initial_count}")
                        print(f"Current count: {current_count}")
                        print(f"New cases: {len(new_cases)}")
                        if new_cases:
                            print(f"First new case ID: {sorted(new_cases)[0]}")
                        print()
                        print("✓ Evaluation is working! New predictions are being saved!")
                        print("=" * 70)
                        return True
                    
                    last_mtime = current_mtime
                    print(f"[{current_time}] File modified but no new cases yet (check #{check_count})")
                else:
                    if check_count % 12 == 0:  # Every minute
                        print(f"[{current_time}] Still monitoring... (check #{check_count}, file unchanged)")
            else:
                print(f"[{current_time}] Results file doesn't exist yet (check #{check_count})")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        return False

if __name__ == '__main__':
    monitor_for_new_prediction()
