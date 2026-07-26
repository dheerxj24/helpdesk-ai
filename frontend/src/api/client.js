// Central fetch wrapper for the FastAPI backend.
//
// API_BASE_URL comes from the VITE_API_URL environment variable (set in
// Vercel: Settings -> Environment Variables -> VITE_API_URL, applied to
// Production + Preview). Falls back to the local FastAPI dev server so
// `npm run dev` still works out of the box without a .env file.
//
// Vite only exposes env vars prefixed with VITE_ to client code, and only
// bakes them in at BUILD time -- changing the var in Vercel requires a
// redeploy (not just a page refresh) to take effect.

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (err) {
    // fetch throws a plain TypeError ("Failed to fetch") for both network
    // failures and CORS rejections -- surface a helpful hint either way.
    throw new ApiError(
      `Could not reach the backend at ${API_BASE_URL}${path}. ` +
        `Is the FastAPI server running, and does it allow CORS from this origin? (${err.message})`,
      0,
    )
  }

  if (!response.ok) {
    let detail = response.statusText
    try {
      const body = await response.json()
      detail = body.detail ? JSON.stringify(body.detail) : detail
    } catch {
      // response had no JSON body, keep statusText
    }
    throw new ApiError(`${response.status} ${detail}`, response.status)
  }

  if (response.status === 204) return null
  return response.json()
}

export function get(path) {
  return request(path, { method: 'GET' })
}

export function post(path, body) {
  return request(path, { method: 'POST', body: JSON.stringify(body) })
}