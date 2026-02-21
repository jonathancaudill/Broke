import { streamText } from 'ai'
import { model } from '@/lib/server/ai'
import { personality } from '@/lib/server/prompts'

export const maxDuration = 60

export async function POST(request: Request) {
  const { query } = (await request.json()) as { query: string }
  console.log(`[api/direct-chat] query: "${query.slice(0, 80)}"`)

  const result = streamText({
    model: model(),
    system: personality,
    prompt: query
  })

  const encoder = new TextEncoder()
  let tokenCount = 0

  const stream = new ReadableStream({
    async start(controller) {
      try {
        for await (const chunk of result.textStream) {
          tokenCount++
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ type: 'text-delta', textDelta: chunk })}\n\n`)
          )
        }
        console.log(`[api/direct-chat] done, ${tokenCount} chunks streamed`)
      } catch (err) {
        console.error(`[api/direct-chat] stream error:`, err)
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ type: 'error', message: String(err) })}\n\n`)
        )
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
