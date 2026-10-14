import { useState } from 'react'

import type { Message, Source } from '../api/types'
import { ChevronIcon, FileIcon } from './icons'
import { Logo } from './Logo'

/** Cosine distance (0 = identical) shown as a 0–100 % relevance figure. */
function relevance(distance: number): number {
  return Math.round(Math.max(0, Math.min(1, 1 - distance)) * 100)
}

function SourceCard({ source, index }: { source: Source; index: number }) {
  const [open, setOpen] = useState(false)
  const score = relevance(source.distance)

  return (
    <li className="rounded-lg border border-zinc-200 bg-white text-sm dark:border-zinc-800 dark:bg-zinc-900">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left"
        aria-expanded={open}
      >
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-indigo-50 text-xs font-semibold text-indigo-700 dark:bg-indigo-500/15 dark:text-indigo-300">
          {index}
        </span>
        <FileIcon className="h-3.5 w-3.5 shrink-0 text-zinc-400" />
        <span className="min-w-0 flex-1 truncate">
          {source.filename || `Documento ${source.document_id}`}
          <span className="text-zinc-500"> · fragmento {source.chunk_index + 1}</span>
        </span>
        <span className="flex shrink-0 items-center gap-1.5 text-xs text-zinc-500" title="Similitud semántica">
          <span className="h-1.5 w-12 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <span className="block h-full rounded-full bg-indigo-500" style={{ width: `${score}%` }} />
          </span>
          {score}%
        </span>
        <ChevronIcon className={`h-3.5 w-3.5 shrink-0 text-zinc-400 transition ${open ? 'rotate-90' : ''}`} />
      </button>
      {open && (
        <p className="whitespace-pre-wrap border-t border-zinc-200 px-3 py-2.5 text-xs leading-relaxed text-zinc-600 dark:border-zinc-800 dark:text-zinc-400">
          {source.content}
        </p>
      )}
    </li>
  )
}

export function MessageBubble({ message }: { message: Message }) {
  const [showSources, setShowSources] = useState(false)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-indigo-600 px-4 py-2.5 text-sm text-white">
          {message.content}
        </p>
      </div>
    )
  }

  const sources = message.sources ?? []

  return (
    <div className="flex gap-3">
      <Logo className="mt-0.5 h-7 w-7 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>

        {sources.length > 0 && (
          <div className="mt-3">
            <button
              onClick={() => setShowSources(!showSources)}
              className="inline-flex items-center gap-1 text-xs font-medium text-zinc-500 hover:text-indigo-600"
              aria-expanded={showSources}
            >
              <ChevronIcon className={`h-3 w-3 transition ${showSources ? 'rotate-90' : ''}`} />
              {sources.length} {sources.length === 1 ? 'fuente' : 'fuentes'}
            </button>

            {showSources && (
              <ol className="mt-2 space-y-1.5">
                {sources.map((source, i) => (
                  <SourceCard key={source.chunk_id} source={source} index={i + 1} />
                ))}
              </ol>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export function TypingIndicator() {
  return (
    <div className="flex gap-3" aria-live="polite">
      <Logo className="h-7 w-7 shrink-0" />
      <div className="flex items-center gap-1 py-2" aria-label="Generando respuesta">
        {[0, 1, 2].map((i) => (
          <span key={i} className="typing-dot h-2 w-2 rounded-full bg-zinc-400" />
        ))}
        <span className="ml-2 text-xs text-zinc-500">Buscando en tus documentos…</span>
      </div>
    </div>
  )
}
