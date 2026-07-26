import { get, post } from './client'

export function listTickets({ status, category } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (category) params.set('category', category)
  const query = params.toString()
  return get(`/tickets${query ? `?${query}` : ''}`)
}

export function getTicket(id) {
  return get(`/tickets/${id}`)
}

export function createTicket({ subject, description }) {
  return post('/tickets', { subject, description })
}
