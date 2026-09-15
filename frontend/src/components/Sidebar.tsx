import type { Session } from '../types'

interface SidebarProps {
  sessions: Session[]
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  collapsed: boolean
  onToggle: () => void
}

function formatTime(iso: string) {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 60_000) return 'just now'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return d.toLocaleDateString()
}

export function Sidebar({ sessions, activeId, onSelect, onNew, collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      aria-label="Session sidebar"
      style={{
        width: collapsed ? 0 : 240,
        minWidth: collapsed ? 0 : 240,
        overflow: 'hidden',
        borderRight: '1px solid var(--color-border)',
        background: 'var(--color-surface)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 200ms cubic-bezier(0.4,0,0.2,1), min-width 200ms cubic-bezier(0.4,0,0.2,1)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '14px 12px 10px',
          borderBottom: '1px solid var(--color-border)',
          flexShrink: 0,
        }}
      >
        <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)', whiteSpace: 'nowrap' }}>
          Lenny Assistant
        </span>
        <button
          id="sidebar-toggle"
          aria-label="Close sidebar"
          onClick={onToggle}
          style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: 4, lineHeight: 1 }}
        >
          ←
        </button>
      </div>

      {/* New Chat button */}
      <div style={{ padding: '10px 10px 6px' }}>
        <button
          id="new-chat-btn"
          className="btn-primary"
          onClick={onNew}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          + New Chat
        </button>
      </div>

      {/* Session list */}
      <nav
        aria-label="Past sessions"
        style={{ flex: 1, overflowY: 'auto', padding: '4px 6px' }}
      >
        {sessions.length === 0 && (
          <p style={{ color: 'var(--color-text-disabled)', fontSize: 'var(--text-xs)', padding: '8px 6px' }}>
            No sessions yet
          </p>
        )}
        {sessions.map(s => (
          <button
            key={s.id}
            id={`session-${s.id}`}
            onClick={() => onSelect(s.id)}
            aria-current={s.id === activeId ? 'page' : undefined}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              background: s.id === activeId ? 'var(--color-accent-subtle)' : 'transparent',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              padding: '8px 10px',
              cursor: 'pointer',
              marginBottom: 2,
              transition: 'background 100ms',
            }}
            onMouseEnter={e => {
              if (s.id !== activeId)
                (e.currentTarget as HTMLButtonElement).style.background = 'var(--color-surface-hover)'
            }}
            onMouseLeave={e => {
              if (s.id !== activeId)
                (e.currentTarget as HTMLButtonElement).style.background = 'transparent'
            }}
          >
            <div style={{
              fontSize: 'var(--text-sm)',
              color: s.id === activeId ? 'var(--color-accent)' : 'var(--color-text-primary)',
              fontWeight: s.id === activeId ? 500 : 400,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {s.title ?? 'Untitled'}
            </div>
            <div className="source-meta" style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
              {formatTime(s.created_at)}
            </div>
          </button>
        ))}
      </nav>
    </aside>
  )
}
