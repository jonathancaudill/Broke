import { NextResponse, type NextRequest } from 'next/server'
import { allPrompts } from '@/lib/server/prompts'

export async function GET(request: NextRequest) {
  const agentName = request.nextUrl.searchParams.get('agent')

  if (agentName) {
    const entry = allPrompts[agentName]
    if (!entry) {
      return NextResponse.json({ error: `Unknown agent: ${agentName}` }, { status: 404 })
    }
    return NextResponse.json({ content: `[${entry.name}]\n${entry.prompt}` })
  }

  const all = Object.values(allPrompts)
    .map((e) => `── ${e.name} ──\n${e.prompt.length > 500 ? e.prompt.slice(0, 500) + '\n...' : e.prompt}`)
    .join('\n\n')

  return NextResponse.json({ content: all })
}
