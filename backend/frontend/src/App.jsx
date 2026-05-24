import { useState } from "react";
import Header from "./components/header.jsx";
import Sidebar from "./components/sidebar.jsx";
import ChatWindow from "./components/chatwindow.jsx";
import { apiUrl } from "./api.js";

export default function App() {
  const [documentInfo, setDocumentInfo] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Upload a PDF to begin.",
      sources: []
    }
  ]);

  async function handleUpload(file) {
    const formData = new FormData();
    formData.append("file", file);
    setUploadError("");
    setUploadStatus("Indexing PDF...");

    const response = await fetch(apiUrl("/upload"), {
      method: "POST",
      body: formData
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }

    setDocumentInfo(data);
    setUploadStatus(`${data.filename} indexed: ${data.pages} pages, ${data.chunks} searchable chunks.`);
    setMessages([
      {
        role: "assistant",
        text: "Ready. Ask a question about your PDF.",
        sources: []
      }
    ]);
  }

  async function handleAsk(question) {
    setMessages((current) => [
      ...current,
      { role: "user", text: question, sources: [] },
      { role: "assistant", text: "Thinking...", sources: [], loading: true }
    ]);

    try {
      const response = await fetch(apiUrl(`/ask?query=${encodeURIComponent(question)}`));
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Question failed");
      }

      setMessages((current) => [
        ...current.filter((message) => !message.loading),
        {
          role: "assistant",
          text: data.answer,
          sources: data.sources || []
        }
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current.filter((message) => !message.loading),
        {
          role: "assistant",
          text: error.message,
          sources: []
        }
      ]);
    }
  }

  function openPage() {
    return true;
  }

  return (
    <div className="app-shell">
      <Header />
      <main className="workspace">
        <Sidebar
          documentInfo={documentInfo}
          uploadStatus={uploadStatus}
          uploadError={uploadError}
          onUpload={handleUpload}
          onUploadError={setUploadError}
        />
        <ChatWindow messages={messages} onAsk={handleAsk} onOpenPage={openPage} />
      </main>
    </div>
  );
}
