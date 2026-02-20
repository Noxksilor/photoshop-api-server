import os
import json
import uuid
import subprocess
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from PIL import Image, ImageOps

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
    
    # Run backend command instead of Photoshop
    backend_command = config.get("backend_command", "python C:\\ps_jobs\\job_0001\\orchestrator.py")
    backend_output_path = config.get("backend_output_path", "C:\\ps_jobs\\job_0001\\out\\result.png")
    backend_log_path = os.path.join(job_dir, "backend_log.txt")
    
    try:
        # Check backend directory and executable exist
        backend_dir = os.path.dirname(os.path.abspath(backend_command.split()[-1]))
        backend_exe = os.path.abspath(backend_command.split()[-1])
        if not os.path.exists(backend_dir):
            return {"ok": False, "error": f"Backend directory not found: {backend_dir}"}
        if not os.path.exists(backend_exe):
            return {"ok": False, "error": f"Backend executable not found: {backend_exe}"}
        
        # Run backend
        result = subprocess.run(
            backend_command,
            shell=True,
            cwd=os.path.dirname(backend_exe),
            timeout=config["max_execution_seconds"],
            check=False,
            capture_output=True,
            text=True
        )
        
        # Save backend log
        with open(backend_log_path, "w", encoding="utf-8") as f:
            f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}")
        
        # Check if backend output file exists
        if not os.path.exists(backend_output_path):
            log_content = ""
            if os.path.exists(backend_log_path):
                with open(backend_log_path, "r", encoding="utf-8") as f:
                    log_content = f.read().strip()
            return {
                "ok": False,
                "error": "backend_output_not_found",
                "backend_log": log_content[:1000]  # Truncate log
            }
        
        # Copy backend output to job directory for return
        import shutil
        shutil.copy(backend_output_path, output_path)
        
    except Exception as e:
        return {"ok": False, "error": f"Failed to run backend: {str(e)}"}
    
    # Return the output file as FileResponse
    return FileResponse(
        path=output_path,
        filename=output_name,
        media_type="image/png"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
