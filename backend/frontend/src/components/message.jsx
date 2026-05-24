import { apiUrl } from "../api.js";

function renderSourceBody(source) {
  if (source.kind === "table") {
    return <pre>{source.content}</pre>;
  }

  if (source.kind === "image") {
    const imageUrl = source.extra?.image_url;
    return (
      <>
        <small>{source.snippet}</small>
        {imageUrl && <img src={apiUrl(imageUrl)} alt={`Image from page ${source.page}`} />}
      </>
    );
  }

  return <small>{source.snippet}</small>;
}

export default function Message({ message, onOpenPage }) {
  const pageNumbers = [...new Set((message.sources || []).map((source) => source.page))];

  return (
    <article className={`message ${message.role}`}>
      <div className="message-bubble">{message.text}</div>

      {message.sources?.length > 0 && (
        <div className="sources">
          <div className="page-list">
            {pageNumbers.map((page) => (
              <a
                className="page-link"
                href={apiUrl(`/pdf#page=${page}`)}
                key={page}
                target="_blank"
                rel="noreferrer"
                onClick={() => onOpenPage(page)}
              >
                Page {page}
              </a>
            ))}
          </div>

          {message.sources.map((source, index) => (
            <div className="source" key={`${source.page}-${source.kind}-${index}`}>
              <strong>
                Page {source.page} - {source.kind}
              </strong>
              {renderSourceBody(source)}
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
