export interface Message {
	id: string
	role: 'user' | 'assistant' | 'system'
	content: string
	type: 'chat' | 'command'
	toolCalls?: ToolCall[]
	pending?: boolean
}

export interface ToolCall {
	id: string
	name: string
	args: Record<string, unknown>
	result?: string
}

export interface ChatMessage {
	role: 'user' | 'assistant' | 'tool'
	content: string | ChatContent[]
}

export interface ChatContent {
	type: 'text' | 'tool-call' | 'tool-result'
	text?: string
	toolCallId?: string
	toolName?: string
	input?: unknown
	output?: { type: 'text'; value: string }
}
