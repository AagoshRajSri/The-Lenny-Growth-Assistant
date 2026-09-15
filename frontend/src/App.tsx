import { useState, useRef, useEffect, useCallback } from 'react'
import { ProviderBadge } from './components/ProviderBadge'
import { Sidebar } from './components/Sidebar'
import { MessageBubble } from './components/MessageBubble'
import { ArtifactPane } from './components/ArtifactPane'
import { useConfig, useSessions, useChat } from './hooks'

import './App.css'

// ─── Welcome screen ───────────────────────────────────────────────────────────
function WelcomeScreen({ onNew }: { onNew: () => void }) {
  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--spacing-8)',
      gap: 'var(--spacing-4)',
      color: 'var(--color-text-muted)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 40 }}>📡</div>
      <h1 style={{ fontSize: 'var(--text-xl)', color: 'var(--color-text-primary)', margin: 0 }}>
        Lenny Growth Assistant
      </h1>
      <p style={{ fontSize: 'var(--text-base)', maxWidth: 420, lineHeight: 'var(--leading-normal)' }}>
        Ask anything sourced from Lenny's Podcast & Newsletter transcripts. Every answer includes episode citations.
      </p>
      <button id="welcome-new-chat" className="btn-primary" onClick={onNew}>
        Start a conversation
      </button>
    </div>
  )
}

// ─── Chat input bar ───────────────────────────────────────────────────────────
interface InputBarProps {
  onSend: (text: string) => void
  disabled: boolean
  streaming: boolean
}

function InputBar({ onSend, disabled, streaming }: InputBarProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const submit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  return (
    <div style={{
      borderTop: '1px solid var(--color-border)',
      padding: 'var(--spacing-3) var(--spacing-4)',
      display: 'flex',
      gap: 'var(--spacing-2)',
      alignItems: 'flex-end',
      background: 'var(--color-surface)',
      flexShrink: 0,
    }}>
      <textarea
        id="chat-input"
        ref={textareaRef}
        value={value}
        placeholder={streaming ? 'Streaming response…' : 'Ask about growth, product, or strategy…'}
        disabled={disabled}
        rows={1}
        aria-label="Chat message input"
        className="input"
        style={{
          resize: 'none',
          overflowY: 'hidden',
          flex: 1,
          minHeight: 44,
          maxHeight: 160,
        }}
        onChange={e => {
          setValue(e.target.value)
          e.target.style.height = 'auto'
          e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
        }}
        onKeyDown={e => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            submit()
          }
        }}
      />
      <button
        id="chat-send-btn"
        className="btn-primary"
        onClick={submit}
        disabled={disabled || !value.trim()}
        style={{ height: 44, paddingLeft: 16, paddingRight: 16, flexShrink: 0 }}
        aria-label="Send message"
      >
        {streaming ? '…' : '→'}
      </button>
    </div>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────
export default function App() {
  const config = useConfig()
  const { sessions, createSession } = useSessions()
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeArtifactId, setActiveArtifactId] = useState<number | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  const { messages, streaming, error, setError, sendMessage } = useChat(activeSessionId)

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleNewChat = useCallback(async () => {
    try {
      const session = await createSession('New Chat')
      setActiveSessionId(session.id)
      setActiveArtifactId(null)
    } catch (e) {
      console.error(e)
    }
  }, [createSession])

  const handleSend = useCallback((text: string) => {
    sendMessage(text, (artifactId) => {
      setActiveArtifactId(artifactId)
    })
  }, [sendMessage])

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--color-bg)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Sidebar */}
      {!sidebarCollapsed && (
        <Sidebar
          sessions={sessions}
          activeId={activeSessionId}
          onSelect={id => { setActiveSessionId(id); setActiveArtifactId(null) }}
          onNew={handleNewChat}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(true)}
        />
      )}

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

        {/* Top bar */}
        <header
          role="banner"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 16px',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            flexShrink: 0,
            gap: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {sidebarCollapsed && (
              <button
                id="sidebar-open-btn"
                aria-label="Open sidebar"
                onClick={() => setSidebarCollapsed(false)}
                style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 18, padding: 4 }}
              >
                ☰
              </button>
            )}
            <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)' }}>
              {activeSessionId ? `Session #${activeSessionId}` : 'Lenny Growth Assistant'}
            </span>
          </div>
          <ProviderBadge config={config} />
        </header>

        {/* Chat + Artifact split */}
        <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

          {/* Chat column */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>

            {/* Messages */}
            <div
              ref={scrollRef}
              id="message-list"
              role="log"
              aria-live="polite"
              aria-label="Conversation"
              style={{ flex: 1, overflowY: 'auto', padding: 'var(--spacing-6) var(--spacing-6)' }}
            >
              {!activeSessionId ? (
                <WelcomeScreen onNew={handleNewChat} />
              ) : messages.length === 0 && !streaming ? (
                <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', marginTop: 64, fontSize: 'var(--text-sm)' }}>
                  Send a message to begin
                </div>
              ) : (
                messages.map(m => (
                  <MessageBubble
                    key={m.id}
                    message={m}
                    onOpenArtifact={setActiveArtifactId}
                  />
                ))
              )}
            </div>

            {/* Error bar */}
            {error && (
              <div
                role="alert"
                style={{
                  margin: '0 var(--spacing-4)',
                  padding: '10px 14px',
                  background: 'rgb(248 81 73 / 0.1)',
                  border: '1px solid var(--color-error)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--color-error)',
                  fontSize: 'var(--text-sm)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <span>⚠ {error}</span>
                <button
                  onClick={() => setError(null)}
                  aria-label="Dismiss error"
                  style={{ background: 'none', border: 'none', color: 'var(--color-error)', cursor: 'pointer', fontWeight: 700 }}
                >
                  ×
                </button>
              </div>
            )}

            {/* Input */}
            {activeSessionId && (
              <InputBar
                onSend={handleSend}
                disabled={!activeSessionId}
                streaming={streaming}
              />
            )}
          </div>

          {/* Artifact pane */}
          <ArtifactPane
            artifactId={activeArtifactId}
            onClose={() => setActiveArtifactId(null)}
          />
        </div>
      </div>

      {/* Blink keyframe */}
      <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>
    </div>
  )
}
