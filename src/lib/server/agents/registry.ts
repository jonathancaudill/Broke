import { generateText } from 'ai';
import { model } from '$lib/server/ai';
import { ragQueryTool } from '$lib/server/tools/rag-query';
import { webSearchTool } from '$lib/server/tools/web-search';
import { checkAvailabilityTool, bookMeetingTool } from '$lib/server/tools/scheduling';
import { deepRagPrompt, researcherPrompt, schedulingPrompt } from '$lib/server/prompts';
import type { CoreTool } from 'ai';

interface AgentConfig {
	name: string;
	description: string;
	systemPrompt: string;
	tools: Record<string, CoreTool>;
	maxSteps: number;
}

const agents: Record<string, AgentConfig> = {
	deep_rag: {
		name: 'deep_rag',
		description:
			'Performs thorough, multi-pass retrieval for complex questions that need cross-referencing or exhaustive coverage.',
		systemPrompt: deepRagPrompt,
		tools: { rag_query: ragQueryTool },
		maxSteps: 15
	},
	researcher: {
		name: 'researcher',
		description:
			"Performs web research to answer questions that need current or external information beyond Jonathan's knowledge base.",
		systemPrompt: researcherPrompt,
		tools: { web_search: webSearchTool },
		maxSteps: 10
	},
	scheduling: {
		name: 'scheduling',
		description:
			"Handles meeting scheduling — checks Jonathan's availability and books meetings on his calendar.",
		systemPrompt: schedulingPrompt,
		tools: { check_availability: checkAvailabilityTool, book_meeting: bookMeetingTool },
		maxSteps: 10
	}
};

export async function callAgent(name: string, query: string): Promise<string> {
	const agent = agents[name];
	if (!agent) {
		const available = Object.keys(agents).join(', ');
		return `Agent '${name}' not found. Available: ${available}`;
	}

	const result = await generateText({
		model: model(),
		system: agent.systemPrompt,
		prompt: query,
		tools: agent.tools,
		maxSteps: agent.maxSteps
	});

	return result.text;
}

export function listAgents(): Array<{ name: string; description: string }> {
	return Object.values(agents).map((a) => ({ name: a.name, description: a.description }));
}

export function getAgentNames(): string[] {
	return Object.keys(agents);
}

export function getAgentConfig(name: string): AgentConfig | undefined {
	return agents[name];
}
