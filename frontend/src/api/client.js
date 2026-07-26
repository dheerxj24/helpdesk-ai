// Central fetch wrapper for the FastAPI backend.
//
// IMPORTANT: The backend at http://127.0.0.1:8000 does not currently have
// CORS configured. If you see a browser console error like:
//   "Access to fetch at 'http://127.0.0.1:8000/...' from origin
//   'http://localhost:5173' has been blocked by CORS policy"
// that is NOT a frontend bug. The backend needs a CORSMiddleware added
// (in app/main.py) allowing the Vite dev origin. This app deliberately does
// not attempt any workaround (no proxy hacks) since the backend is out of
// scope for this change -- flag it and fix it on the backend instead.

export const API_BASE_URL = 'http://127.0.0.1:8000'

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
