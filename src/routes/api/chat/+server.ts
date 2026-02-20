import type { RequestHandler } from './$types';
import { createOrchestratorStream } from '$lib/server/orchestrator';
import type { CoreMessage } from 'ai';

export const POST: RequestHandler = async ({ request }) => {
	const { messages } = (await request.json()) as { messages: CoreMessage[] };

	const result = createOrchestratorStream(messages);
	const encoder = new TextEncoder();

	const stream = new ReadableStream({
		async start(controller) {
			try {
				for await (const part of result.fullStream) {
					let event: Record<string, unknown> | null = null;

					switch (part.type) {
						case 'text-delta':
							event = { type: 'text-delta', textDelta: part.textDelta };
							break;
						case 'tool-call':
							event = {
								type: 'tool-call',
								toolCallId: part.toolCallId,
								toolName: part.toolName,
								args: part.args
							};
							break;
						case 'tool-result':
							event = {
								type: 'tool-result',
								toolCallId: part.toolCallId,
								toolName: part.toolName,
								result:
									typeof part.result === 'string'
										? part.result.slice(0, 1000)
										: JSON.stringify(part.result).slice(0, 1000)
							};
							break;
						case 'step-finish':
							event = { type: 'step-finish' };
							break;
						case 'finish':
							event = { type: 'finish' };
							break;
					}

					if (event) {
						controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
					}
				}
			} catch (err) {
				controller.enqueue(
					encoder.encode(`data: ${JSON.stringify({ type: 'error', message: String(err) })}\n\n`)
				);
			} finally {
				controller.enqueue(encoder.encode('data: [DONE]\n\n'));
				controller.close();
			}
		}
	});

	return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			Connection: 'keep-alive'
		}
	});
};
