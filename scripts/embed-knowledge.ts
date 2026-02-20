import 'dotenv/config';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { createClient } from '@supabase/supabase-js';
import { embedMany } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';

const openai = createOpenAI({ apiKey: process.env.OPENAI_API_KEY! });
const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);

interface Chunk {
	id: string;
	content: string;
	collection: string;
	section: string;
	source: string;
}

const HEADING_RE = /^(#{1,3})\s+(.+)$/gm;

function chunkMarkdown(text: string, source: string, collection: string): Chunk[] {
	const positions: Array<[number, string]> = [];
	let match: RegExpExecArray | null;

	while ((match = HEADING_RE.exec(text)) !== null) {
		positions.push([match.index, match[2]]);
	}
	HEADING_RE.lastIndex = 0;

	if (positions.length === 0) {
		return [{ id: `${collection}_0`, content: text.trim(), collection, section: 'root', source }];
	}

	const chunks: Chunk[] = [];

	const preamble = text.slice(0, positions[0][0]).trim();
	if (preamble) {
		chunks.push({
			id: `${collection}_${chunks.length}`,
			content: preamble,
			collection,
			section: 'preamble',
			source
		});
	}

	for (let i = 0; i < positions.length; i++) {
		const [start, heading] = positions[i];
		const end = i + 1 < positions.length ? positions[i + 1][0] : text.length;
		const body = text.slice(start, end).trim();

		if (body) {
			chunks.push({
				id: `${collection}_${chunks.length}`,
				content: body,
				collection,
				section: heading,
				source
			});
		}
	}

	return chunks;
}

async function main() {
	const knowledgeDir = join(process.cwd(), 'knowledge_data');
	const files = readdirSync(knowledgeDir)
		.filter((f) => f.endsWith('.md'))
		.sort();

	console.log(`found ${files.length} knowledge files`);

	const allChunks: Chunk[] = [];

	for (const file of files) {
		const text = readFileSync(join(knowledgeDir, file), 'utf-8');
		const collection = file.replace('.md', '');
		const chunks = chunkMarkdown(text, file, collection);
		allChunks.push(...chunks);
		console.log(`  ${file}: ${chunks.length} chunks`);
	}

	console.log(`\nembedding ${allChunks.length} chunks...`);

	const { embeddings } = await embedMany({
		model: openai.embedding('text-embedding-3-small'),
		values: allChunks.map((c) => c.content)
	});

	console.log(`embedding complete. upserting to supabase...`);

	const rows = allChunks.map((chunk, i) => ({
		id: chunk.id,
		content: chunk.content,
		collection: chunk.collection,
		section: chunk.section,
		source: chunk.source,
		embedding: embeddings[i]
	}));

	for (let i = 0; i < rows.length; i += 100) {
		const batch = rows.slice(i, i + 100);
		const { error } = await supabase.from('documents').upsert(batch);
		if (error) {
			console.error('error upserting:', error);
			throw error;
		}
		console.log(`  upserted ${Math.min(i + 100, rows.length)}/${rows.length}`);
	}

	console.log('\ndone!');
}

main().catch(console.error);
