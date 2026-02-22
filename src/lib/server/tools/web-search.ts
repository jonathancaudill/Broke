import { tool, jsonSchema } from 'ai'

const TAVILY_API_URL = 'https://api.tavily.com/search'

interface TavilyResult {
  title: string
  url: string
  content: string
  score?: number
}

interface TavilyResponse {
  query: string
  answer?: string
  results: TavilyResult[]
  response_time?: number
}

async function searchWeb(query: string): Promise<string> {
  const apiKey = process.env.TAVILY_API_KEY
  if (!apiKey) {
    return (
      'Web search is not configured: TAVILY_API_KEY is missing. ' +
      'Add it to .env to enable the researcher to search the web.'
    )
  }

  const res = await fetch(TAVILY_API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: apiKey,
      query,
      max_results: 8,
      search_depth: 'basic'
    })
  })

  if (!res.ok) {
    const err = await res.text()
    console.error('[web-search] Tavily API error:', res.status, err)
    return `Web search failed (${res.status}). Please try a different query or try again later.`
  }

  const data = (await res.json()) as TavilyResponse
  const results = data.results ?? []

  if (results.length === 0) {
    return `No results found for: "${query}"`
  }

  const answer = data.answer
  const snippets = results
    .map((r, i) => `${i + 1}. [${r.title}](${r.url})\n   ${r.content}`)
    .join('\n\n')

  return answer
    ? `Answer: ${answer}\n\nSources:\n${snippets}`
    : `Search results for "${query}":\n\n${snippets}`
}

export const webSearchTool = tool({
  description:
    'Search the web for current or external information. ' +
    "Use this when the question requires up-to-date data that " +
    "isn't in Jonathan's knowledge base.",
  inputSchema: jsonSchema<{ query: string }>({
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'The search query to look up.'
      }
    },
    required: ['query']
  }),
  execute: async ({ query }) => searchWeb(query)
})
