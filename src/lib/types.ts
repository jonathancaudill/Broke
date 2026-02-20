export interface Message {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	type: 'chat' | 'command';
	toolCalls?: ToolCall[];
}

export interface ToolCall {
	id: string;
	name: string;
	args: Record<string, unknown>;
	result?: string;
}
