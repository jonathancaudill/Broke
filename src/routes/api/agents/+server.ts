import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { listAgents } from '$lib/server/agents/registry';

export const GET: RequestHandler = async () => {
	return json({ agents: listAgents() });
};
