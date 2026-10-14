import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/client'
import type { DocumentItem } from '../api/types'

const POLL_INTERVAL_MS = 2000

/**
 * The user's documents. While any of them is still being indexed the list
 * is polled, so status badges move to "ready" / "failed" on their own.
 */
export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(
    () =>
      api.listDocuments().then(
        (items) => {
          setDocuments(items.sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at)))
          setError(null)
        },
        (err: unknown) => {
          setError(err instanceof Error ? err.message : 'Error al cargar documentos')
        },
      ),
    [],
  )

  useEffect(() => {
    void refresh()
  }, [refresh])

  const hasProcessing = documents.some((document) => document.status === 'processing')

  useEffect(() => {
    if (!hasProcessing) return

    const timer = window.setInterval(() => void refresh(), POLL_INTERVAL_MS)

    return () => window.clearInterval(timer)
  }, [hasProcessing, refresh])

  return { documents, error, refresh }
}
