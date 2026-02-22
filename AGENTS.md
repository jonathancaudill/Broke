# AGENTS.md - Coding Agent Guidelines for Broke

## Project Overview

Broke is a Next.js 15 application that powers an AI-powered conversational agent portfolio system. It answers questions about Jonathan Caudill's skills, experience, projects, and background using RAG (Retrieval Augmented Generation) with Supabase vector storage.

## Build/Lint/Test Commands

```bash
npm run dev              # Start dev server (http://localhost:3000)
npm run build            # Build for production
npm run start            # Start production server
npm run lint             # Run ESLint
npm run embed            # Embed knowledge markdown files into Supabase
```

**Note:** No test framework is currently configured. If tests are added, check package.json for the test command.

## Project Structure

```
src/
├── app/
│   ├── api/                    # API route handlers (chat, ask, agents, prompts)
│   ├── globals.css             # Global styles with Tailwind
│   ├── layout.tsx              # Root layout
│   └── page.tsx                # Main chat UI
├── components/
│   ├── ChatInput.tsx           # Chat input component
│   └── ChatMessage.tsx         # Chat message component
└── lib/
    ├── server/
    │   ├── ai.ts               # OpenAI model factory
    │   ├── orchestrator.ts     # Main chat orchestration
    │   ├── prompts.ts          # System prompts for agents
    │   ├── agents/registry.ts  # Agent definitions and dispatcher
    │   ├── knowledge/store.ts  # Supabase RAG search
    │   └── tools/              # AI SDK tools (rag-query, scheduling, etc.)
    └── types.ts                # Shared TypeScript interfaces
```

## Code Style Guidelines

### Formatting

- **Indentation:** Use tabs (not spaces)
- **Quotes:** Single quotes for strings, double quotes only when necessary
- **Semicolons:** Not required (TypeScript/JavaScript are optional)
- **Trailing commas:** None in code (follow existing patterns)

### Imports

Order imports in this sequence, separated by blank lines:

```typescript
// 1. External packages
import { streamText } from 'ai'
import { createClient, type SupabaseClient } from '@supabase/supabase-js'

// 2. Next.js internals
import { NextResponse, type NextRequest } from 'next/server'

// 3. Local imports (use @/ alias)
import { model } from '@/lib/server/ai'
import type { Message } from '@/lib/types'
```

### TypeScript

- **Strict mode:** Enabled (see tsconfig.json)
- **Interfaces:** Prefer `interface` over `type` for object shapes
- **Type imports:** Use `import type { X }` for type-only imports

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Variables/Functions | camelCase | `sendChat`, `streamStatus` |
| Components | PascalCase | `ChatMessage.tsx` |
| Interfaces/Types | PascalCase | `Message`, `AgentConfig` |
| File names (TS/JS) | kebab-case | `rag-query.ts`, `call-agent.ts` |
| API endpoints | kebab-case | `direct-chat`, `web-search` |
| Tools (AI SDK) | snake_case | `rag_query`, `call_agent` |
| Agents | snake_case | `deep_rag`, `researcher` |
| Constants | SCREAMING_SNAKE | `MAX_STEPS`, `MEMORY_WINDOW` |

### React Components

Use React 19 with hooks:

```tsx
'use client'

import { useState, useCallback } from 'react'

export default function MyComponent({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [isLoading, setIsLoading] = useState(false)
  
  return <div>...</div>
}
```

### API Routes (Next.js App Router)

Use typed Route Handlers:

```typescript
import { NextResponse, type NextRequest } from 'next/server'

export async function POST(request: NextRequest) {
  const body = (await request.json()) as { query: string }
  return NextResponse.json({ result })
}
```

### Error Handling

Use try/catch with descriptive console logging:

```typescript
try {
  const result = await someAsyncOperation()
  return NextResponse.json({ result })
} catch (err) {
  console.error('[api/endpoint] error:', err)
  return NextResponse.json({ error: String(err) }, { status: 500 })
}
```

### AI SDK Tools

Use `tool()` and `jsonSchema()` from the `ai` package:

```typescript
import { tool, jsonSchema } from 'ai'

export const myTool = tool({
  description: 'Clear description of what the tool does.',
  inputSchema: jsonSchema<{ param: string }>({
    type: 'object',
    properties: { param: { type: 'string', description: 'Parameter description.' } },
    required: ['param']
  }),
  execute: async ({ param }) => 'result string'
})
```

### Comments

Do not add comments to code unless explicitly requested. Code should be self-documenting through clear naming and structure.

## Environment Variables

Required (see `.env.example`): `OPENAI_API_KEY`, `OPENAI_MODEL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. Optional: `TAVILY_API_KEY` (enables web search for the researcher agent).

Access via `process.env`:

```typescript
const apiKey = process.env.OPENAI_API_KEY
```

## Key Dependencies

- **Next.js 15** - Framework (App Router)
- **React 19** - UI library
- **Tailwind CSS v4** - Styling
- **AI SDK** - OpenAI integration (@ai-sdk/openai, ai)
- **Supabase** - Vector database (@supabase/supabase-js)
- **Zod** - Schema validation

## Architecture Notes

1. **Orchestrator Pattern**: Main orchestrator receives queries and dispatches to specialist agents
2. **Streaming Responses**: Chat endpoints use SSE (Server-Sent Events) with ReadableStream
3. **RAG Pipeline**: Knowledge embedded via scripts/embed-knowledge.ts, searched via Supabase RPC
4. **Tool-based Agents**: Agents use AI SDK tools for RAG search, web search, and scheduling
