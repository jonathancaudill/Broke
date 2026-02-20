import { tool, jsonSchema } from 'ai';
import { callAgent, getAgentNames } from '$lib/server/agents/registry';

export function createCallAgentTool() {
	const names = getAgentNames();
	return tool({
		description:
			'Call another specialist agent to get information or a second opinion. ' +
			`Available agents: ${names.join(', ')}`,
		inputSchema: jsonSchema<{ agent_name: string; query: string }>({
			type: 'object',
			properties: {
				agent_name: {
					type: 'string',
					description: 'Name of the agent to call.'
				},
				query: {
					type: 'string',
					description: 'The question or task to send to the agent.'
				}
			},
			required: ['agent_name', 'query']
		}),
		execute: async ({ agent_name, query }) => {
			return await callAgent(agent_name, query);
		}
	});
}
