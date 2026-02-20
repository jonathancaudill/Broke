import { streamText, type CoreMessage } from 'ai';
import { model } from '$lib/server/ai';
import { orchestratorPrompt } from '$lib/server/prompts';
import { ragQueryTool } from '$lib/server/tools/rag-query';
import { createCallAgentTool } from '$lib/server/tools/call-agent';

export function createOrchestratorStream(messages: CoreMessage[]) {
	return streamText({
		model: model(),
		system: orchestratorPrompt,
		messages,
		tools: {
			rag_query: ragQueryTool,
			call_agent: createCallAgentTool()
		},
		maxSteps: 12
	});
}
