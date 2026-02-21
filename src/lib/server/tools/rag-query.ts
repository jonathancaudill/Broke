import { tool, jsonSchema } from 'ai'
import { searchDocuments } from '@/lib/server/knowledge/store'

export const ragQueryTool = tool({
  description:
    "Search the knowledge base for information about Jonathan — " +
    "his resume, projects, skills, and background. " +
    "Specify a collection to narrow results: 'resume', 'projects', " +
    "'skills', or 'background'. Use 'all' to search everything.",
  inputSchema: jsonSchema<{ query: string; collection: string }>({
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'The search query describing what information you need.'
      },
      collection: {
        type: 'string',
        enum: ['resume', 'projects', 'skills', 'background', 'all'],
        description: 'Which knowledge collection to search.'
      }
    },
    required: ['query', 'collection']
  }),
  execute: async ({ query, collection }) => {
    const results = await searchDocuments(query, collection)

    if (results.length === 0) {
      return 'No relevant information found in the knowledge base.'
    }

    return results
      .map((r) => `[${r.source ?? 'unknown'} / ${r.section ?? ''}]\n${r.content}`)
      .join('\n---\n')
  }
})
