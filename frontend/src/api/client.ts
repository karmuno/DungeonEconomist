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

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  }

  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  const response = await fetch(`${BASE_URL}${url}`, options)

  if (!response.ok) {
    let data: unknown
    try {
      data = await response.json()
    } catch {
      data = null
    }
    throw new ApiError(
      `Request failed: ${method} ${url} (${response.status})`,
      response.status,
      data,
    )
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
