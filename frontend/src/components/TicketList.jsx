import { useEffect, useState, useCallback } from 'react'
import { listTickets } from '../api/tickets'
import Loading from './Loading'
import ErrorMessage from './ErrorMessage'
import StatusBadge from './StatusBadge'
import TicketDetail from './TicketDetail'

const STATUS_OPTIONS = ['open', 'auto_resolved', 'escalated', 'closed']
const CATEGORY_OPTIONS = ['Network', 'Access', 'Hardware', 'Software', 'Email', 'Other']

export default function TicketList({ refreshKey }) {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [selectedId, setSelectedId] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    listTickets({ status: status || undefined, category: category || undefined })
      .then(setTickets)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [status, category])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount pattern
    load()
  }, [load, refreshKey])

  return (
    <div className="card">
      <div className="card-header">
        <h2>Tickets</h2>
        <div className="filters">
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All</option>
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {loading && <Loading label="Loading tickets..." />}
      {error && <ErrorMessage error={error} onRetry={load} />}

      {!loading && !error && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Subject</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {tickets.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted center">
                    No tickets found.
                  </td>
                </tr>
              )}
              {tickets.map((t) => (
                <tr key={t.id} className="clickable-row" onClick={() => setSelectedId(t.id)}>
                  <td>{t.subject}</td>
                  <td>{t.category || '—'}</td>
                  <td>{t.priority || '—'}</td>
                  <td>
                    <StatusBadge status={t.status} />
                  </td>
                  <td>{t.confidence_score != null ? `${(t.confidence_score * 100).toFixed(0)}%` : '—'}</td>
                  <td>{new Date(t.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedId != null && (
        <TicketDetail ticketId={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </div>
  )
}
