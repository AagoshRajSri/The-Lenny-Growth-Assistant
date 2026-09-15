import type { ConfigResponse } from '../types'

interface ProviderBadgeProps {
  config: ConfigResponse | null
}

export function ProviderBadge({ config }: ProviderBadgeProps) {
  if (!config) {
    return (
      <span
        className="model-tag"
        style={{
          color: 'var(--color-text-disabled)',
          fontSize: 'var(--text-xs)',
          padding: '2px 8px',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-full)',
        }}
      >
        connecting…
      </span>
    )
  }

  const isOllama = config.llm_provider === 'ollama'
  const label = isOllama
    ? `ollama · ${config.ollama_model}`
    : 'anthropic · claude'

  return (
    <span
      aria-label={`Active provider: ${label}`}
      className="model-tag"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        fontSize: 'var(--text-xs)',
        fontFamily: 'var(--font-mono)',
        padding: '2px 8px',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-full)',
        color: isOllama ? 'var(--color-success)' : 'var(--color-accent)',
        background: isOllama
          ? 'rgb(63 185 80 / 0.10)'
          : 'var(--color-accent-subtle)',
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: isOllama ? 'var(--color-success)' : 'var(--color-accent)',
          flexShrink: 0,
        }}
      />
      {label}
    </span>
  )
}
