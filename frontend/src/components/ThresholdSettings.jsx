import { useState } from 'react'
import { updateThreshold } from '../api/admin'
import ErrorMessage from './ErrorMessage'

// The backend has no GET endpoint for current thresholds, only POST /admin/threshold
// which returns the resulting values. We default the inputs to the values hardcoded
// in app/main.py (THRESHOLD_AUTO=0.80, THRESHOLD_SUGGEST=0.55) and update them
// from the response after a successful save.
export default function ThresholdSettings() {
  const [thresholdAuto, setThresholdAuto] = useState(0.8)
  const [thresholdSuggest, setThresholdSuggest] = useState(0.55)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSaved(null)
    try {
      const res = await updateThreshold({
        threshold_auto: Number(thresholdAuto),
        threshold_suggest: Number(thresholdSuggest),
      })
      setThresholdAuto(res.threshold_auto)
      setThresholdSuggest(res.threshold_suggest)
      setSaved(res)
    } catch (err) {
      setError(err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>Threshold Settings</h2>
      </div>
      <p className="muted small">
        Note: these values live in-memory on the backend process and reset on
        server restart (see the comment in <code>app/main.py</code>).
      </p>
      <form onSubmit={handleSubmit} className="form form-inline">
        <label>
          Auto-resolve threshold
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={thresholdAuto}
            onChange={(e) => setThresholdAuto(e.target.value)}
          />
        </label>
        <label>
          Suggest threshold
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            value={thresholdSuggest}
            onChange={(e) => setThresholdSuggest(e.target.value)}
          />
        </label>
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? 'Saving...' : 'Update Thresholds'}
        </button>
      </form>

      {error && <ErrorMessage error={error} />}
      {saved && (
        <p className="success-text">
          Saved: auto ≥ {saved.threshold_auto}, suggest ≥ {saved.threshold_suggest}
        </p>
      )}
    </div>
  )
}
