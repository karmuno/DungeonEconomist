import * as Sentry from '@sentry/vue'

const BASE_URL = ''

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(message: string, status: number, data: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

let _isRefreshing = false
let _refreshQueue: Array<{ resolve: () => void; reject: (err: unknown) => void }> = []

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem('refreshToken')
  if (!refreshToken) return false

  // If already refreshing, wait for the in-flight refresh to finish
  if (_isRefreshing) {
    return new Promise((resolve, reject) => {
      _refreshQueue.push({ resolve: () => resolve(true), reject: () => reject(false) })
    })
  }

  _isRefreshing = true
  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) return false

    const data = await response.json()
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('refreshToken', data.refresh_token)

    // Resolve all queued requests
    _refreshQueue.forEach(q => q.resolve())
    return true
  } catch {
    _refreshQueue.forEach(q => q.reject(false))
    return false
  } finally {
    _isRefreshing = false
    _refreshQueue = []
  }
}

async function request<T>(method: string, url: string, body?: unknown, isRetry = false): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  const token = localStorage.getItem('token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const keepId = localStorage.getItem('keepId')
  if (keepId) {
    headers['X-Keep-Id'] = keepId
  }

  const options: RequestInit = {
    method,
    headers,
  }

  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  // Callers almost always swallow these in a bare `catch {}` and show a friendly
  // notification, so report here or Sentry never hears about them.
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${url}`, options)
  } catch (err) {
    // No response at all: offline, DNS, CORS, server down.
    Sentry.captureException(err, {
      tags: { api_status: 'network' },
      extra: { method, url },
    })
    throw err
  }

  if (response.status === 401 && !isRetry && !url.startsWith('/auth/')) {
    const refreshed = await tryRefreshToken()
    if (refreshed) {
      return request<T>(method, url, body, true)
    }
    // Refresh failed — clear auth state and redirect to login
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('keepId')
    window.location.href = '/login'
  }

  if (!response.ok) {
    let data: unknown
    try {
      data = await response.json()
    } catch {
      data = null
    }
    const error = new ApiError(
      `Request failed: ${method} ${url} (${response.status})`,
      response.status,
      data,
    )
    // 5xx only. Reporting 4xx would bury the signal under expected validation
    // failures and 401s, which the refresh flow above already handles.
    if (response.status >= 500) {
      Sentry.captureException(error, {
        tags: { api_status: String(response.status) },
        extra: { method, url, body: data },
      })
    }
    throw error
  }

  return response.json() as Promise<T>
}

export function get<T>(url: string): Promise<T> {
  return request<T>('GET', url)
}

export function post<T>(url: string, body?: unknown): Promise<T> {
  return request<T>('POST', url, body)
}

export function put<T>(url: string, body?: unknown): Promise<T> {
  return request<T>('PUT', url, body)
}

export function del<T>(url: string): Promise<T> {
  return request<T>('DELETE', url)
}
