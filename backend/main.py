import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from document_loader import load_pdf
from qa_engine import answer_question
from vector_store import create_vector_store


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
ASSET_DIR = BASE_DIR / "assets"
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSET_DIR = FRONTEND_DIST_DIR / "frontend-assets"

UPLOAD_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Offiline Doc Chatbot")
app.mount("/assets", StaticFiles(directory=ASSET_DIR), name="assets")
if FRONTEND_ASSET_DIR.exists():
    app.mount(
        "/frontend-assets",
        StaticFiles(directory=FRONTEND_ASSET_DIR),
        name="frontend-assets",
    )

allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db = None
indexed_document: Optional[dict] = None


def serialize_document_chunk(chunk: dict) -> dict:
    return {
        "page": chunk["page"],
        "kind": chunk["kind"],
        "content": chunk["content"],
        "snippet": " ".join(chunk["content"].split())[:260],
        "extra": chunk.get("extra", {}),
    }


@app.get("/")
async def home():
    frontend_index = FRONTEND_DIST_DIR / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)

    return {
        "message": "Offline Doc Chatbot API is running.",
        "frontend": "Run the React app from backend/frontend at http://127.0.0.1:5173",
    }


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global vector_db, indexed_document

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    doc_id = uuid4().hex
    pdf_path = UPLOAD_DIR / f"{doc_id}_{Path(file.filename).name}"
    with pdf_path.open("wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    pages = load_pdf(pdf_path, image_output_dir=ASSET_DIR / doc_id, doc_id=doc_id)
    vector_db = create_vector_store(pages)
    page_count = max((page["page"] for page in pages), default=0)
    indexed_document = {
        "id": doc_id,
        "filename": file.filename,
        "pages": page_count,
        "chunks": len(vector_db.documents),
        "path": str(pdf_path),
    }

    return {
        "message": "PDF processed and indexed.",
        "filename": file.filename,
        "pages": indexed_document["pages"],
        "chunks": indexed_document["chunks"],
    }


@app.get("/ask")
async def ask(query: str):
    if vector_db is None:
        raise HTTPException(status_code=400, detail="Please upload a PDF first.")
    if not query.strip():
        raise HTTPException(status_code=400, detail="Please enter a question.")

    return answer_question(query=query, vector_db=vector_db)


@app.get("/pdf")
async def current_pdf():
    if not indexed_document:
        raise HTTPException(status_code=404, detail="Please upload a PDF first.")

    return FileResponse(
        indexed_document["path"],
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{indexed_document["filename"]}"'},
    )


@app.get("/page/{page_number}")
async def page_details(page_number: int):
    if vector_db is None:
        raise HTTPException(status_code=400, detail="Please upload a PDF first.")

    page_chunks = [
        serialize_document_chunk(chunk)
        for chunk in vector_db.documents
        if int(chunk["page"]) == page_number and chunk["kind"] in {"table", "image"}
    ]

    return {"page": page_number, "items": page_chunks}


@app.get("/health")
async def health():
    return {"status": "ok", "document": indexed_document}
