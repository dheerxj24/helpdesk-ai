import { useState } from 'react'
import { createTicket } from '../api/tickets'
import ErrorMessage from '../components/ErrorMessage'
import StatusBadge from '../components/StatusBadge'

const DECISION_LABELS = {
  auto_resolved: 'Auto-resolved',
  escalated: 'Escalated to a human agent',
  open: 'Suggested resolution (pending agent review)',
}

export default function CreateTicketForm({ onCreated }) {
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!subject.trim() || !description.trim()) return

    setSubmitting(true)
    setError(null)
    setResult(null)
    try {
      const ticket = await createTicket({ subject, description })
      setResult(ticket)
      setSubject('')
      setDescription('')
      onCreated?.()
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>Create Ticket</h2>
      </div>

      <form onSubmit={handleSubmit} className="form">
        <label>
          Subject
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Can't connect to VPN"
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the issue in detail..."
            rows={5}
            required
          />
        </label>
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Submitting...' : 'Submit Ticket'}
        </button>
      </form>

      {error && <ErrorMessage error={error} />}

      {result && (
        <div className="result-box">
          <h3>Ticket #{result.id} created</h3>
          <div className="ticket-detail-meta">
            <StatusBadge status={result.status} />
            {result.category && <span className="pill">{result.category}</span>}
            {result.priority && <span className="pill">{result.priority}</span>}
            {result.confidence_score != null && (
              <span className="pill">
                Confidence: {(result.confidence_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
          <p className="muted">
            Routing decision: <strong>{DECISION_LABELS[result.status] || result.status}</strong>
          </p>
          {result.resolution && (
            <>
              <h4>Suggested Resolution</h4>
              <p className="detail-text">{result.resolution}</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
