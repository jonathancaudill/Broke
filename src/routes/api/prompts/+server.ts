import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { allPrompts } from '$lib/server/prompts';

export const GET: RequestHandler = async ({ url }) => {
	const agentName = url.searchParams.get('agent');

	if (agentName) {
		const entry = allPrompts[agentName];
		if (!entry) {
			return json({ error: `Unknown agent: ${agentName}` }, { status: 404 });
		}
		return json({ content: `[${entry.name}]\n${entry.prompt}` });
	}

	const all = Object.values(allPrompts)
		.map((e) => `── ${e.name} ──\n${e.prompt.length > 500 ? e.prompt.slice(0, 500) + '\n...' : e.prompt}`)
		.join('\n\n');

	return json({ content: all });
};
