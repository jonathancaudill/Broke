import { tool } from 'ai';
import { z } from 'zod';
import { callAgent, getAgentNames } from '$lib/server/agents/registry';

export function createCallAgentTool() {
	const names = getAgentNames();
	return tool({
		description:
			'Call another specialist agent to get information or a second opinion. ' +
			`Available agents: ${names.join(', ')}`,
		parameters: z.object({
			agent_name: z.string().describe('Name of the agent to call.'),
			query: z.string().describe('The question or task to send to the agent.')
		}),
		execute: async ({ agent_name, query }) => {
			return await callAgent(agent_name, query);
		}
	});
}
