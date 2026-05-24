import Upload from "./upload.jsx";

export default function Sidebar({ documentInfo, uploadStatus, uploadError, onUpload, onUploadError }) {
  return (
    <aside className="sidebar">
      <Upload onUpload={onUpload} onUploadError={onUploadError} />

      {uploadStatus && <div className="status">{uploadStatus}</div>}
      {uploadError && <div className="status error">{uploadError}</div>}

      <div className="doc-card">
        <h2>Current PDF</h2>
        {documentInfo ? (
          <>
            <p className="doc-name">{documentInfo.filename}</p>
            <dl>
              <div>
                <dt>Pages</dt>
                <dd>{documentInfo.pages}</dd>
              </div>
              <div>
                <dt>Chunks</dt>
                <dd>{documentInfo.chunks}</dd>
              </div>
            </dl>
          </>
        ) : (
          <p>No PDF uploaded yet.</p>
        )}
      </div>
    </aside>
  );
}
