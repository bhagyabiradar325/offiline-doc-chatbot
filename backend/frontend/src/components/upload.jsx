import { useState } from "react";

export default function Upload({ onUpload, onUploadError }) {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!file) return;

    setIsUploading(true);
    onUploadError("");

    try {
      await onUpload(file);
    } catch (error) {
      onUploadError(error.message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label htmlFor="pdf">PDF file</label>
      <input
        id="pdf"
        type="file"
        accept="application/pdf"
        onChange={(event) => setFile(event.target.files[0] || null)}
        required
      />
      <button type="submit" disabled={isUploading || !file}>
        {isUploading ? "Uploading..." : "Upload PDF"}
      </button>
    </form>
  );
}
