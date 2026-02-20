import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { embed } from 'ai';
import { embeddingModel } from '$lib/server/ai';
import { env } from '$env/dynamic/private';

let client: SupabaseClient | null = null;

function getClient(): SupabaseClient {
	if (!client) {
		client = createClient(env.SUPABASE_URL!, env.SUPABASE_SERVICE_ROLE_KEY!);
	}
	return client;
}

export interface DocumentMatch {
	id: string;
	content: string;
	collection: string;
	section: string | null;
	source: string | null;
	similarity: number;
}

export async function searchDocuments(
	query: string,
	collection: string = 'all',
	count: number = 5
): Promise<DocumentMatch[]> {
	const { embedding } = await embed({
		model: embeddingModel(),
		value: query
	});

	const { data, error } = await getClient().rpc('match_documents', {
		query_embedding: embedding,
		match_count: count,
		filter_collection: collection === 'all' ? null : collection
	});

	if (error) throw new Error(`Supabase search failed: ${error.message}`);
	return (data as DocumentMatch[]) ?? [];
}
