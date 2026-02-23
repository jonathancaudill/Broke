import { createClient, type SupabaseClient } from '@supabase/supabase-js'

let client: SupabaseClient | null = null

function getClient(): SupabaseClient {
  if (!client) {
    client = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!)
  }
  return client
}

export type QaLogSource = 'chat' | 'ask' | 'direct-chat'

export interface QaLogEntry {
  source: QaLogSource
  question: string
  answer: string | null
  agent?: string | null
}

export async function logQa(entry: QaLogEntry): Promise<void> {
  try {
    const { error } = await getClient().from('qa_log').insert({
      source: entry.source,
      question: entry.question,
      answer: entry.answer ?? null,
      agent: entry.agent ?? null
    })
    if (error) console.error('[qa-log] insert failed:', error.message)
  } catch (err) {
    console.error('[qa-log] error:', err)
  }
}
