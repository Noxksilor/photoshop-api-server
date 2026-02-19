import os
import json
import requests

def main():
    # Check config.json exists
    if not os.path.exists("config.json"):
        print("ERROR: Missing config.json, please copy from config.example.json")
        return 1
    
    # Load config
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Check input file exists
    input_path = config.get("default_input")
    if not input_path or not os.path.exists(input_path):
        print(f"ERROR: Input file not found at {input_path}, please put a PNG there.")
        return 1
    
    # Check example_script.jsx exists
    if not os.path.exists("example_script.jsx"):
        print("ERROR: Missing example_script.jsx in project root")
        return 1
    
    # Read example script
    with open("example_script.jsx", "r", encoding="utf-8") as f:
        script_text = f.read()
    
    # Create output directory if doesn't exist
    output_dir = r"C:\ps_jobs\api_tests"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "test_result.png")
    
    # Send request
    try:
        response = requests.post(
            "http://localhost:8000/run_script",
            json={
                "script_text": script_text,
                "output_name": "test_result.png"
            },
            timeout=300
        )
        
        if response.status_code == 200 and response.headers.get("content-type") == "image/png":
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"OK: test_result.png saved to {output_path}")
            return 0
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("detail", "Unknown error")
            except:
                error_msg = response.text
            print(f"ERROR: {error_msg}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is server.py running on http://localhost:8000?")
        return 1
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    os._exit(exit_code)
