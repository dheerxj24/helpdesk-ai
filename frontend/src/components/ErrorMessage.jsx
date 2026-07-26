export default function ErrorMessage({ error, onRetry }) {
  const message = error?.message || String(error)
  const looksLikeCors = error?.status === 0

  return (
    <div className="state-box error-box">
      <p>Something went wrong: {message}</p>
      {looksLikeCors && (
        <p className="error-hint">
          This looks like a network/CORS failure. The FastAPI backend does not
          currently send CORS headers, so browser requests from this dev
          server (a different origin) can be blocked. Add{' '}
          <code>CORSMiddleware</code> to <code>app/main.py</code> on the
          backend to allow this origin -- that's a backend change, not
          something this frontend can work around.
        </p>
      )}
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn btn-secondary">
          Retry
        </button>
      )}
    </div>
  )
}
