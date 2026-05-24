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

## React Frontend

The frontend is now a separate React app in `frontend/`.

First time only:

```powershell
cd frontend
npm install
```

Run backend:

```powershell
.\run_app.bat
```

Run frontend in another terminal:

```powershell
.\run_frontend.bat
```

Open:

```text
http://127.0.0.1:5173
```

## Public URL Options

- Best for privacy/offline use: keep it local at `http://127.0.0.1:8000`.
- Best temporary public link: Cloudflare Tunnel or ngrok.
- Best always-online deployment: a VPS like DigitalOcean, AWS Lightsail, or Render/Railway.

If your PDF is private, do not deploy it publicly unless you add login protection.

## Deploy With GitHub, Render, And Vercel

Recommended setup:

| Part | Service |
| --- | --- |
| Code storage | GitHub |
| Backend | Render |
| Frontend | Vercel |

### 1. Push Code To GitHub

Create a GitHub repository, then push this project folder:

```powershell
git add .
git commit -m "Prepare app for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/offline-doc-chatbot.git
git push -u origin main
```

### 2. Deploy Backend On Render

In Render, create a new Web Service from your GitHub repo.

Use these settings:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

After deploy, Render gives you a backend URL like:

```text
https://offline-doc-chatbot-backend.onrender.com
```

Open this to test:

```text
https://offline-doc-chatbot-backend.onrender.com/health
```

### 3. Deploy Frontend On Vercel

In Vercel, import the same GitHub repo.

Use these settings:

```text
Root Directory: backend/frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

Add this Environment Variable in Vercel:

```text
VITE_API_BASE_URL=https://YOUR_RENDER_BACKEND_URL
```

Redeploy the frontend after adding the environment variable.

### 4. Lock CORS After You Know The Vercel URL

In Render, set this Environment Variable:

```text
ALLOWED_ORIGINS=https://YOUR_VERCEL_FRONTEND_URL
```

Then redeploy the backend.

## Notes

Text and tables are extracted from PDF pages. Image metadata is indexed, but exact text inside scanned images needs OCR before upload.

This version uses local TF-IDF search, so it does not need Hugging Face, OpenAI, or internet access to answer from the uploaded PDF.
