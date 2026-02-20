import type { RequestHandler } from './$types';
import { streamText } from 'ai';
import { model } from '$lib/server/ai';
import { personality } from '$lib/server/prompts';

export const POST: RequestHandler = async ({ request }) => {
	const { query } = (await request.json()) as { query: string };

	const result = streamText({
		model: model(),
		system: personality,
		prompt: query,
		temperature: 0.7
	});

	const encoder = new TextEncoder();

	const stream = new ReadableStream({
		async start(controller) {
			try {
				for await (const chunk of result.textStream) {
					controller.enqueue(
						encoder.encode(`data: ${JSON.stringify({ type: 'text-delta', textDelta: chunk })}\n\n`)
					);
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
