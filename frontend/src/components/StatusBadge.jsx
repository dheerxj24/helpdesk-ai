const STATUS_STYLES = {
  auto_resolved: { background: '#dcfce7', color: '#166534', label: 'Auto Resolved' },
  escalated: { background: '#fee2e2', color: '#991b1b', label: 'Escalated' },
  open: { background: '#fef9c3', color: '#854d0e', label: 'Open' },
  closed: { background: '#e5e7eb', color: '#374151', label: 'Closed' },
}

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || {
    background: '#e5e7eb',
    color: '#374151',
    label: status || 'Unknown',
  }
  return (
    <span
      className="status-badge"
      style={{ background: style.background, color: style.color }}
    >
      {style.label}
    </span>
  )
}
