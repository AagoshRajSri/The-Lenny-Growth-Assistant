// ─── Domain types ────────────────────────────────────────────────────────────

export interface Session {
  id: number
  title: string | null
  model_provider: string | null
  created_at: string
}

export interface Citation {
  episode_title: string
  url: string
}

export interface ChatMessage {
  id: string // local UUID for rendering before DB id arrives
  db_id?: number
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  artifact_id?: number | null
  created_at: string
  streaming?: boolean
}

export interface Artifact {
  id: number
  type: 'markdown' | 'html'
  sanitized_content: string | null
  created_at: string
}

export interface ConfigResponse {
  llm_provider: string
  ollama_model: string
  ollama_base_url: string
}

export interface ProviderError {
  error: boolean
  message: string
  details?: string
}
