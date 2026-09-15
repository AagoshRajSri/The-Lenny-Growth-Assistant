import { useState, useEffect } from 'react'
import type { Artifact } from '../types'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface ArtifactPaneProps {
  artifactId: number | null
  onClose: () => void
}

export function ArtifactPane({ artifactId, onClose }: ArtifactPaneProps) {
  const [artifact, setArtifact] = useState<Artifact | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)

  useEffect(() => {
    if (!artifactId) return
    setLoading(true)
    setError(null)
    setShowRaw(false)

    fetch(`${API}/api/artifacts/${artifactId}`)
      .then(async r => {
        if (!r.ok) throw new Error(`Artifact not found (${r.status})`)
        return r.json() as Promise<Artifact>
      })
      .then(setArtifact)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [artifactId])

  if (!artifactId) return null

  const isOpen = !!artifactId

  return (
    <aside
      id="artifact-pane"
      aria-label="Artifact viewer"
      role="complementary"
      style={{
        width: isOpen ? 520 : 0,
        minWidth: isOpen ? 520 : 0,
        overflow: 'hidden',
        borderLeft: '1px solid var(--color-border)',
        background: 'var(--color-surface)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 200ms cubic-bezier(0.4,0,0.2,1)',
        flexShrink: 0,
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 14px',
        borderBottom: '1px solid var(--color-border)',
        flexShrink: 0,
        gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 'var(--text-xs)',
            color: 'var(--color-text-muted)',
          }}>
            artifact #{artifactId}
          </span>
          {artifact && (
            <span
              className={`badge-info`}
              style={{ textTransform: 'uppercase', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)' }}
            >
              {artifact.type}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* Raw Source toggle */}
          {artifact && (
            <button
              id="artifact-raw-toggle"
              aria-pressed={showRaw}
              onClick={() => setShowRaw(r => !r)}
              style={{
                fontSize: 'var(--text-xs)',
                fontFamily: 'var(--font-mono)',
                padding: '3px 8px',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                background: showRaw ? 'var(--color-surface-hover)' : 'transparent',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
              }}
            >
              {showRaw ? 'rendered' : 'raw source'}
            </button>
          )}

          <button
            id="artifact-close-btn"
            aria-label="Close artifact pane"
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
          >
            ×
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 18px' }}>
        {loading && (
          <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>Loading artifact…</p>
        )}

        {error && (
          <div
            role="alert"
            style={{
              background: 'rgb(248 81 73 / 0.1)',
              border: '1px solid var(--color-error)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
              color: 'var(--color-error)',
              fontSize: 'var(--text-sm)',
            }}
          >
            {error}
          </div>
        )}

        {artifact && !loading && (
          <>
            {showRaw ? (
              /* Raw source — always safe, it's plaintext */
              <pre
                style={{
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                  fontSize: 'var(--text-xs)',
                  color: 'var(--color-text-muted)',
                  background: 'var(--color-surface-raised)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--spacing-4)',
                  margin: 0,
                }}
              >
                {artifact.sanitized_content ?? '(empty)'}
              </pre>
            ) : artifact.type === 'html' ? (
              /* Sandboxed HTML: sandbox strictly excludes allow-scripts */
              <iframe
                id="artifact-iframe"
                title={`Artifact ${artifactId}`}
                sandbox="allow-same-origin"
                srcDoc={`<!DOCTYPE html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'"><style>body{font-family:system-ui;font-size:14px;color:#e6edf3;background:#1f2937;padding:16px;margin:0;line-height:1.6}</style></head><body>${artifact.sanitized_content ?? ''}</body></html>`}
                style={{
                  width: '100%',
                  height: '100%',
                  minHeight: 400,
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--color-surface-raised)',
                }}
              />
            ) : (
              /* Markdown rendered as preformatted text (Phase 11+ will add marked.js) */
              <div
                style={{
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-base)',
                  lineHeight: 'var(--leading-normal)',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {artifact.sanitized_content}
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  )
}
