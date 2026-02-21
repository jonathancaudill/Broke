'use client'

import { useMemo } from 'react'
import { marked } from 'marked'
import type { Message, ToolCall } from '@/lib/types'

interface ChatMessageProps {
  message: Message
  debug?: boolean
  isLastInGroup?: boolean
}

const TOOL_MARKER_RE = /<<TOOL:([^>]+)>>/

function describeToolCall(name: string, args: Record<string, unknown>): string {
  if (name === 'rag_query') {
    return `searching knowledge base (${args.collection || 'all'})`
  }
  if (name === 'call_agent') {
    return `talking to ${args.agent_name}`
  }
  if (name === 'check_availability') {
    return 'checking calendar'
  }
  if (name === 'book_meeting') {
    return 'booking meeting'
  }
  if (name === 'web_search') {
    return `searching the web`
  }
  return name
}

type Segment =
  | { type: 'text'; content: string; html: string }
  | { type: 'tool'; toolCallId: string; toolCall?: ToolCall }

function parseSegments(content: string, toolCalls: ToolCall[]): Segment[] {
  if (!content) return []

  const toolMap = new Map(toolCalls.map(tc => [tc.id, tc]))
  const segments: Segment[] = []

  // Split on tool markers first
  const parts = content.split(TOOL_MARKER_RE)

  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) {
      // Odd indices are captured tool call IDs
      const toolCallId = parts[i]
      segments.push({ type: 'tool', toolCallId, toolCall: toolMap.get(toolCallId) })
    } else {
      // Even indices are text — split further on double newlines
      const text = parts[i]
      const paragraphs = text.split(/\n\n+/)
      for (const p of paragraphs) {
        const trimmed = p.trim()
        if (!trimmed) continue
        const html = marked.parse(trimmed, { async: false }) as string
        segments.push({ type: 'text', content: trimmed, html })
      }
    }
  }

  return segments
}

export default function ChatMessage({ message, debug = false, isLastInGroup = true }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const isCommand = message.type === 'command'

  const segments = useMemo(() => {
    if (isUser || isSystem || isCommand) return []
    return parseSegments(message.content || '', message.toolCalls || [])
  }, [isUser, isSystem, isCommand, message.content, message.toolCalls])

  if (isCommand) {
    if (isUser) {
      return (
        <div className="message-row user">
          <div className="bubble command-bubble">{message.content}</div>
        </div>
      )
    }
    return (
      <div className="system-message">
        <pre>{message.content}</pre>
      </div>
    )
  }

  if (isSystem) {
    return (
      <div className="system-message">
        <pre>{message.content}</pre>
      </div>
    )
  }

  if (isUser) {
    return (
      <div className="message-row user">
        <div className={`bubble bubble-user ${isLastInGroup ? 'tail' : ''}`}>
          <span className="bubble-text">{message.content}</span>
        </div>
      </div>
    )
  }

  // Assistant message — render as multiple bubbles
  const textSegments = segments.filter(s => s.type === 'text')
  const lastTextIndex = textSegments.length - 1
  let textCounter = -1

  return (
    <>
      {segments.map((seg, i) => {
        if (seg.type === 'tool') {
          return (
            <div key={`tool-${seg.toolCallId}`} className="tool-activity">
              <div className="tool-activity-dot" />
              <span className="tool-activity-label">
                {seg.toolCall ? describeToolCall(seg.toolCall.name, seg.toolCall.args) : '...'}
              </span>
              {debug && seg.toolCall?.result && (
                <details className="tool-activity-details">
                  <summary>result</summary>
                  <pre>{seg.toolCall.result}</pre>
                </details>
              )}
            </div>
          )
        }

        textCounter++
        const isLast = textCounter === lastTextIndex
        const showAvatar = isLast && isLastInGroup

        return (
          <div key={`text-${i}`} className="assistant-row">
            {showAvatar ? (
              <img src="/logo.png" alt="" className="assistant-avatar" />
            ) : (
              <div className="assistant-avatar-spacer"></div>
            )}
            <div
              className={`bubble bubble-assistant ${showAvatar ? 'tail' : ''}`}
              dangerouslySetInnerHTML={{ __html: seg.html }}
            />
          </div>
        )
      })}
    </>
  )
}
