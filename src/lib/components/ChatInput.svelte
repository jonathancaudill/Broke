<script lang="ts">
	let {
		value = $bindable(''),
		onsubmit,
		disabled = false
	}: {
		value: string;
		onsubmit: (text: string) => void;
		disabled?: boolean;
	} = $props();

	let inputEl: HTMLTextAreaElement | undefined = $state();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			submit();
		}
	}

	function submit() {
		const text = value.trim();
		if (!text || disabled) return;
		onsubmit(text);
		value = '';
		if (inputEl) {
			inputEl.style.height = 'auto';
		}
	}

	function autoResize(e: Event) {
		const el = e.target as HTMLTextAreaElement;
		el.style.height = 'auto';
		el.style.height = Math.min(el.scrollHeight, 120) + 'px';
	}
</script>

<div class="input-bar">
	<textarea
		bind:this={inputEl}
		bind:value
		onkeydown={handleKeydown}
		oninput={autoResize}
		placeholder="message broke..."
		rows="1"
		{disabled}
	></textarea>
	<button onclick={submit} disabled={disabled || !value.trim()} class="send-button" aria-label="Send message">
		<svg viewBox="0 0 24 24" width="18" height="18" fill="none">
			<circle cx="12" cy="12" r="11" fill="currentColor" />
			<path d="M12 16V8M8 12l4-4 4 4" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
		</svg>
	</button>
</div>
