import { createOpenAI } from '@ai-sdk/openai';
import { env } from '$env/dynamic/private';

export function model() {
	const provider = createOpenAI({ apiKey: env.OPENAI_API_KEY });
	return provider(env.OPENAI_MODEL || 'gpt-4o');
}

export function embeddingModel() {
	const provider = createOpenAI({ apiKey: env.OPENAI_API_KEY });
	return provider.embedding('text-embedding-3-small');
}
