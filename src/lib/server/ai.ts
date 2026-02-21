import { createOpenAI } from '@ai-sdk/openai'

export function model() {
  const provider = createOpenAI({ apiKey: process.env.OPENAI_API_KEY })
  return provider.chat(process.env.OPENAI_MODEL || 'gpt-4o')
}

export function embeddingModel() {
  const provider = createOpenAI({ apiKey: process.env.OPENAI_API_KEY })
  return provider.embedding('text-embedding-3-small')
}
