import os
import shutil
from uuid import uuid4
from pathlib import Path
import replicate
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Setup folders
UPLOAD_VIDEO_FOLDER = "uploads/videos/"
Path(UPLOAD_VIDEO_FOLDER).mkdir(parents=True, exist_ok=True)


@app.post("/generate-video")
async def generate_video(
    file: UploadFile = File(...),
    dot_size: int = Form(4),          # Default: 4 (bisa diubah via form-data)
    threshold: int = Form(128),        # Default: 128 (range 0-255)
    inverse: bool = Form(False)        # Default: False
):
    # Validasi file
    if not file.filename.lower().endswith((".mp4", ".mov", ".avi")):
        raise HTTPException(400, "Only MP4/MOV/AVI files are allowed.")

    # Validasi parameter
    if dot_size < 1 or dot_size > 10:
        raise HTTPException(400, "dot_size must be between 1-10")
    if threshold < 0 or threshold > 255:
        raise HTTPException(400, "threshold must be between 0-255")

    temp_id = uuid4().hex
    temp_path = f"temp_{temp_id}_{file.filename}"

    try:
        # Simpan file sementara
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Proses dengan Replicate
        with open(temp_path, "rb") as video_file:
            output = replicate.run(
                "lucataco/dotted-video:ea6107f7dc327e05d64eb42241250261af417d41d00c6399b06b0d62cd3c1a2a",
                input={
                    "video": video_file,
                    "dot_size": dot_size,          # Pakai nilai dari user
                    "threshold": threshold,        # Pakai nilai dari user
                    "inverse": inverse,            # Pakai nilai dari user
                    "inverse_threshold": False     # Tetap default
                }
            )

        # Simpan hasil
        output_filename = f"dotted_{uuid4().hex}.mp4"
        output_path = os.path.join(UPLOAD_VIDEO_FOLDER, output_filename)

        with open(output_path, "wb") as f:
            f.write(output.read())

        return JSONResponse({
            "status": "success",
            "video_url": f"/uploads/videos/{output_filename}",
            "settings": {                          # Return konfigurasi yang dipakai
                "dot_size": dot_size,
                "threshold": threshold,
                "inverse": inverse
            }
        })

    except Exception as e:
        raise HTTPException(500, f"Internal Server Error: {str(e)}")

    finally:
        # Bersihkan file sementara
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
