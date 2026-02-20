import { streamText, type CoreMessage } from 'ai';
import { model } from '$lib/server/ai';
import { orchestratorPrompt } from '$lib/server/prompts';
import { ragQueryTool } from '$lib/server/tools/rag-query';
import { createCallAgentTool } from '$lib/server/tools/call-agent';

export const orchestratorTools = {
	rag_query: ragQueryTool,
	call_agent: createCallAgentTool()
};

export function createSingleStep(messages: CoreMessage[]) {
	return streamText({
		model: model(),
		system: orchestratorPrompt,
		messages,
		tools: orchestratorTools
	});
}
