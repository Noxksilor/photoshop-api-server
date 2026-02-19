import os
import json
import uuid
import subprocess
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Photoshop API Server")

# Load configuration
def load_config():
    config_file = "config.json"
    example_config_file = "config.example.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")
    
    if os.path.exists(example_config_file):
        try:
            with open(example_config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config.example.json: {e}")
    
    raise Exception("No configuration file found")

config = load_config()

class ScriptRequest(BaseModel):
    script_text: str
    output_name: Optional[str] = None

@app.post("/run_script")
async def run_script(request: ScriptRequest):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(config["work_dir"], job_id)
    
    # Create job directory
    try:
        os.makedirs(job_dir, exist_ok=True)
    except Exception as e:
        return {"ok": False, "error": f"Failed to create job directory: {str(e)}"}
    
    # Determine output filename
    output_name = request.output_name or config["default_output_name"]
    output_path = os.path.join(job_dir, output_name)
    
    # Prepare JSX script
    script_text = request.script_text
    # Replace placeholders if present
    script_text = script_text.replace("{{INPUT_PATH}}", config["default_input"])
    script_text = script_text.replace("{{OUTPUT_PATH}}", output_path)
    
    script_path = os.path.join(job_dir, "script.jsx")
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)
    except Exception as e:
        return {"ok": False, "error": f"Failed to save script: {str(e)}"}
    
    # Run Photoshop with the script
    photoshop_cmd = f'"{config["photoshop_path"]}" -r "{script_path}"'
    try:
        process = subprocess.Popen(
            photoshop_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for process to complete or timeout
        start_time = time.time()
        while process.poll() is None:
            time.sleep(1)
            if time.time() - start_time > config["max_execution_seconds"]:
                process.kill()
                return {"ok": False, "error": "Execution timed out"}
        
        # Check for errors in Photoshop output
        stdout, stderr = process.communicate()
        stderr_text = stderr.decode("utf-8", errors="replace")
        if process.returncode != 0:
            return {"ok": False, "error": f"Photoshop execution failed: {stderr_text}"}
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to run Photoshop: {str(e)}"}
    
    # Check if output file exists
    if not os.path.exists(output_path):
        return {"ok": False, "error": "Output file not generated"}
    
    # Return the output file as FileResponse
    return FileResponse(
        path=output_path,
        filename=output_name,
        media_type="image/png"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
