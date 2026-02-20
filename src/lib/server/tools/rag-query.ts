import { tool } from 'ai';
import { z } from 'zod';
import { searchDocuments } from '$lib/server/knowledge/store';

export const ragQueryTool = tool({
	description:
		"Search the knowledge base for information about Jonathan — " +
		"his resume, projects, skills, and background. " +
		"Specify a collection to narrow results: 'resume', 'projects', " +
		"'skills', or 'background'. Use 'all' to search everything.",
	parameters: z.object({
		query: z.string().describe('The search query describing what information you need.'),
		collection: z
			.enum(['resume', 'projects', 'skills', 'background', 'all'])
			.describe('Which knowledge collection to search.')
	}),
	execute: async ({ query, collection }) => {
		const results = await searchDocuments(query, collection);

		if (results.length === 0) {
			return 'No relevant information found in the knowledge base.';
		}

		return results
			.map((r) => `[${r.source ?? 'unknown'} / ${r.section ?? ''}]\n${r.content}`)
			.join('\n---\n');
	}
});
