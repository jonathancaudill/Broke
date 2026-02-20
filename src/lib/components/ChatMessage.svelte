<script lang="ts">
	import { marked } from 'marked';
	import type { Message } from '$lib/types';

	let { message, debug = false }: { message: Message; debug?: boolean } = $props();

	const isUser = $derived(message.role === 'user');
	const isSystem = $derived(message.role === 'system');
	const isCommand = $derived(message.type === 'command');

	const html = $derived(
		isUser || isSystem || isCommand
			? ''
			: (marked.parse(message.content || '', { async: false }) as string)
	);

	function describeToolCall(name: string, args: Record<string, unknown>): string {
		if (name === 'rag_query') {
			return `searching knowledge base (${args.collection || 'all'})`;
		}
		if (name === 'call_agent') {
			return `talking to ${args.agent_name}`;
		}
		if (name === 'check_availability') {
			return 'checking calendar';
		}
		if (name === 'book_meeting') {
			return 'booking meeting';
		}
		if (name === 'web_search') {
			return `searching the web`;
		}
		return name;
	}
</script>

{#if isCommand}
	{#if isUser}
		<div class="message-row user">
			<div class="bubble command-bubble">{message.content}</div>
		</div>
	{:else}
		<div class="system-message">
			<pre>{message.content}</pre>
		</div>
	{/if}
{:else if isSystem}
	<div class="system-message">
		<pre>{message.content}</pre>
	</div>
{:else}
	<div class="message-row" class:user={isUser}>
		<div class="bubble" class:bubble-user={isUser} class:bubble-assistant={!isUser}>
			{#if isUser}
				{message.content}
			{:else}
				{@html html}
			{/if}
		</div>
	</div>

	{#if debug && !isUser && message.toolCalls?.length}
		<div class="debug-tools">
			{#each message.toolCalls as tc}
				<div class="tool-call">
					<span class="tool-icon">🔧</span>
					<span>{describeToolCall(tc.name, tc.args)}</span>
					{#if tc.result}
						<details>
							<summary>result</summary>
							<pre>{tc.result}</pre>
						</details>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
{/if}
