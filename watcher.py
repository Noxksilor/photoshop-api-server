#!/usr/bin/env python3
"""
Watcher script for Photoshop API Server tests

Runs run_all.ps1 repeatedly, collects logs, and stops after N successful runs
"""

import os
import subprocess
import time
import datetime
import json
import shutil
from pathlib import Path

# Configuration
AUTO_COMMIT = False  # Set to True to automatically commit and push logs
INTERVAL_SECONDS = 60  # Time to wait between runs
SUCCESS_THRESHOLD = 3  # Number of consecutive successful runs to stop

def main():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    consecutive_success = 0
    run_count = 0
    
    while consecutive_success < SUCCESS_THRESHOLD:
        run_count += 1
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = logs_dir / f"run-{timestamp}"
        run_dir.mkdir()
        
        print(f"[{timestamp}] Run {run_count}: Starting...")
        
        try:
            # Run run_all.ps1
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", "run_all.ps1"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            # Save full output
            output_file = run_dir / "run_all_output.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
            
            # Parse output to determine status
            status = "OK"
            error_message = None
            input_path = None
            result_path = r"C:\ps_jobs\api_tests\test_result.png"
            result_exists = os.path.exists(result_path)
            server_return_code = result.returncode
            
            # Extract input path from config if available
            config_path = Path("config.json")
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        input_path = config.get("default_input", None)
                except Exception as e:
                    print(f"Error reading config: {e}")
            
            # Determine status from output
            output = result.stdout + result.stderr
            if "ERROR:" in output or result.returncode != 0 or not result_exists:
                status = "ERROR"
                # Extract error message
                error_lines = []
                for line in output.splitlines():
                    if line.strip().startswith("ERROR:"):
                        error_lines.append(line.strip())
                error_message = "\n".join(error_lines) or "Unknown error"
            
            # Save summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": status,
                "error_message": error_message,
                "input_path": input_path,
                "result_path": result_path,
                "result_exists": result_exists,
                "server_return_code": server_return_code
            }
            
            with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            # Extract Photoshop error if present
            if "Photoshop execution failed:" in output:
                photoshop_error = []
                for line in output.splitlines():
                    if "Photoshop execution failed:" in line:
                        photoshop_error.append(line)
                    elif len(photoshop_error) > 0 and line.strip():
                        photoshop_error.append(line)
                if photoshop_error:
                    with open(run_dir / "photoshop_error.txt", "w", encoding="utf-8") as f:
                        f.write("\n".join(photoshop_error))
            
            # Update success counter
            if status == "OK":
                consecutive_success += 1
                print(f"[{timestamp}] Run {run_count}: OK (consecutive: {consecutive_success}/{SUCCESS_THRESHOLD})")
            else:
                consecutive_success = 0
                print(f"[{timestamp}] Run {run_count}: ERROR - {error_message}")
            
            # Auto commit if enabled and we have logs to commit
            if AUTO_COMMIT:
                try:
                    subprocess.run(["git", "add", str(logs_dir)], check=True)
                    subprocess.run(["git", "commit", "-m", f"Watcher run at {timestamp}"], check=True)
                    subprocess.run(["git", "push"], check=True)
                except Exception as e:
                    print(f"Error committing changes: {e}")
            
            # Wait before next run if we haven't reached success threshold
            if consecutive_success < SUCCESS_THRESHOLD:
                print(f"Waiting {INTERVAL_SECONDS} seconds before next run...")
                time.sleep(INTERVAL_SECONDS)
                
        except subprocess.TimeoutExpired:
            status = "ERROR"
            error_message = "Timeout - run exceeded 10 minutes"
            print(f"[{timestamp}] Run {run_count}: {status} - {error_message}")
            consecutive_success = 0
            
            # Save timeout summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": status,
                "error_message": error_message,
                "input_path": None,
                "result_path": result_path,
                "result_exists": False,
                "server_return_code": -1
            }
            
            with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
            time.sleep(INTERVAL_SECONDS)
            
        except Exception as e:
            status = "ERROR"
            error_message = str(e)
            print(f"[{timestamp}] Run {run_count}: {status} - {error_message}")
            consecutive_success = 0
            
            # Save exception summary
            summary = {
                "timestamp": datetime.datetime.now().isoformat(),
                "status": status,
                "error_message": error_message,
                "input_path": None,
                "result_path": result_path,
                "result_exists": False,
                "server_return_code": -1
            }
            
            with open(run_dir / "summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
                
            time.sleep(INTERVAL_SECONDS)
    
    print(f"Successfully completed {SUCCESS_THRESHOLD} consecutive runs - stopping watcher")

if __name__ == "__main__":
    main()
