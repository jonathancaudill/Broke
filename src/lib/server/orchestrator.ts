import { streamText } from 'ai'
import { model } from '@/lib/server/ai'
import { getOrchestratorPrompt } from '@/lib/server/prompts'
import { ragQueryTool } from '@/lib/server/tools/rag-query'
import { createCallAgentTool } from '@/lib/server/tools/call-agent'

export const orchestratorTools = {
  rag_query: ragQueryTool,
  call_agent: createCallAgentTool()
}

export function createSingleStep(messages: { role: string; content: string | unknown[] }[]) {
  return streamText({
    model: model(),
    system: getOrchestratorPrompt(),
    messages: messages as never,
    tools: orchestratorTools
  })
}
