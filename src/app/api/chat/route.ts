import { createSingleStep } from '@/lib/server/orchestrator'
import { logQa } from '@/lib/server/qa-log'

export const maxDuration = 60

const MAX_STEPS = 12

export async function POST(request: Request) {
  const { messages } = (await request.json()) as { messages: { role: string; content: string }[] }
  console.log(
    `[api/chat] received ${messages.length} messages, last: "${messages[messages.length - 1]?.content?.toString().slice(0, 80)}"`
  )

  const encoder = new TextEncoder()
  const currentMessages: { role: string; content: string | unknown[] }[] = [...messages]
  const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user')
  const question =
    typeof lastUserMessage?.content === 'string'
      ? lastUserMessage.content
      : Array.isArray(lastUserMessage?.content)
        ? (lastUserMessage.content as { text?: string }[]).map((c) => c.text ?? '').join('')
        : ''

  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: Record<string, unknown>) =>
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`))
      let fullAnswer = ''

      try {
        for (let step = 0; step < MAX_STEPS; step++) {
          console.log(`[api/chat] step ${step + 1}`)
          const result = createSingleStep(currentMessages)

          let stepText = ''
          const toolCalls: Array<{
            toolCallId: string
            toolName: string
            input: unknown
          }> = []
          const toolResults: Array<{
            toolCallId: string
            toolName: string
            output: unknown
          }> = []

          for await (const part of result.fullStream) {
            if (part.type === 'text-delta') {
              stepText += part.text
              send({ type: 'text-delta', textDelta: part.text })
            } else if (part.type === 'tool-call') {
              console.log(
                `[api/chat]   tool-call: ${part.toolName}(${JSON.stringify(part.input).slice(0, 200)})`
              )
              toolCalls.push({
                toolCallId: part.toolCallId,
                toolName: part.toolName,
                input: part.input
              })
              send({
                type: 'tool-call',
                toolCallId: part.toolCallId,
                toolName: part.toolName,
                args: part.input
              })
            } else if (part.type === 'tool-result') {
              const p = part as unknown as {
                toolCallId: string
                toolName: string
                output: unknown
              }
              const outputStr =
                typeof p.output === 'string'
                  ? p.output
                  : JSON.stringify(p.output)
              console.log(
                `[api/chat]   tool-result: ${p.toolName} -> ${outputStr.slice(0, 200)}`
              )
              toolResults.push({
                toolCallId: p.toolCallId,
                toolName: p.toolName,
                output: p.output
              })
              send({
                type: 'tool-result',
                toolCallId: p.toolCallId,
                toolName: p.toolName,
                result: outputStr.slice(0, 1000)
              })
            }
          }

          fullAnswer += stepText

          if (toolCalls.length === 0) {
            console.log(
              `[api/chat] step ${step + 1} done — no tool calls, final answer (${stepText.length} chars)`
            )
            if (question) await logQa({ source: 'chat', question, answer: fullAnswer || null })
            break
          }

          console.log(
            `[api/chat] step ${step + 1} done — ${toolCalls.length} tool call(s), continuing`
          )

          const assistantContent: Array<Record<string, unknown>> = []
          if (stepText) {
            assistantContent.push({ type: 'text', text: stepText })
          }
          for (const tc of toolCalls) {
            assistantContent.push({
              type: 'tool-call',
              toolCallId: tc.toolCallId,
              toolName: tc.toolName,
              input: tc.input
            })
          }
          currentMessages.push({
            role: 'assistant',
            content: assistantContent
          })

          const toolContent = toolResults.map((tr) => ({
            type: 'tool-result' as const,
            toolCallId: tr.toolCallId,
            toolName: tr.toolName,
            output: {
              type: 'text' as const,
              value: typeof tr.output === 'string' ? tr.output : JSON.stringify(tr.output)
            }
          }))
          currentMessages.push({
            role: 'tool',
            content: toolContent
          })
        }
      } catch (err) {
        console.error(`[api/chat] stream error:`, err)
        send({ type: 'error', message: String(err) })
      } finally {
        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
      }
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    }
  })
}
