"""
FastAPI HTTP Wrapper for FT-Echo TCP Client
Provides REST API endpoints that use the TCP client library.
"""
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import tempfile
import os
from tcp_client_lib import list_files, get_file, put_file, resume_file

app = FastAPI(title="FT-Echo HTTP API")

# CORS middleware for React frontend
# Allow CORS for frontend. In development we allow all origins to avoid
# preflight failures when the frontend is accessed via the LAN IP.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
TCP_HOST = os.getenv("FT_ECHO_HOST", "localhost")
TCP_PORT = int(os.getenv("FT_ECHO_PORT", "9000"))


@app.get("/api/list")
async def api_list():
    """List files on the TCP server"""
    try:
        files = list_files(TCP_HOST, TCP_PORT)
        return {"ok": True, "files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/get")
async def api_get(file: str = Query(..., description="Filename to download")):
    """Download a file from the TCP server"""
    try:
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Download file
        result = get_file(TCP_HOST, TCP_PORT, file, temp_path)
        
        # Stream file back to client
        def generate():
            with open(temp_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    yield chunk
            # Clean up temp file
            os.unlink(temp_path)
        
        return StreamingResponse(
            generate(),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{file}"',
                "X-SHA256": result['sha']
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/put")
async def api_put(file: UploadFile = File(...)):
    """Upload a file to the TCP server"""
    temp_path = None
    try:
        # Get original filename
        original_filename = file.filename or "uploaded_file"
        
        # Sanitize filename (remove path components for security)
        import re
        safe_filename = os.path.basename(original_filename)
        safe_filename = re.sub(r'[^\w\s.-]', '', safe_filename)  # Remove unsafe chars
        if not safe_filename:
            safe_filename = "uploaded_file"
        
        # Save uploaded file to temporary location with original filename
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, safe_filename)
        
        # Handle filename collisions
        counter = 1
        base_path = temp_path
        while os.path.exists(temp_path):
            name, ext = os.path.splitext(base_path)
            temp_path = f"{name}_{counter}{ext}"
            counter += 1
        
        # Write uploaded content to temp file
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Upload to TCP server (it will use the filename from the path)
        result = put_file(TCP_HOST, TCP_PORT, temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        return {
            "ok": True,
            "filename": safe_filename,
            "sha": result['sha'],
            "size": result['size']
        }
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/resume")
async def api_resume(data: dict):
    """Resume a file transfer"""
    try:
        filename = data.get('file')
        offset = data.get('offset', 0)
        direction = data.get('direction', 'get')
        filepath = data.get('filepath')  # For PUT resume, this is the source file
        
        if not filename:
            raise HTTPException(status_code=400, detail="Missing 'file' parameter")
        
        if direction not in ['get', 'put']:
            raise HTTPException(status_code=400, detail="Direction must be 'get' or 'put'")
        
        result = resume_file(TCP_HOST, TCP_PORT, filename, offset, direction, filepath=filepath)
        
        return {
            "ok": True,
            "sha": result.get('sha'),
            "size": result.get('size')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "FT-Echo HTTP API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

