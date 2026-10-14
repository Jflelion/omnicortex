import type {
  ConversationDetail,
  ConversationSummary,
  ConversationTurn,
  DocumentItem,
  User,
} from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '')
const TOKEN_KEY = 'omnicortex.token'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Storage unavailable (private mode): the session lasts until reload.
  }
}

let onUnauthorized: (() => void) | null = null

/** Called whenever the API rejects the token (expired or invalid). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()

  if (token) headers.set('Authorization', `Bearer ${token}`)

  if (init.body && !(init.body instanceof FormData) && !(init.body instanceof URLSearchParams)) {
    headers.set('Content-Type', 'application/json')
  }

  let response: Response

  try {
    response = await fetch(`${API_URL}${path}`, { ...init, headers })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con la API. ¿Está el backend en marcha?')
  }

  if (response.status === 401 && token) onUnauthorized?.()

  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }

  if (response.status === 204) return undefined as T

  return (await response.json()) as T
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()

    if (typeof body.detail === 'string') return body.detail

    // FastAPI validation errors: [{ loc, msg }, ...]
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { msg: string }) => item.msg).join('. ')
    }
  } catch {
    // Not JSON.
  }

  return `Error ${response.status}`
}

const json = (body: unknown) => JSON.stringify(body)

export const api = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: new URLSearchParams({ username, password }),
    }),

  register: (data: { username: string; email: string; password: string; full_name?: string }) =>
    request<User>('/users/', { method: 'POST', body: json(data) }),

  me: () => request<User>('/auth/me'),

  /** Resolves once the API answers at all (it may report itself degraded). */
  ping: () => fetch(`${API_URL}/health`).then(() => undefined),

  listDocuments: () => request<DocumentItem[]>('/documents/'),

  uploadDocument: (file: File) => {
    const form = new FormData()
    form.append('file', file)

    return request<DocumentItem>('/documents/upload', { method: 'POST', body: form })
  },

  deleteDocument: (id: number) => request<void>(`/documents/${id}`, { method: 'DELETE' }),

  reindexDocument: (id: number) =>
    request<DocumentItem>(`/documents/${id}/reindex`, { method: 'POST' }),

  listConversations: () => request<ConversationSummary[]>('/conversations/'),

  getConversation: (id: number) => request<ConversationDetail>(`/conversations/${id}`),

  createConversation: () =>
    request<ConversationSummary>('/conversations/', { method: 'POST', body: json({}) }),

  renameConversation: (id: number, title: string) =>
    request<ConversationSummary>(`/conversations/${id}`, {
      method: 'PATCH',
      body: json({ title }),
    }),

  deleteConversation: (id: number) =>
    request<void>(`/conversations/${id}`, { method: 'DELETE' }),

  sendMessage: (id: number, question: string) =>
    request<ConversationTurn>(`/conversations/${id}/messages`, {
      method: 'POST',
      body: json({ question }),
    }),
}
