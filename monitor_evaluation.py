#!/usr/bin/env python3
"""
Live monitoring of Google evaluation progress
"""

import json
import os
import time
import subprocess
from datetime import datetime

def get_process_info():
    """Get info about running evaluation process."""
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        lines = result.stdout.split('\n')
        for line in lines:
            if 'run_evaluation' in line and 'google' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) > 1:
                    return {
                        'pid': parts[1],
                        'running': True,
                        'command': ' '.join(parts[10:])
                    }
    except:
        pass
    return {'running': False}

def get_log_progress(log_file='google_eval_fresh.log'):
    """Extract progress from log file."""
    if not os.path.exists(log_file):
        return None
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Look for progress indicators
        progress_lines = [l for l in lines if 'Progress:' in l]
        if progress_lines:
            last_progress = progress_lines[-1]
            # Extract numbers like "Progress: 50/500"
            import re
            match = re.search(r'Progress:\s*(\d+)/(\d+)', last_progress)
            if match:
                return {
                    'current': int(match.group(1)),
                    'total': int(match.group(2)),
                    'percent': int(match.group(1)) / int(match.group(2)) * 100
                }
    except:
        pass
    return None

def get_file_status(results_file='data/processed/evaluation_results_google.json'):
    """Get status from results file."""
    if not os.path.exists(results_file):
        return {
            'exists': False,
            'cases': 0,
            'last_modified': None
        }
    
    try:
        mtime = os.path.getmtime(results_file)
        mod_time = datetime.fromtimestamp(mtime)
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        predictions = results.get('predictions', [])
        successful = [p for p in predictions if p.get('success')]
        unique_cases = len(set(p.get('case_id') for p in successful))
        
        return {
            'exists': True,
            'cases': unique_cases,
            'total_predictions': len(predictions),
            'last_modified': mod_time,
            'age_seconds': (datetime.now() - mod_time).total_seconds(),
            'overall_score': results.get('score', {}).get('overall_score', 0)
        }
    except Exception as e:
        return {
            'exists': True,
            'error': str(e)
        }

def monitor_live():
    """Monitor evaluation with live updates."""
    print("=" * 70)
    print("Google Gemini Evaluation - Live Monitor")
    print("=" * 70)
    print("Press Ctrl+C to stop monitoring\n")
    
    last_file_cases = 0
    last_log_progress = None
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print("=" * 70)
            print("Google Gemini Evaluation - Live Monitor")
            print("=" * 70)
            print(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
            
            # Check process
            process_info = get_process_info()
            if process_info.get('running'):
                print(f"✓ Process Status: RUNNING (PID: {process_info['pid']})")
            else:
                print("⚠ Process Status: NOT RUNNING")
            
            # Check log progress
            log_progress = get_log_progress()
            if log_progress:
                print(f"\n📊 Log Progress: {log_progress['current']}/{log_progress['total']} cases ({log_progress['percent']:.1f}%)")
                if last_log_progress and log_progress['current'] > last_log_progress['current']:
                    print(f"   ⬆ Progress updated! (+{log_progress['current'] - last_log_progress['current']} cases)")
                last_log_progress = log_progress
            else:
                print("\n📊 Log Progress: No progress data yet")
            
            # Check file status
            file_status = get_file_status()
            if file_status.get('exists'):
                cases = file_status.get('cases', 0)
                age = file_status.get('age_seconds', 0)
                
                print(f"\n📁 Results File Status:")
                print(f"   Cases evaluated: {cases}/500 ({cases/500*100:.1f}%)")
                print(f"   Total predictions: {file_status.get('total_predictions', 0)}")
                
                if age < 60:
                    print(f"   Last modified: {file_status['last_modified'].strftime('%H:%M:%S')} ({age:.0f}s ago) ⬆ UPDATING!")
                elif age < 300:
                    print(f"   Last modified: {file_status['last_modified'].strftime('%H:%M:%S')} ({age/60:.1f}m ago)")
                else:
                    print(f"   Last modified: {file_status['last_modified'].strftime('%H:%M:%S')} ({age/60:.1f}m ago) - Will update when complete")
                
                if cases > last_file_cases:
                    print(f"   ⬆ NEW CASES ADDED! (+{cases - last_file_cases} cases)")
                    last_file_cases = cases
                
                if file_status.get('overall_score'):
                    print(f"   Overall Score: {file_status['overall_score']:.1f}%")
            else:
                print(f"\n📁 Results File: Not created yet (will be created when evaluation completes)")
            
            # Show recent log output
            print(f"\n📝 Recent Log Output (last 5 lines):")
            if os.path.exists('google_eval_fresh.log'):
                try:
                    with open('google_eval_fresh.log', 'r') as f:
                        lines = f.readlines()
                        for line in lines[-5:]:
                            print(f"   {line.rstrip()}")
                except:
                    print("   (Could not read log)")
            else:
                print("   (No log file yet)")
            
            print("\n" + "=" * 70)
            print("Refreshing in 5 seconds... (Ctrl+C to stop)")
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == '__main__':
    monitor_live()
