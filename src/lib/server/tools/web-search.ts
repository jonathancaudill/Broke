import { tool } from 'ai';
import { z } from 'zod';

export const webSearchTool = tool({
	description:
		'Search the web for current or external information. ' +
		"Use this when the question requires up-to-date data that " +
		"isn't in Jonathan's knowledge base.",
	parameters: z.object({
		query: z.string().describe('The search query to look up.')
	}),
	execute: async ({ query }) => {
		return (
			`[STUB] Web search for: "${query}"\n\n` +
			'No real results — web search integration is not yet wired up.\n' +
			'When implemented, this tool will return summarised search results ' +
			'from a search API.'
		);
	}
});
