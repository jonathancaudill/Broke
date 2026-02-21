import { NextResponse, type NextRequest } from 'next/server'
import { callAgent } from '@/lib/server/agents/registry'

export async function POST(request: NextRequest) {
  const { agent, query } = (await request.json()) as { agent: string; query: string }

  try {
    const result = await callAgent(agent, query)
    return NextResponse.json({ result })
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
