export type DocumentStatus = 'processing' | 'ready' | 'failed'

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  is_active: boolean
  role: { id: number; name: string }
}

export interface DocumentItem {
  id: number
  filename: string
  content_type: string
  status: DocumentStatus
  error_message: string | null
  uploaded_at: string
}

export interface Source {
  chunk_id: number
  document_id: number
  filename: string
  chunk_index: number
  content: string
  distance: number
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources: Source[] | null
  created_at: string
}

export interface ConversationSummary {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationDetail extends ConversationSummary {
  messages: Message[]
}

export interface ConversationTurn {
  conversation: ConversationSummary
  user_message: Message
  assistant_message: Message
}
