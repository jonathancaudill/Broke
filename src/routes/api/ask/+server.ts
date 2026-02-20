import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { callAgent } from '$lib/server/agents/registry';

export const POST: RequestHandler = async ({ request }) => {
	const { agent, query } = (await request.json()) as { agent: string; query: string };

	try {
		const result = await callAgent(agent, query);
		return json({ result });
	} catch (err) {
		return json({ error: String(err) }, { status: 500 });
	}
};
