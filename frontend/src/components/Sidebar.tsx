import { useState } from 'react'

import type { ConversationSummary, User } from '../api/types'
import { ChatIcon, LogoutIcon, PencilIcon, PlusIcon, TrashIcon } from './icons'
import { Logo } from './Logo'

interface Props {
  user: User
  conversations: ConversationSummary[]
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onRename: (id: number, title: string) => void
  onDelete: (id: number) => void
  onLogout: () => void
}

function groupLabel(isoDate: string): string {
  const days = Math.floor((Date.now() - new Date(isoDate).getTime()) / 86_400_000)

  if (days < 1) return 'Hoy'
  if (days < 7) return 'Últimos 7 días'
  return 'Anteriores'
}

export function Sidebar({ user, conversations, activeId, onSelect, onNew, onRename, onDelete, onLogout }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null)
  const [draft, setDraft] = useState('')

  function commitRename(id: number) {
    const title = draft.trim()
    setEditingId(null)

    if (title) onRename(id, title)
  }

  const groups = new Map<string, ConversationSummary[]>()

  for (const conversation of conversations) {
    const label = groupLabel(conversation.updated_at)
    groups.set(label, [...(groups.get(label) ?? []), conversation])
  }

  return (
    <div className="flex h-full flex-col bg-zinc-50 dark:bg-zinc-900">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <Logo className="h-7 w-7" />
        <span className="font-semibold tracking-tight">OmniCortex</span>
      </div>

      <div className="px-3">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-500"
        >
          <PlusIcon /> Nueva conversación
        </button>
      </div>

      <nav className="scroll-thin mt-4 flex-1 overflow-y-auto px-3 pb-4" aria-label="Conversaciones">
        {conversations.length === 0 && (
          <p className="px-2 py-6 text-center text-xs text-zinc-500">Tus conversaciones aparecerán aquí.</p>
        )}

        {[...groups.entries()].map(([label, items]) => (
          <div key={label} className="mb-4">
            <p className="px-2 pb-1 text-xs font-medium text-zinc-500">{label}</p>
            <ul className="space-y-0.5">
              {items.map((conversation) => {
                const active = conversation.id === activeId

                return (
                  <li key={conversation.id} className="group relative">
                    {editingId === conversation.id ? (
                      <input
                        autoFocus
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        onBlur={() => commitRename(conversation.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') commitRename(conversation.id)
                          if (e.key === 'Escape') setEditingId(null)
                        }}
                        maxLength={200}
                        className="w-full rounded-lg border border-indigo-500 bg-white px-2.5 py-2 text-sm outline-none dark:bg-zinc-950"
                        aria-label="Nuevo título"
                      />
                    ) : (
                      <>
                        <button
                          onClick={() => onSelect(conversation.id)}
                          className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 pr-14 text-left text-sm transition ${
                            active
                              ? 'bg-white font-medium shadow-sm ring-1 ring-zinc-200 dark:bg-zinc-800 dark:ring-zinc-700'
                              : 'text-zinc-700 hover:bg-zinc-200/60 dark:text-zinc-300 dark:hover:bg-zinc-800/60'
                          }`}
                        >
                          <ChatIcon className="h-3.5 w-3.5 shrink-0 text-zinc-400" />
                          <span className="truncate">{conversation.title}</span>
                        </button>
                        <div className="absolute right-1.5 top-1/2 flex -translate-y-1/2 gap-0.5 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 sm:focus-within:opacity-100">
                          <button
                            onClick={() => {
                              setDraft(conversation.title)
                              setEditingId(conversation.id)
                            }}
                            className="rounded p-1 text-zinc-500 hover:text-indigo-600"
                            aria-label={`Renombrar ${conversation.title}`}
                          >
                            <PencilIcon className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`¿Eliminar "${conversation.title}"?`)) onDelete(conversation.id)
                            }}
                            className="rounded p-1 text-zinc-500 hover:text-red-600"
                            aria-label={`Eliminar ${conversation.title}`}
                          >
                            <TrashIcon className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-3 border-t border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
          {user.username.slice(0, 1).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{user.username}</p>
          <p className="truncate text-xs text-zinc-500">{user.role.name}</p>
        </div>
        <button
          onClick={onLogout}
          className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-200 dark:hover:bg-zinc-800"
          aria-label="Cerrar sesión"
          title="Cerrar sesión"
        >
          <LogoutIcon />
        </button>
      </div>
    </div>
  )
}
