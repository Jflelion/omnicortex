import { useRef, useState, type DragEvent } from 'react'

import { api, ApiError } from '../api/client'
import type { DocumentItem, DocumentStatus } from '../api/types'
import { FileIcon, RetryIcon, TrashIcon, UploadIcon, XIcon } from './icons'

interface Props {
  documents: DocumentItem[]
  loadError: string | null
  onChange: () => Promise<void>
  onClose: () => void
}

const STATUS_STYLES: Record<DocumentStatus, { label: string; className: string; dot: string }> = {
  processing: {
    label: 'Procesando',
    className: 'bg-amber-50 text-amber-700 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-300',
    dot: 'bg-amber-500 animate-pulse',
  },
  ready: {
    label: 'Listo',
    className: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-300',
    dot: 'bg-emerald-500',
  },
  failed: {
    label: 'Fallido',
    className: 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-500/10 dark:text-red-300',
    dot: 'bg-red-500',
  },
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  const style = STATUS_STYLES[status]

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${style.className}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {style.label}
    </span>
  )
}

export function DocumentsPanel({ documents, loadError, onChange, onClose }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(0)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function upload(files: FileList | File[]) {
    setError(null)

    for (const file of Array.from(files)) {
      setUploading((n) => n + 1)

      try {
        await api.uploadDocument(file)
      } catch (err) {
        setError(`${file.name}: ${err instanceof ApiError ? err.message : 'error al subir'}`)
      } finally {
        setUploading((n) => n - 1)
      }

      await onChange()
    }
  }

  async function run(action: () => Promise<unknown>) {
    setError(null)

    try {
      await action()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error inesperado')
    }

    await onChange()
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)

    if (event.dataTransfer.files.length) void upload(event.dataTransfer.files)
  }

  const readyCount = documents.filter((d) => d.status === 'ready').length

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
        <div>
          <h2 className="text-sm font-semibold">Documentos</h2>
          <p className="text-xs text-zinc-500">
            {readyCount} de {documents.length} listos para consultar
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 xl:hidden dark:hover:bg-zinc-800"
          aria-label="Cerrar panel de documentos"
        >
          <XIcon />
        </button>
      </header>

      <div className="p-4">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`flex w-full flex-col items-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center transition ${
            dragging
              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10'
              : 'border-zinc-300 hover:border-indigo-400 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900'
          }`}
        >
          <UploadIcon className="h-6 w-6 text-indigo-500" />
          <span className="text-sm font-medium">
            {uploading ? `Subiendo ${uploading} archivo(s)…` : 'Arrastra PDFs o haz clic'}
          </span>
          <span className="text-xs text-zinc-500">Se indexan en segundo plano</span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => {
            if (e.target.files) void upload(e.target.files)
            e.target.value = ''
          }}
        />

        {(error || loadError) && (
          <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700 dark:bg-red-950/50 dark:text-red-300">
            {error || loadError}
          </p>
        )}
      </div>

      <ul className="scroll-thin flex-1 space-y-2 overflow-y-auto px-4 pb-4">
        {documents.length === 0 && (
          <li className="py-8 text-center text-sm text-zinc-500">Aún no has subido documentos.</li>
        )}

        {documents.map((document) => (
          <li
            key={document.id}
            className="group rounded-lg border border-zinc-200 p-3 dark:border-zinc-800"
          >
            <div className="flex items-start gap-2.5">
              <FileIcon className="mt-0.5 h-4 w-4 shrink-0 text-zinc-400" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium" title={document.filename}>
                  {document.filename}
                </p>
                <div className="mt-1.5 flex items-center gap-2">
                  <StatusBadge status={document.status} />
                  <span className="text-xs text-zinc-500">
                    {new Date(document.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
                {document.status === 'failed' && document.error_message && (
                  <p className="mt-2 text-xs text-zinc-500">{document.error_message}</p>
                )}
              </div>

              <div className="flex shrink-0 gap-0.5 opacity-100 transition sm:opacity-0 sm:group-hover:opacity-100 sm:focus-within:opacity-100">
                {document.status === 'failed' && (
                  <button
                    onClick={() => void run(() => api.reindexDocument(document.id))}
                    className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-indigo-600 dark:hover:bg-zinc-800"
                    aria-label={`Reintentar ${document.filename}`}
                    title="Reintentar indexación"
                  >
                    <RetryIcon className="h-3.5 w-3.5" />
                  </button>
                )}
                <button
                  onClick={() => {
                    if (confirm(`¿Eliminar "${document.filename}"?`)) {
                      void run(() => api.deleteDocument(document.id))
                    }
                  }}
                  className="rounded-md p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-red-600 dark:hover:bg-zinc-800"
                  aria-label={`Eliminar ${document.filename}`}
                  title="Eliminar"
                >
                  <TrashIcon className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
