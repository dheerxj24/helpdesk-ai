import { useEffect, useState, useCallback } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { getSummary, getConfidenceDist } from '../api/analytics'
import Loading from './Loading'
import ErrorMessage from './ErrorMessage'

const STATUS_COLORS = {
  auto_resolved: '#16a34a',
  escalated: '#dc2626',
  open_or_suggested: '#ca8a04',
}

const CATEGORY_COLOR = '#2563eb'
const CONFIDENCE_COLOR = '#7c3aed'

export default function AnalyticsDashboard({ refreshKey }) {
  const [summary, setSummary] = useState(null)
  const [confDist, setConfDist] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    Promise.all([getSummary(), getConfidenceDist()])
      .then(([summaryData, confData]) => {
        setSummary(summaryData)
        setConfDist(confData)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount pattern
    load()
  }, [load, refreshKey])

  if (loading) return <Loading label="Loading analytics..." />
  if (error) return <ErrorMessage error={error} onRetry={load} />
  if (!summary || summary.total_tickets === 0) {
    return <div className="state-box">No tickets yet -- create some to see analytics.</div>
  }

  const categoryData = Object.entries(summary.tickets_by_category || {}).map(
    ([category, count]) => ({ category, count }),
  )

  const statusData = [
    { name: 'Auto Resolved', value: summary.auto_resolved, key: 'auto_resolved' },
    { name: 'Escalated', value: summary.escalated, key: 'escalated' },
    { name: 'Open / Suggested', value: summary.open_or_suggested, key: 'open_or_suggested' },
  ].filter((d) => d.value > 0)

  const confidenceData = Object.entries(confDist?.buckets || {}).map(([bucket, count]) => ({
    bucket,
    count,
  }))

  return (
    <div className="analytics-grid">
      <div className="summary-cards">
        <SummaryCard label="Total Tickets" value={summary.total_tickets} />
        <SummaryCard
          label="Auto-Resolve Rate"
          value={`${(summary.auto_resolve_rate * 100).toFixed(1)}%`}
        />
        <SummaryCard
          label="Average Confidence"
          value={summary.average_confidence != null ? `${(summary.average_confidence * 100).toFixed(1)}%` : '—'}
        />
      </div>

      <div className="chart-row">
        <div className="card chart-card">
          <h3>Tickets by Category</h3>
          {categoryData.length === 0 ? (
            <p className="muted">No categorized tickets yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill={CATEGORY_COLOR} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card chart-card">
          <h3>Status Breakdown</h3>
          {statusData.length === 0 ? (
            <p className="muted">No status data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {statusData.map((entry) => (
                    <Cell key={entry.key} fill={STATUS_COLORS[entry.key]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="card chart-card">
        <h3>Confidence Score Distribution</h3>
        {confidenceData.length === 0 ? (
          <p className="muted">No logged decisions yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={confidenceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill={CONFIDENCE_COLOR} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}

function SummaryCard({ label, value }) {
  return (
    <div className="card summary-card">
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  )
}
