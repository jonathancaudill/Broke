# Rewrite Broke: SvelteKit → Next.js 15 + React + Tailwind

## Context
Rewrite the "Broke" AI portfolio chat agent from SvelteKit/Svelte 5 to Next.js 15 (App Router) with React 19 and Tailwind CSS v4. The app is an AI-powered chat interface representing Jonathan Caudill to recruiters, featuring multi-agent orchestration, RAG via Supabase, SSE streaming, and slash commands. Deployed to Vercel.

## Approach
The server-side AI logic (orchestrator, agents, tools, prompts, knowledge store) is framework-agnostic TypeScript using the Vercel AI SDK — it ports with minimal changes (`$env` → `process.env`, `$lib` → `@/lib`). The main work is converting Svelte components to React and porting CSS to Tailwind.

---

## Steps

### 1. Scaffold Next.js project
- Update `package.json`: swap SvelteKit deps for `next`, `react`, `react-dom`, `tailwindcss`, `@tailwindcss/postcss`
- Remove: `@sveltejs/adapter-vercel`, `@sveltejs/kit`, `@sveltejs/vite-plugin-svelte`, `svelte`, `svelte-check`, `vite`
- Create `next.config.ts`, `postcss.config.mjs`, update `tsconfig.json`
- Delete `svelte.config.js`, `vite.config.ts`, `src/app.html`, `src/app.d.ts`

### 2. Create `src/app/globals.css`
- `@import "tailwindcss"` + `@theme` block with custom colors/fonts
- Keep CSS custom properties, `@keyframes` (typing, fadeIn, send-pop), markdown-in-bubble styles, scrollbar styling
- Everything else moves to Tailwind utility classes on JSX elements

### 3. Create `src/app/layout.tsx`
- Metadata (title, viewport, theme-color), font imports, globals.css import
- Simple `<html><body>{children}</body></html>` shell

### 4. Port server-side modules (minimal changes)
Copy to `src/lib/server/` with these swaps:
- `ai.ts`, `knowledge/store.ts`: `$env/dynamic/private` → `process.env`
- `orchestrator.ts`, `agents/registry.ts`, `tools/rag-query.ts`, `tools/call-agent.ts`: `$lib/` → `@/lib/`
- `prompts.ts`, `tools/web-search.ts`, `tools/scheduling.ts`, `types.ts`: copy unchanged

### 5. Convert 5 API routes to Next.js Route Handlers
Each `src/routes/api/X/+server.ts` → `src/app/api/X/route.ts`:
- `RequestHandler` → `export async function GET/POST(request: NextRequest)`
- `json()` from `@sveltejs/kit` → `NextResponse.json()`
- SSE streaming (`ReadableStream` + `new Response`) works identically
- Add `export const maxDuration = 60` on streaming routes for Vercel

### 6. Convert `ChatInput.svelte` → `src/components/ChatInput.tsx`
- `$bindable` → controlled component (value + onChange props)
- `$props()` → function parameter destructuring
- `bind:this` → `useRef`, `oninput` → `onInput`, `onkeydown` → `onKeyDown`
- Auto-resize textarea, enter-to-submit, animated send button

### 7. Convert `ChatMessage.svelte` → `src/components/ChatMessage.tsx`
- `$derived` → `useMemo` for markdown parsing via `marked`
- `{@html}` → `dangerouslySetInnerHTML`
- `class:tail={isLastInGroup}` → conditional className
- Debug mode tool call display, avatar logic, bubble styling

### 8. Convert `+page.svelte` → `src/app/page.tsx` (largest piece)
- `'use client'` component
- `$state` → `useState` for messages, input, isLoading, debugMode, reasoningEffort, streamStatus
- `$state` element binding → `useRef` for chatContainer
- SSE streaming: use `useRef` for mutable streaming message, flush to state on each delta
- `await tick()` + scroll → `useEffect` on messages dependency
- All slash command handling (`/debug`, `/clear`, `/help`, `/agents`, `/thinking`, `/ask`, `/chat`, `/prompt`)
- 20-message memory window

### 9. Move static assets & clean up
- `static/` → `public/` (logo.png, background.png, etc.)
- Delete all `.svelte` files, `src/routes/`, `.svelte-kit/`
- `.env` stays as-is (no `NEXT_PUBLIC_` prefix needed — all server-only)

### 10. Verify
- `npm run dev` — app starts
- `/api/agents` — GET route returns agent list
- Chat UI renders, send a message, SSE streaming works
- All slash commands functional
- Mobile viewport + safe-area styling correct

## Key Files
| Source (Svelte) | Target (Next.js) |
|---|---|
| `src/routes/+page.svelte` | `src/app/page.tsx` |
| `src/routes/+layout.svelte` | `src/app/layout.tsx` |
| `src/app.css` | `src/app/globals.css` |
| `src/lib/components/ChatInput.svelte` | `src/components/ChatInput.tsx` |
| `src/lib/components/ChatMessage.svelte` | `src/components/ChatMessage.tsx` |
| `src/routes/api/chat/+server.ts` | `src/app/api/chat/route.ts` |
| `src/routes/api/ask/+server.ts` | `src/app/api/ask/route.ts` |
| `src/routes/api/agents/+server.ts` | `src/app/api/agents/route.ts` |
| `src/routes/api/prompts/+server.ts` | `src/app/api/prompts/route.ts` |
| `src/routes/api/direct-chat/+server.ts` | `src/app/api/direct-chat/route.ts` |
| `src/lib/server/*` | `src/lib/server/*` (minor edits) |
| `src/lib/types.ts` | `src/lib/types.ts` (unchanged) |
