import { useEffect, useState, type FormEvent } from 'react'

import { api, ApiError } from '../api/client'
import { Logo } from './Logo'

type Mode = 'login' | 'register'

interface Props {
  onAuthenticated: (token: string) => void
}

// The hosted demo API sleeps when idle; tell the visitor why the first
// request is slow instead of letting it look broken.
const WAKE_NOTICE_DELAY_MS = 1500

function useServerWaking(): boolean {
  const [waking, setWaking] = useState(false)

  useEffect(() => {
    let answered = false
    const timer = window.setTimeout(() => {
      if (!answered) setWaking(true)
    }, WAKE_NOTICE_DELAY_MS)

    const done = () => {
      answered = true
      window.clearTimeout(timer)
      setWaking(false)
    }

    api.ping().then(done, done)

    return () => window.clearTimeout(timer)
  }, [])

  return waking
}

const FEATURES = [
  ['RAG local', 'Embeddings y LLM con Ollama: tus documentos no salen de tu máquina.'],
  ['Fuentes auditables', 'Cada respuesta muestra los fragmentos exactos que la sustentan.'],
  ['Conversaciones', 'Preguntas de seguimiento con el contexto de la charla.'],
]

export function AuthScreen({ onAuthenticated }: Props) {
  const [mode, setMode] = useState<Mode>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const waking = useServerWaking()

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setLoading(true)

    try {
      if (mode === 'register') {
        await api.register({ username, email, password, full_name: username })
      }

      const { access_token } = await api.login(username, password)
      onAuthenticated(access_token)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error inesperado')
    } finally {
      setLoading(false)
    }
  }

  const inputClass =
    'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm outline-none transition ' +
    'focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-zinc-700 dark:bg-zinc-900'

  return (
    <div className="grid min-h-full lg:grid-cols-2">
      <aside className="relative hidden overflow-hidden bg-zinc-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div
          className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-indigo-600/30 blur-3xl"
          aria-hidden="true"
        />
        <div className="relative flex items-center gap-3">
          <Logo />
          <span className="text-lg font-semibold tracking-tight">OmniCortex</span>
        </div>

        <div className="relative max-w-md">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight">
            Pregunta a tus documentos.
            <span className="block text-indigo-300">Obtén respuestas con evidencia.</span>
          </h1>

          <ul className="mt-10 space-y-6">
            {FEATURES.map(([title, text]) => (
              <li key={title} className="flex gap-3">
                <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-indigo-400" />
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="text-sm text-zinc-400">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-zinc-500">FastAPI · PostgreSQL + pgvector · Ollama · React</p>
      </aside>

      <main className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <Logo />
            <span className="text-lg font-semibold">OmniCortex</span>
          </div>

          <h2 className="text-2xl font-semibold tracking-tight">
            {mode === 'login' ? 'Inicia sesión' : 'Crea tu cuenta'}
          </h2>
          <p className="mt-1 text-sm text-zinc-500">
            {mode === 'login' ? '¿No tienes cuenta? ' : '¿Ya tienes cuenta? '}
            <button
              type="button"
              className="font-medium text-indigo-600 hover:underline dark:text-indigo-400"
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login')
                setError(null)
              }}
            >
              {mode === 'login' ? 'Regístrate' : 'Inicia sesión'}
            </button>
          </p>

          {waking && (
            <p role="status" className="mt-6 flex items-center gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
              <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-amber-500" />
              Despertando el servidor de la demo… puede tardar hasta un minuto.
            </p>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Usuario</span>
              <input
                className={inputClass}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                {...(mode === 'register' && {
                  minLength: 3,
                  maxLength: 50,
                  // Browsers compile this with the "v" flag, where "-" must be escaped.
                  pattern: String.raw`[A-Za-z0-9_.\-]+`,
                  title: 'De 3 a 50 caracteres: letras, números, punto, guion o guion bajo',
                })}
              />
            </label>

            {mode === 'register' && (
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium">Correo</span>
                <input
                  type="email"
                  className={inputClass}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </label>
            )}

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Contraseña</span>
              <input
                type="password"
                className={inputClass}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
                {...(mode === 'register' && { minLength: 8, maxLength: 72 })}
              />
            </label>

            {error && (
              <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-indigo-500 disabled:opacity-60"
            >
              {loading ? 'Un momento…' : mode === 'login' ? 'Entrar' : 'Crear cuenta'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
