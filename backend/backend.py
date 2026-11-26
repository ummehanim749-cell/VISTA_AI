
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import sys
from fastapi import UploadFile, File, HTTPException
import uuid
from media_processor import process_media
from starlette.concurrency import run_in_threadpool
from question_answer import VISTAQuestionAnswer
from pydantic import BaseModel
# Project root
ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="VISTA AI Backend")

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_json(filename):
    file_path = ROOT / filename

    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.get("/")
def home():
    return {
        "message": "VISTA AI Backend is running",
        "status": "ready"
    }


@app.get("/tracking")
def get_tracking():
    data = load_json("tracking_data.json")

    if data is None:
        return {"error": "tracking_data.json not found"}

    return data


@app.get("/events")
def get_events():
    data = load_json("events.json")

    if data is None:
        return {"error": "events.json not found"}

    return data


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv"}
    extension = Path(file.filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format"
        )

    upload_folder = ROOT / "uploads"
    upload_folder.mkdir(exist_ok=True)

    video_id = str(uuid.uuid4())
    saved_path = upload_folder / f"{video_id}{extension}"

    with open(saved_path, "wb") as destination:
        while chunk := await file.read(1024 * 1024):
            destination.write(chunk)

        await file.close()

    try:
        # Run YOLO and ByteTrack video processing
        tracking_data = await run_in_threadpool(
            process_media,
            str(saved_path)
        )

        # Save tracking results for the frontend API
        tracking_path = ROOT / "tracking_data.json"

        with open(tracking_path, "w", encoding="utf-8") as output_file:
            json.dump(tracking_data, output_file, indent=4)

        return {
            "status": "success",
            "message": "Video uploaded and processed successfully",
            "video_id": video_id,
            "filename": file.filename,
            "total_frames": len(tracking_data),
            "tracking_file": "tracking_data.json"
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(error)}"
        )
        from pydantic import BaseModel


class QuestionRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_vista(request: QuestionRequest):
    tracking_path = ROOT / "tracking_data.json"

    if not tracking_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Tracking data not found"
        )

    try:
        qa = VISTAQuestionAnswer(str(tracking_path))
        answer = qa.answer(request.question)

        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )