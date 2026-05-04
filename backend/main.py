from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from document_loader import load_pdf
from qa_engine import answer_question
from vector_store import create_vector_store


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
ASSET_DIR = BASE_DIR / "assets"
UPLOAD_DIR.mkdir(exist_ok=True)
ASSET_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Offline Doc Chatbot")
app.mount("/assets", StaticFiles(directory=ASSET_DIR), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_db = None
indexed_document: Optional[dict] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Offline Doc Chatbot</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: #f6f7f9;
      color: #17202a;
    }
    * { box-sizing: border-box; }
    body { margin: 0; }
    main {
      width: min(1280px, calc(100% - 32px));
      margin: 28px auto;
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr) 420px;
      gap: 18px;
    }
    section {
      background: #ffffff;
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(20, 28, 38, 0.06);
    }
    h1 { margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }
    p { margin: 0 0 14px; color: #52616f; line-height: 1.5; }
    label { display: block; margin-bottom: 8px; font-weight: 650; }
    input[type="file"], input[type="text"] {
      width: 100%;
      border: 1px solid #c7d0dc;
      border-radius: 6px;
      padding: 11px 12px;
      font-size: 15px;
      background: #fff;
    }
    input[type="file"] { padding: 9px; }
    button {
      border: 0;
      border-radius: 6px;
      background: #1769aa;
      color: white;
      font-weight: 700;
      padding: 11px 14px;
      cursor: pointer;
      min-height: 42px;
    }
    button:disabled { background: #8aa8c3; cursor: wait; }
    .row { display: flex; gap: 10px; align-items: center; }
    .row input { flex: 1; }
    .status {
      min-height: 22px;
      margin-top: 12px;
      color: #2d6a4f;
      font-size: 14px;
    }
    .error { color: #b42318; }
    .answer {
      white-space: pre-wrap;
      line-height: 1.55;
      background: #f9fafb;
      border: 1px solid #e4e8ef;
      border-radius: 8px;
      padding: 14px;
      min-height: 160px;
    }
    .sources { margin-top: 14px; display: grid; gap: 10px; }
    .source {
      border: 1px solid #d8dee8;
      border-radius: 8px;
      padding: 12px;
      background: #fff;
    }
    .source strong { display: block; margin-bottom: 6px; }
    .source small { color: #637083; }
    .page-link {
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 6px 9px;
      margin-bottom: 8px;
      color: #1769aa;
      background: #eef6fc;
      border: 1px solid #c7dff2;
      border-radius: 6px;
      font-weight: 700;
      text-decoration: none;
    }
    .source pre {
      overflow-x: auto;
      white-space: pre-wrap;
      background: #f4f6f8;
      border: 1px solid #e0e5ec;
      border-radius: 6px;
      padding: 10px;
      margin: 8px 0 0;
      color: #2b3642;
      font-family: Consolas, monospace;
      font-size: 13px;
      line-height: 1.45;
    }
    .source img {
      display: block;
      max-width: 100%;
      max-height: 280px;
      object-fit: contain;
      border: 1px solid #d8dee8;
      border-radius: 6px;
      margin-top: 8px;
      background: #fff;
    }
    .viewer {
      min-height: 680px;
      padding: 0;
      overflow: hidden;
    }
    .viewerHeader {
      padding: 12px 14px;
      border-bottom: 1px solid #d8dee8;
      font-weight: 700;
    }
    iframe {
      width: 100%;
      height: 630px;
      border: 0;
      background: #eef1f5;
    }
    @media (max-width: 1100px) {
      main { grid-template-columns: 1fr; margin-top: 16px; }
      .viewer { min-height: 520px; }
      iframe { height: 470px; }
      .row { flex-direction: column; align-items: stretch; }
    }
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Offline Doc Chatbot</h1>
      <p>Upload one PDF, then ask questions. Results show page links, extracted tables, and extracted PDF images when found.</p>
      <form id="uploadForm">
        <label for="pdf">PDF file</label>
        <input id="pdf" type="file" accept="application/pdf" required />
        <div style="height: 12px"></div>
        <button id="uploadBtn" type="submit">Upload PDF</button>
      </form>
      <div id="uploadStatus" class="status"></div>
    </section>

    <section>
      <h2>Ask your PDF</h2>
      <form id="askForm" class="row">
        <input id="question" type="text" placeholder="Example: Which table shows revenue?" required />
        <button id="askBtn" type="submit">Ask</button>
      </form>
      <div style="height: 14px"></div>
      <div id="answer" class="answer">Upload a PDF to begin.</div>
      <div id="sources" class="sources"></div>
    </section>

    <section class="viewer">
      <div class="viewerHeader">PDF page viewer</div>
      <iframe id="pdfViewer" title="PDF page viewer"></iframe>
    </section>
  </main>

  <script>
    const uploadForm = document.querySelector("#uploadForm");
    const askForm = document.querySelector("#askForm");
    const uploadStatus = document.querySelector("#uploadStatus");
    const answerBox = document.querySelector("#answer");
    const sourcesBox = document.querySelector("#sources");
    const pdfViewer = document.querySelector("#pdfViewer");
    const uploadBtn = document.querySelector("#uploadBtn");
    const askBtn = document.querySelector("#askBtn");

    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = document.querySelector("#pdf").files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("file", file);
      uploadBtn.disabled = true;
      uploadStatus.className = "status";
      uploadStatus.textContent = "Indexing PDF...";

      try {
        const response = await fetch("/upload", { method: "POST", body: formData });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Upload failed");
        uploadStatus.textContent = `${data.filename} indexed: ${data.pages} pages, ${data.chunks} searchable chunks.`;
        answerBox.textContent = "Ready. Ask a question about your PDF.";
        sourcesBox.innerHTML = "";
        pdfViewer.src = "/pdf#page=1";
      } catch (error) {
        uploadStatus.className = "status error";
        uploadStatus.textContent = error.message;
      } finally {
        uploadBtn.disabled = false;
      }
    });

    askForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const question = document.querySelector("#question").value.trim();
      if (!question) return;

      askBtn.disabled = true;
      answerBox.textContent = "Thinking...";
      sourcesBox.innerHTML = "";

      try {
        const response = await fetch(`/ask?query=${encodeURIComponent(question)}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Question failed");
        answerBox.textContent = data.answer;
        sourcesBox.innerHTML = data.sources.map(renderSource).join("");
      } catch (error) {
        answerBox.textContent = error.message;
      } finally {
        askBtn.disabled = false;
      }
    });

    sourcesBox.addEventListener("click", (event) => {
      const link = event.target.closest("[data-page]");
      if (!link) return;
      event.preventDefault();
      openPage(link.dataset.page);
    });

    function openPage(page) {
      pdfViewer.src = `/pdf#page=${page}`;
      window.open(`/pdf#page=${page}`, "_blank");
    }

    function escapeHtml(value) {
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function renderSource(source) {
      const pageLink = `<a href="/pdf#page=${source.page}" data-page="${source.page}" class="page-link">Open page ${source.page}</a>`;
      const title = `<strong>Page ${source.page} - ${escapeHtml(source.kind)}</strong>`;

      if (source.kind === "table") {
        return `
          <div class="source">
            ${pageLink}
            ${title}
            <pre>${escapeHtml(source.content)}</pre>
          </div>
        `;
      }

      if (source.kind === "image") {
        const imageUrl = source.extra && source.extra.image_url;
        const imageTag = imageUrl ? `<img src="${imageUrl}" alt="Image from page ${source.page}" />` : "";
        return `
          <div class="source">
            ${pageLink}
            ${title}
            <small>${escapeHtml(source.snippet)}</small>
            ${imageTag}
          </div>
        `;
      }

      return `
        <div class="source">
          ${pageLink}
          ${title}
          <small>${escapeHtml(source.snippet)}</small>
        </div>
      `;
    }
  </script>
</body>
</html>
"""


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
        filename=indexed_document["filename"],
    )


@app.get("/health")
async def health():
    return {"status": "ok", "document": indexed_document}
