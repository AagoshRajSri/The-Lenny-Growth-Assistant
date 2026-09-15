import { useState } from 'react'
import type { ChatMessage, Citation } from '../types'

// ─── Citation footnote ────────────────────────────────────────────────────────

function CitationRef({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false)

  return (
    <span style={{ position: 'relative', display: 'inline-block' }}>
      <button
        aria-label={`Citation ${index + 1}: ${citation.episode_title}`}
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'var(--color-accent-subtle)',
          color: 'var(--color-accent)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.65rem',
          padding: '1px 5px',
          cursor: 'pointer',
          verticalAlign: 'super',
          lineHeight: 1,
        }}
      >
        [{index + 1}]
      </button>
      {open && (
        <span
          role="tooltip"
          style={{
            position: 'absolute',
            bottom: '120%',
            left: 0,
            width: 260,
            background: 'var(--color-surface-raised)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 12px',
            zIndex: 50,
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)', marginBottom: 4 }}>
            {citation.episode_title}
          </div>
          <a
            href={citation.url}
            target="_blank"
            rel="noopener noreferrer"
            className="source-meta"
            style={{ fontSize: 'var(--text-xs)', color: 'var(--color-accent)', wordBreak: 'break-all' }}
          >
            {citation.url}
          </a>
        </span>
      )}
    </span>
  )
}

// ─── Streaming cursor ─────────────────────────────────────────────────────────

function StreamCursor() {
  return (
    <span
      aria-hidden="true"
      style={{
        display: 'inline-block',
        width: 2,
        height: '1.1em',
        background: 'var(--color-accent)',
        marginLeft: 2,
        verticalAlign: 'middle',
        borderRadius: 1,
        animation: 'blink 0.9s step-end infinite',
      }}
    />
  )
}

// ─── Single message ───────────────────────────────────────────────────────────

interface MessageBubbleProps {
  message: ChatMessage
  onOpenArtifact: (id: number) => void
}

const OUT_OF_SCOPE_PHRASES = [
  'not covered',
  "don't cover",
  'transcripts do not',
  'not in the transcripts',
  'cannot find information',
]

export function MessageBubble({ message, onOpenArtifact }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isOutOfScope = !isUser && OUT_OF_SCOPE_PHRASES.some(p =>
    message.content.toLowerCase().includes(p)
  )

  return (
    <article
      aria-label={`${isUser ? 'Your' : 'Assistant'} message`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 'var(--spacing-4)',
      }}
    >
      {/* Role label */}
      <div style={{
        fontSize: 'var(--text-xs)',
        fontFamily: 'var(--font-mono)',
        color: 'var(--color-text-muted)',
        marginBottom: 4,
        paddingLeft: isUser ? 0 : 2,
      }}>
        {isUser ? 'you' : 'lenny-assistant'}
      </div>

      {/* Bubble */}
      <div
        style={{
          maxWidth: '78%',
          background: isUser ? 'var(--color-accent-subtle)' : 'var(--color-surface)',
          border: `1px solid ${isOutOfScope ? 'var(--color-warning)' : 'var(--color-border)'}`,
          borderRadius: isUser
            ? 'var(--radius-lg) var(--radius-sm) var(--radius-lg) var(--radius-lg)'
            : 'var(--radius-sm) var(--radius-lg) var(--radius-lg) var(--radius-lg)',
          padding: '10px 14px',
          color: 'var(--color-text-primary)',
          fontSize: 'var(--text-base)',
          lineHeight: 'var(--leading-normal)',
          position: 'relative',
        }}
      >
        {/* Out-of-scope indicator */}
        {isOutOfScope && (
          <div style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--color-warning)',
            fontFamily: 'var(--font-mono)',
            marginBottom: 6,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}>
            ⚠ out of corpus
          </div>
        )}

        {/* Content */}
        <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {message.content}
          {message.streaming && <StreamCursor />}
        </span>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              sources:
            </span>
            {message.citations.map((c, i) => (
              <CitationRef key={i} citation={c} index={i} />
            ))}
          </div>
        )}

        {/* Artifact button */}
        {message.artifact_id != null && (
          <button
            id={`open-artifact-${message.artifact_id}`}
            onClick={() => onOpenArtifact(message.artifact_id!)}
            style={{
              marginTop: 10,
              display: 'block',
              fontSize: 'var(--text-xs)',
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-accent)',
              background: 'var(--color-accent-subtle)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: '4px 10px',
              cursor: 'pointer',
            }}
          >
            ↗ view artifact #{message.artifact_id}
          </button>
        )}
      </div>
    </article>
  )
}
