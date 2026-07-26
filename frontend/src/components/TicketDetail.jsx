import { useEffect, useState } from 'react'
import { getTicket } from '../api/tickets'
import Loading from './Loading'
import ErrorMessage from './ErrorMessage'
import StatusBadge from './StatusBadge'

export default function TicketDetail({ ticketId, onClose }) {
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount pattern
    setLoading(true)
    setError(null)
    getTicket(ticketId)
      .then((data) => {
        if (!cancelled) setTicket(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [ticketId])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Ticket #{ticketId}</h2>
          <button type="button" className="btn-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {loading && <Loading label="Loading ticket..." />}
        {error && <ErrorMessage error={error} />}

        {ticket && !loading && !error && (
          <div className="ticket-detail-body">
            <h3>{ticket.subject}</h3>
            <div className="ticket-detail-meta">
              <StatusBadge status={ticket.status} />
              {ticket.category && <span className="pill">{ticket.category}</span>}
              {ticket.priority && <span className="pill">{ticket.priority}</span>}
              {ticket.confidence_score != null && (
                <span className="pill">
                  Confidence: {(ticket.confidence_score * 100).toFixed(0)}%
                </span>
              )}
            </div>

            <section>
              <h4>Description</h4>
              <p className="detail-text">{ticket.description}</p>
            </section>

            <section>
              <h4>Resolution</h4>
              {ticket.resolution ? (
                <p className="detail-text">{ticket.resolution}</p>
              ) : (
                <p className="detail-text muted">No resolution yet.</p>
              )}
            </section>

            <p className="muted small">
              Created: {new Date(ticket.created_at).toLocaleString()}
              {ticket.resolved_by ? ` · Resolved by: ${ticket.resolved_by}` : ''}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
