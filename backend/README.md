# Offline Doc Chatbot

Upload one PDF, ask questions, and receive source snippets with page numbers.

## Run

Double-click `run_app.bat`, or run this command from the backend folder:

```powershell
.\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

## Public URL Options

- Best for privacy/offline use: keep it local at `http://127.0.0.1:8000`.
- Best temporary public link: Cloudflare Tunnel or ngrok.
- Best always-online deployment: a VPS like DigitalOcean, AWS Lightsail, or Render/Railway.

If your PDF is private, do not deploy it publicly unless you add login protection.

## Notes

Text and tables are extracted from PDF pages. Image metadata is indexed, but exact text inside scanned images needs OCR before upload.

This version uses local TF-IDF search, so it does not need Hugging Face, OpenAI, or internet access to answer from the uploaded PDF.
