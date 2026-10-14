import { useEffect, useRef, useState, type FormEvent } from 'react'

import type { Message } from '../api/types'
import { FileIcon, MenuIcon, SendIcon } from './icons'
import { Logo } from './Logo'
import { MessageBubble, TypingIndicator } from './MessageBubble'

interface Props {
  title: string
  messages: Message[]
  pending: boolean
  error: string | null
  readyDocuments: number
  onSend: (question: string) => void
  onOpenSidebar: () => void
  onOpenDocuments: () => void
}

const SUGGESTIONS = [
  'Resume los puntos clave del documento',
  '¿Qué fechas importantes se mencionan?',
  '¿Quiénes son los responsables y cómo contactarlos?',
]

export function ChatView({
  title,
  messages,
  pending,
  error,
  readyDocuments,
  onSend,
  onOpenSidebar,
  onOpenDocuments,
}: Props) {
  const [draft, setDraft] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, pending])

  function submit(event?: FormEvent) {
    event?.preventDefault()
    const question = draft.trim()

    if (!question || pending) return

    onSend(question)
    setDraft('')

    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const empty = messages.length === 0 && !pending

  return (
    <div className="flex h-full min-w-0 flex-col">
      <header className="flex items-center gap-2 border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <button
          onClick={onOpenSidebar}
          className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 lg:hidden dark:hover:bg-zinc-800"
          aria-label="Abrir conversaciones"
        >
          <MenuIcon />
        </button>
        <h1 className="min-w-0 flex-1 truncate text-sm font-semibold">{title}</h1>
        <button
          onClick={onOpenDocuments}
          className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-zinc-600 hover:bg-zinc-100 xl:hidden dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          <FileIcon /> Documentos
        </button>
      </header>

      <div className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
          {empty && (
            <div className="flex flex-col items-center pt-12 text-center">
              <Logo className="h-12 w-12" />
              <h2 className="mt-4 text-xl font-semibold tracking-tight">¿Qué quieres saber?</h2>
              <p className="mt-1 max-w-md text-sm text-zinc-500">
                {readyDocuments > 0
                  ? `Respondo usando tus ${readyDocuments} documento(s) indexados y te muestro las fuentes.`
                  : 'Sube un PDF en el panel de documentos para empezar.'}
              </p>
              {readyDocuments > 0 && (
                <div className="mt-8 grid w-full gap-2 sm:grid-cols-3">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => onSend(suggestion)}
                      className="rounded-xl border border-zinc-200 p-3 text-left text-sm text-zinc-600 transition hover:border-indigo-300 hover:bg-indigo-50/50 dark:border-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-900"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {pending && <TypingIndicator />}

          {error && (
            <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
              {error}
            </p>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      <form onSubmit={submit} className="mx-auto w-full max-w-3xl px-4 pb-4">
        <div className="flex items-end gap-2 rounded-2xl border border-zinc-300 bg-white p-2 shadow-sm transition focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 dark:border-zinc-700 dark:bg-zinc-900">
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                submit()
              }
            }}
            rows={1}
            maxLength={2000}
            placeholder="Pregunta sobre tus documentos…"
            className="max-h-[200px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none"
            aria-label="Pregunta"
          />
          <button
            type="submit"
            disabled={!draft.trim() || pending}
            className="rounded-xl bg-indigo-600 p-2.5 text-white transition hover:bg-indigo-500 disabled:opacity-40"
            aria-label="Enviar"
          >
            <SendIcon />
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-zinc-500">
          Respuestas generadas localmente con Ollama. Verifica las fuentes.
        </p>
      </form>
    </div>
  )
}
