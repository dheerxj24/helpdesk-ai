import { post } from './client'

export function updateThreshold({ threshold_auto, threshold_suggest }) {
  return post('/admin/threshold', { threshold_auto, threshold_suggest })
}
