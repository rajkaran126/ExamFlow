"""FastAPI Application Server for EXAMFLOW AI.
Exposes endpoints for chat, streaming SSE, PDF upload, RAG search,
consequential action approvals, and voice interaction.
"""

import os
import shutil
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    ChatRequest, ChatResponse, DocumentMetadata, ConsequentialConfirmation,
    UserRole
)
from app.agent import examflow_agent
from app.context_manager import context_manager
from app.voice.voice_service import voice_service
from app.retrieval.vector_store import vector_store

# Create uploads directory if missing
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Advanced Autonomous Agent for PS-072 Online Exam Proctoring Result Engine",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
@app.head("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>EXAMFLOW AI System Active</h1><p>Static UI not yet loaded.</p>"

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "problem_statement": settings.PROBLEM_STATEMENT,
        "environment": settings.ENVIRONMENT,
        "llama_model": settings.LLAMA_MODEL_ID,
        "llama_live_api": bool(settings.LLAMA_API_KEY)
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Processes conversational questions, investigations, and tool calls."""
    try:
        return await examflow_agent.chat(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streams response tokens using Server-Sent Events (SSE)."""
    async def event_generator():
        try:
            async for chunk in examflow_agent.chat_stream(request):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR: {str(e)}]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/documents/upload", response_model=DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form("default_session")
):
    """Uploads a PDF directly inside the AI chat interface and indexes it for RAG."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Index document
        metadata = examflow_agent.upload_and_index_document(
            file_path=file_path,
            filename=file.filename,
            session_id=session_id
        )
        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.get("/api/documents/list", response_model=List[DocumentMetadata])
async def list_documents(session_id: str = "default_session"):
    """Lists indexed documents for the current session."""
    session = context_manager.get_or_create_session(session_id)
    return list(session.attached_docs.values())

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str, session_id: str = "default_session"):
    """Deletes an attached document and removes its references."""
    session = context_manager.get_or_create_session(session_id)
    removed = session.remove_document(doc_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "success", "message": f"Document {doc_id} detached."}

@app.post("/api/action/confirm")
async def confirm_action(confirmation: ConsequentialConfirmation):
    """Executes a Level 5 consequential action after explicit user confirmation."""
    try:
        result = examflow_agent.confirm_consequential_action(confirmation)
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...)):
    """Transcribes audio payload for push-to-talk."""
    try:
        audio_bytes = await file.read()
        return voice_service.transcribe_audio(audio_bytes, file.content_type or "audio/webm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice/synthesize")
async def synthesize_voice(payload: dict):
    """Generates audio voice synthesis text and parameters."""
    text = payload.get("text", "")
    return voice_service.synthesize_speech(text)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
