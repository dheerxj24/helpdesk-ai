import { get } from './client'

export function getSummary() {
  return get('/analytics/summary')
}

export function getConfidenceDist() {
  return get('/analytics/confidence-dist')
}
