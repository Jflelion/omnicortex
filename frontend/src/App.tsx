import { useCallback, useEffect, useRef, useState } from 'react'

import { api, ApiError, getToken, setToken, setUnauthorizedHandler } from './api/client'
import type { ConversationSummary, Message, User } from './api/types'
import { AuthScreen } from './components/AuthScreen'
import { ChatView } from './components/ChatView'
import { DocumentsPanel } from './components/DocumentsPanel'
import { Sidebar } from './components/Sidebar'
import { useDocuments } from './hooks/useDocuments'

const NEW_CONVERSATION_TITLE = 'Nueva conversación'

function errorText(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Error inesperado'
}

export default function App() {
  const [token, setTokenState] = useState(getToken)
  const [user, setUser] = useState<User | null>(null)

  const logout = useCallback(() => {
    setToken(null)
    setTokenState(null)
    setUser(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    return () => setUnauthorizedHandler(null)
  }, [logout])

  useEffect(() => {
    if (!token) return

    api.me().then(setUser).catch(logout)
  }, [token, logout])

  if (!token) {
    return (
      <AuthScreen
        onAuthenticated={(newToken) => {
          setToken(newToken)
          setTokenState(newToken)
        }}
      />
    )
  }

  if (!user) {
    return <div className="flex h-full items-center justify-center text-sm text-zinc-500">Cargando…</div>
  }

  return <Workspace user={user} onLogout={logout} />
}

function Workspace({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [documentsOpen, setDocumentsOpen] = useState(false)

  const { documents, error: documentsError, refresh: refreshDocuments } = useDocuments()

  // Guards against a slow answer landing in a conversation the user left.
  const activeIdRef = useRef(activeId)

  function activate(id: number | null) {
    activeIdRef.current = id
    setActiveId(id)
  }

  useEffect(() => {
    api.listConversations().then(setConversations).catch((err) => setError(errorText(err)))
  }, [])

  async function selectConversation(id: number) {
    setSidebarOpen(false)
    setError(null)
    activate(id)
    setMessages([])

    try {
      const detail = await api.getConversation(id)
      if (activeIdRef.current === id) setMessages(detail.messages)
    } catch (err) {
      setError(errorText(err))
    }
  }

  function newConversation() {
    setSidebarOpen(false)
    activate(null)
    setMessages([])
    setError(null)
  }

  function upsertConversation(conversation: ConversationSummary) {
    setConversations((list) => [conversation, ...list.filter((c) => c.id !== conversation.id)])
  }

  async function send(question: string) {
    setError(null)
    setPending(true)

    const optimistic: Message = {
      id: -Date.now(),
      role: 'user',
      content: question,
      sources: null,
      created_at: new Date().toISOString(),
    }
    setMessages((list) => [...list, optimistic])

    try {
      let conversationId = activeId

      if (conversationId === null) {
        const created = await api.createConversation()
        conversationId = created.id
        upsertConversation(created)
        activate(created.id)
      }

      const turn = await api.sendMessage(conversationId, question)
      upsertConversation(turn.conversation)

      if (activeIdRef.current === conversationId) {
        setMessages((list) => [
          ...list.filter((m) => m.id !== optimistic.id),
          turn.user_message,
          turn.assistant_message,
        ])
      }
    } catch (err) {
      // The API stores nothing when the answer fails; drop the bubble.
      setMessages((list) => list.filter((m) => m.id !== optimistic.id))
      setError(`No se pudo responder «${question}»: ${errorText(err)}`)
    } finally {
      setPending(false)
    }
  }

  async function rename(id: number, title: string) {
    try {
      upsertConversation(await api.renameConversation(id, title))
    } catch (err) {
      setError(errorText(err))
    }
  }

  async function remove(id: number) {
    try {
      await api.deleteConversation(id)
      setConversations((list) => list.filter((c) => c.id !== id))
      if (activeId === id) newConversation()
    } catch (err) {
      setError(errorText(err))
    }
  }

  const activeTitle = conversations.find((c) => c.id === activeId)?.title ?? NEW_CONVERSATION_TITLE
  const readyDocuments = documents.filter((d) => d.status === 'ready').length

  const overlay = (open: boolean, close: () => void) =>
    open && <div className="fixed inset-0 z-30 bg-zinc-950/40 backdrop-blur-sm" onClick={close} aria-hidden="true" />

  return (
    <div className="flex h-full overflow-hidden">
      {overlay(sidebarOpen, () => setSidebarOpen(false))}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 border-r border-zinc-200 transition-transform lg:static lg:z-auto lg:w-64 lg:translate-x-0 dark:border-zinc-800 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar
          user={user}
          conversations={conversations}
          activeId={activeId}
          onSelect={(id) => void selectConversation(id)}
          onNew={newConversation}
          onRename={(id, title) => void rename(id, title)}
          onDelete={(id) => void remove(id)}
          onLogout={onLogout}
        />
      </aside>

      <main className="min-w-0 flex-1">
        <ChatView
          key={activeId ?? 'new'}
          title={activeTitle}
          messages={messages}
          pending={pending}
          error={error}
          readyDocuments={readyDocuments}
          onSend={(question) => void send(question)}
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenDocuments={() => setDocumentsOpen(true)}
        />
      </main>

      {overlay(documentsOpen, () => setDocumentsOpen(false))}
      <aside
        className={`fixed inset-y-0 right-0 z-40 w-80 max-w-[85vw] border-l border-zinc-200 bg-white transition-transform xl:static xl:z-auto xl:translate-x-0 dark:border-zinc-800 dark:bg-zinc-950 ${
          documentsOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <DocumentsPanel
          documents={documents}
          loadError={documentsError}
          onChange={refreshDocuments}
          onClose={() => setDocumentsOpen(false)}
        />
      </aside>
    </div>
  )
}
