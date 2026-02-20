<script lang="ts">
	import { tick } from 'svelte';
	import ChatMessage from '$lib/components/ChatMessage.svelte';
	import ChatInput from '$lib/components/ChatInput.svelte';
	import type { Message, ToolCall } from '$lib/types';

	let messages = $state<Message[]>([]);
	let input = $state('');
	let isLoading = $state(false);
	let debugMode = $state(false);
	let reasoningEffort = $state<string | null>(null);
	let streamStatus = $state<string | null>(null);
	let chatContainer: HTMLElement | undefined = $state();

	const MEMORY_WINDOW = 20;

	const HELP_TEXT = `commands:
  /debug              toggle debug mode
  /clear              reset conversation
  /agents             list available agents
  /thinking [level]   set reasoning effort (low / medium / high)
  /ask <agent> <query> run a single agent in isolation
  /chat <query>       talk to the llm directly (no tools)
  /prompt [agent]     show system prompt (all or one)
  /help               show this message`;

	async function scrollToBottom() {
		await tick();
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	}

	function addSystemMessage(content: string) {
		messages.push({
			id: crypto.randomUUID(),
			role: 'system',
			content,
			type: 'command'
		});
		scrollToBottom();
	}

	function describeToolCall(name: string, args: Record<string, unknown>): string {
		if (name === 'rag_query') return `searching knowledge base (${args.collection || 'all'})`;
		if (name === 'call_agent') return `talking to ${args.agent_name}`;
		if (name === 'check_availability') return 'checking calendar';
		if (name === 'book_meeting') return 'booking meeting';
		if (name === 'web_search') return 'searching the web';
		return name;
	}

	async function parseSSEStream(response: Response, msg: Message) {
		const reader = response.body!.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });
			const parts = buffer.split('\n\n');
			buffer = parts.pop() || '';

			for (const part of parts) {
				for (const line of part.split('\n')) {
					if (!line.startsWith('data: ')) continue;
					const data = line.slice(6);
					if (data === '[DONE]') continue;

					try {
						const event = JSON.parse(data);

						if (event.type === 'text-delta') {
							msg.content += event.textDelta;
							streamStatus = null;
							scrollToBottom();
						} else if (event.type === 'tool-call') {
							streamStatus = describeToolCall(event.toolName, event.args) + '...';
							if (msg.toolCalls) {
								msg.toolCalls.push({
									id: event.toolCallId,
									name: event.toolName,
									args: event.args
								});
							}
							scrollToBottom();
						} else if (event.type === 'tool-result') {
							streamStatus = null;
							if (msg.toolCalls) {
								const tc = msg.toolCalls.find(
									(t: ToolCall) => t.id === event.toolCallId
								);
								if (tc) tc.result = event.result;
							}
						} else if (event.type === 'error') {
							msg.content += `\n\nerror: ${event.message}`;
							streamStatus = null;
						}
					} catch {
						/* skip malformed events */
					}
				}
			}
		}
	}

	async function sendChat(text: string) {
		messages.push({
			id: crypto.randomUUID(),
			role: 'user',
			content: text,
			type: 'chat'
		});

		const assistantMsg: Message = {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: '',
			type: 'chat',
			toolCalls: []
		};
		messages.push(assistantMsg);
		isLoading = true;
		streamStatus = null;
		scrollToBottom();

		const chatMessages = messages
			.filter((m) => m.type === 'chat' && m.content.trim())
			.slice(-MEMORY_WINDOW)
			.map((m) => ({ role: m.role, content: m.content }));

		try {
			const response = await fetch('/api/chat', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ messages: chatMessages })
			});

			if (!response.ok) {
				assistantMsg.content = `error: ${response.status} ${response.statusText}`;
				return;
			}

			await parseSSEStream(response, assistantMsg);
		} catch (err) {
			assistantMsg.content = `error: ${err}`;
		} finally {
			isLoading = false;
			streamStatus = null;
			scrollToBottom();
		}
	}

	async function streamFromEndpoint(endpoint: string, body: Record<string, unknown>) {
		const assistantMsg: Message = {
			id: crypto.randomUUID(),
			role: 'assistant',
			content: '',
			type: 'chat',
			toolCalls: []
		};
		messages.push(assistantMsg);
		isLoading = true;
		streamStatus = null;
		scrollToBottom();

		try {
			const response = await fetch(endpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});

			if (!response.ok) {
				assistantMsg.content = `error: ${response.status} ${response.statusText}`;
				return;
			}

			await parseSSEStream(response, assistantMsg);
		} catch (err) {
			assistantMsg.content = `error: ${err}`;
		} finally {
			isLoading = false;
			streamStatus = null;
			scrollToBottom();
		}
	}

	async function handleAskCommand(text: string) {
		const rest = text.slice(5).trim();
		const spaceIdx = rest.indexOf(' ');
		if (spaceIdx === -1) {
			addSystemMessage('usage: /ask <agent> <query>');
			return;
		}
		const agent = rest.slice(0, spaceIdx).toLowerCase();
		const query = rest.slice(spaceIdx + 1).trim();

		isLoading = true;
		scrollToBottom();

		try {
			const response = await fetch('/api/ask', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ agent, query })
			});
			const data = await response.json();
			if (data.error) {
				addSystemMessage(`error: ${data.error}`);
			} else {
				addSystemMessage(data.result);
			}
		} catch (err) {
			addSystemMessage(`error: ${err}`);
		} finally {
			isLoading = false;
			scrollToBottom();
		}
	}

	async function handleCommand(text: string) {
		messages.push({
			id: crypto.randomUUID(),
			role: 'user',
			content: text,
			type: 'command'
		});
		scrollToBottom();

		const low = text.toLowerCase().trim();

		if (low === '/debug') {
			debugMode = !debugMode;
			addSystemMessage(`debug mode: ${debugMode ? 'ON' : 'OFF'}`);
			return;
		}

		if (low === '/clear') {
			messages = [];
			return;
		}

		if (low === '/help') {
			addSystemMessage(HELP_TEXT);
			return;
		}

		if (low === '/agents') {
			try {
				const response = await fetch('/api/agents');
				const data = await response.json();
				const list = data.agents
					.map((a: { name: string; description: string }) => `  ${a.name} — ${a.description}`)
					.join('\n');
				addSystemMessage(list);
			} catch {
				addSystemMessage('failed to fetch agent list');
			}
			return;
		}

		if (low.startsWith('/thinking')) {
			const level = text.slice(9).trim().toLowerCase();
			if (!level) {
				addSystemMessage(
					`reasoning effort: ${reasoningEffort || 'default'}\noptions: low, medium, high`
				);
			} else if (['low', 'medium', 'high'].includes(level)) {
				reasoningEffort = level;
				addSystemMessage(`reasoning effort → ${level}`);
			} else {
				addSystemMessage('invalid. choose from: low, medium, high');
			}
			return;
		}

		if (low.startsWith('/ask ')) {
			await handleAskCommand(text);
			return;
		}

		if (low.startsWith('/chat ')) {
			const query = text.slice(6).trim();
			if (!query) {
				addSystemMessage('usage: /chat <query>');
				return;
			}
			await streamFromEndpoint('/api/direct-chat', { query });
			return;
		}

		if (low.startsWith('/prompt')) {
			const agent = text.slice(7).trim().toLowerCase();
			try {
				const url = agent ? `/api/prompts?agent=${agent}` : '/api/prompts';
				const response = await fetch(url);
				const data = await response.json();
				if (data.error) {
					addSystemMessage(`error: ${data.error}`);
				} else {
					addSystemMessage(data.content);
				}
			} catch {
				addSystemMessage('failed to fetch prompt');
			}
			return;
		}

		addSystemMessage('unknown command. type /help for available commands.');
	}

	async function handleSubmit(text: string) {
		if (!text.trim()) return;

		if (text.trim().startsWith('/')) {
			await handleCommand(text.trim());
		} else {
			await sendChat(text.trim());
		}
	}
</script>

<svelte:head>
	<title>broke</title>
</svelte:head>

<div class="chat-app">
	<header class="chat-header">
		<h1>broke</h1>
		{#if debugMode}
			<span class="debug-badge">debug</span>
		{/if}
	</header>

	<div class="chat-messages" bind:this={chatContainer}>
		{#if messages.length === 0}
			<div class="empty-state">
				<p>hey, i'm broke. ask me about jonathan.</p>
				<p class="hint">type /help for commands</p>
			</div>
		{/if}

		{#each messages as message (message.id)}
			<ChatMessage {message} debug={debugMode} />
		{/each}

		{#if streamStatus}
			<div class="stream-status">{streamStatus}</div>
		{/if}

		{#if isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content}
			<div class="typing-indicator-wrap">
				<div class="typing-indicator">
					<span></span>
					<span></span>
					<span></span>
				</div>
			</div>
		{/if}
	</div>

	<ChatInput bind:value={input} onsubmit={handleSubmit} disabled={isLoading} />
</div>
