import { useState, useEffect, useCallback } from 'react'
import type { ConfigResponse, Session, ChatMessage, Citation } from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ─── Config hook ─────────────────────────────────────────────────────────────
export function useConfig() {
  const [config, setConfig] = useState<ConfigResponse | null>(null)

  useEffect(() => {
    fetch(`${API}/api/config`)
      .then(r => r.json())
      .then(setConfig)
      .catch(() => setConfig(null))
  }, [])

  return config
}

// ─── Sessions hook ───────────────────────────────────────────────────────────
export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([])

  const refresh = useCallback(() => {
    // Sessions are stored locally for now; replace with API listing when available.
    const raw = localStorage.getItem('sessions')
    if (raw) setSessions(JSON.parse(raw))
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const addSession = useCallback((s: Session) => {
    setSessions(prev => {
      const next = [s, ...prev]
      localStorage.setItem('sessions', JSON.stringify(next))
      return next
    })
  }, [])

  const createSession = useCallback(async (title?: string): Promise<Session> => {
    const res = await fetch(`${API}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title ?? 'New Chat', model_provider: 'ollama' }),
    })
    if (!res.ok) throw new Error(`Failed to create session: ${res.status}`)
    const session: Session = await res.json()
    addSession(session)
    return session
  }, [addSession])

  return { sessions, createSession, refresh }
}

// ─── Chat hook ───────────────────────────────────────────────────────────────
export function useChat(sessionId: number | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (
    text: string,
    onArtifact: (id: number) => void,
  ) => {
    if (!sessionId || streaming) return
    setError(null)

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      streaming: true,
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setStreaming(true)

    const res = await fetch(`${API}/api/sessions/${sessionId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    })

    if (!res.ok || !res.body) {
      const body = await res.json().catch(() => ({}))
      const msg = body?.error?.message ?? `HTTP ${res.status}`
      setError(msg)
      setStreaming(false)
      setMessages(prev => prev.filter(m => m.id !== assistantMsg.id))
      return
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let citations: Citation[] = []

    const updateAssistant = (patch: Partial<ChatMessage>) =>
      setMessages(prev =>
        prev.map(m => m.id === assistantMsg.id ? { ...m, ...patch } : m)
      )

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('event: token')) continue
          if (line.startsWith('event: error')) continue
          if (line.startsWith('event: done')) continue
          if (!line.startsWith('data: ')) continue

          const data = line.slice(6)

          // Check for structured error
          try {
            const parsed = JSON.parse(data)
            if (parsed?.error) {
              setError(parsed.error?.message ?? 'Provider error')
              updateAssistant({ streaming: false, content: '' })
              setStreaming(false)
              return
            }
            // done event payload
            if ('citations' in parsed) {
              citations = parsed.citations ?? []
              const artifactId: number | null = parsed.artifact_id ?? null
              updateAssistant({ citations, artifact_id: artifactId, streaming: false })
              if (artifactId) onArtifact(artifactId)
              break
            }
          } catch {
            // plain token text — accumulate directly
            setMessages(prev =>
              prev.map(m =>
                m.id === assistantMsg.id
                  ? { ...m, content: m.content + data }
                  : m
              )
            )
          }
        }
      }
    } finally {
      updateAssistant({ streaming: false })
      setStreaming(false)
    }
  }, [sessionId, streaming])

  return { messages, setMessages, streaming, error, setError, sendMessage }
}
