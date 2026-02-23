'use client'

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { computeGaussianKernelByRadius } from 'liquid-glass/src/utils'
import ChatMessage from '@/components/ChatMessage'
import ChatInput from '@/components/ChatInput'
import LiquidGlassVars from '@/components/LiquidGlassVars'
import StatusBar from '@/components/StatusBar'
import { GitHubIcon } from '@/components/Icons'
import type { Message, ToolCall } from '@/lib/types'

const MEMORY_WINDOW = 20

const HELP_TEXT = `commands:
  /debug              toggle debug mode
  /clear              reset conversation
  /agents             list available agents
  /thinking [level]   set reasoning effort (low / medium / high)
  /ask <agent> <query> run a single agent in isolation
  /chat <query>       talk to the llm directly (no tools)
  /prompt [agent]     show system prompt (all or one)
  /help               show this message`

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [debugMode, setDebugMode] = useState(false)
  const [reasoningEffort, setReasoningEffort] = useState<string | null>(null)
  const [streamStatus, setStreamStatus] = useState<string | null>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const streamingMessageRef = useRef<Message | null>(null)

  const scrollToBottom = useCallback(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const addSystemMessage = useCallback((content: string) => {
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      role: 'system',
      content,
      type: 'command'
    }])
  }, [])

  const describeToolCall = (name: string, args: Record<string, unknown>): string => {
    if (name === 'rag_query') return `searching knowledge base (${args.collection || 'all'})`
    if (name === 'call_agent') return `talking to ${args.agent_name}`
    if (name === 'check_availability') return 'checking calendar'
    if (name === 'book_meeting') return 'booking meeting'
    if (name === 'web_search') return 'searching the web'
    return name
  }

  const parseSSEStream = async (response: Response, msgIndex: number) => {
    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const event = JSON.parse(data)

            setMessages(prev => {
              const msg = prev[msgIndex]
              if (!msg) return prev

              let updated: Message | null = null

              if (event.type === 'text-delta') {
                updated = { ...msg, content: msg.content + event.textDelta }
                setStreamStatus(null)
              } else if (event.type === 'tool-call') {
                setStreamStatus(describeToolCall(event.toolName, event.args) + '...')
                const marker = `\n\n<<TOOL:${event.toolCallId}>>\n\n`
                updated = {
                  ...msg,
                  content: msg.content + marker,
                  toolCalls: [...(msg.toolCalls || []), {
                    id: event.toolCallId,
                    name: event.toolName,
                    args: event.args
                  }]
                }
              } else if (event.type === 'tool-result') {
                setStreamStatus(null)
                updated = {
                  ...msg,
                  toolCalls: (msg.toolCalls || []).map((t: ToolCall) =>
                    t.id === event.toolCallId ? { ...t, result: event.result } : t
                  )
                }
              } else if (event.type === 'error') {
                updated = { ...msg, content: msg.content + `\n\nerror: ${event.message}` }
                setStreamStatus(null)
              }

              if (!updated) return prev
              return prev.map((m, i) => i === msgIndex ? updated! : m)
            })
            scrollToBottom()
          } catch (e) {
            console.error('[sse] failed to parse event:', e, part)
          }
        }
      }
    }
  }

  const sendChat = async (text: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      type: 'chat'
    }
    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      type: 'chat',
      toolCalls: []
    }
    
    setMessages(prev => [...prev, userMsg, assistantMsg])
    const msgIndex = messages.length + 1
    setIsLoading(true)
    setStreamStatus(null)
    scrollToBottom()

    const allMessages = [...messages, userMsg]
    const chatMessages = allMessages
      .filter((m) => m.type === 'chat' && m.content.trim())
      .slice(-MEMORY_WINDOW)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: chatMessages })
      })

      if (!response.ok) {
        setMessages(prev => {
          const updated = [...prev]
          updated[msgIndex].content = `error: ${response.status} ${response.statusText}`
          return updated
        })
        return
      }

      await parseSSEStream(response, msgIndex)
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        updated[msgIndex].content = `error: ${err}`
        return updated
      })
    } finally {
      setIsLoading(false)
      setStreamStatus(null)
      scrollToBottom()
    }
  }

  const streamFromEndpoint = async (endpoint: string, body: Record<string, unknown>) => {
    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      type: 'chat',
      toolCalls: []
    }
    
    setMessages(prev => [...prev, assistantMsg])
    const msgIndex = messages.length
    setIsLoading(true)
    setStreamStatus(null)
    scrollToBottom()

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })

      if (!response.ok) {
        setMessages(prev => {
          const updated = [...prev]
          updated[msgIndex].content = `error: ${response.status} ${response.statusText}`
          return updated
        })
        return
      }

      await parseSSEStream(response, msgIndex)
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        updated[msgIndex].content = `error: ${err}`
        return updated
      })
    } finally {
      setIsLoading(false)
      setStreamStatus(null)
      scrollToBottom()
    }
  }

  const handleAskCommand = async (text: string) => {
    const rest = text.slice(5).trim()
    const spaceIdx = rest.indexOf(' ')
    if (spaceIdx === -1) {
      addSystemMessage('usage: /ask <agent> <query>')
      return
    }
    const agent = rest.slice(0, spaceIdx).toLowerCase()
    const query = rest.slice(spaceIdx + 1).trim()

    setIsLoading(true)
    scrollToBottom()

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent, query })
      })
      const data = await response.json()
      if (data.error) {
        addSystemMessage(`error: ${data.error}`)
      } else {
        addSystemMessage(data.result)
      }
    } catch (err) {
      addSystemMessage(`error: ${err}`)
    } finally {
      setIsLoading(false)
      scrollToBottom()
    }
  }

  const handleCommand = async (text: string) => {
    setMessages(prev => [...prev, {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      type: 'command'
    }])
    scrollToBottom()

    const low = text.toLowerCase().trim()

    if (low === '/debug') {
      setDebugMode(prev => !prev)
      addSystemMessage(`debug mode: ${!debugMode ? 'ON' : 'OFF'}`)
      return
    }

    if (low === '/clear') {
      setMessages([])
      return
    }

    if (low === '/help') {
      addSystemMessage(HELP_TEXT)
      return
    }

    if (low === '/agents') {
      try {
        const response = await fetch('/api/agents')
        const data = await response.json()
        const list = data.agents
          .map((a: { name: string; description: string }) => `  ${a.name} — ${a.description}`)
          .join('\n')
        addSystemMessage(list)
      } catch {
        addSystemMessage('failed to fetch agent list')
      }
      return
    }

    if (low.startsWith('/thinking')) {
      const level = text.slice(9).trim().toLowerCase()
      const validLevels = ['minimal', 'low', 'medium', 'high']
      if (!level) {
        addSystemMessage(
          `reasoning effort: ${reasoningEffort || 'default'}\noptions: ${validLevels.join(', ')}`
        )
      } else if (validLevels.includes(level)) {
        setReasoningEffort(level)
        addSystemMessage(`reasoning effort → ${level}`)
      } else {
        addSystemMessage(`invalid. choose from: ${validLevels.join(', ')}`)
      }
      return
    }

    if (low.startsWith('/ask ')) {
      await handleAskCommand(text)
      return
    }

    if (low.startsWith('/chat ')) {
      const query = text.slice(6).trim()
      if (!query) {
        addSystemMessage('usage: /chat <query>')
        return
      }
      await streamFromEndpoint('/api/direct-chat', { query })
      return
    }

    if (low.startsWith('/prompt')) {
      const agent = text.slice(7).trim().toLowerCase()
      try {
        const url = agent ? `/api/prompts?agent=${agent}` : '/api/prompts'
        const response = await fetch(url)
        const data = await response.json()
        if (data.error) {
          addSystemMessage(`error: ${data.error}`)
        } else {
          addSystemMessage(data.content)
        }
      } catch {
        addSystemMessage('failed to fetch prompt')
      }
      return
    }

    addSystemMessage('unknown command. type /help for available commands.')
  }

  const handleSubmit = async (text: string) => {
    if (!text.trim()) return

    if (text.trim().startsWith('/')) {
      await handleCommand(text.trim())
    } else {
      await sendChat(text.trim())
    }
  }

  const liquidGlassBlur = useMemo(() => computeGaussianKernelByRadius(16).length, [])

  return (
    <>
      <StatusBar />
      <div className="chat-app" data-liquid-glass-blur={liquidGlassBlur}>
        <LiquidGlassVars />
      <div className="chat-bg"></div>

      <header className="chat-header">
        <div className="header-top">
          <a
            href="https://github.com/jonathancaudill/Broke"
            target="_blank"
            rel="noopener noreferrer"
            className="back-button icon-button"
            aria-label="GitHub"
          >
            <GitHubIcon size={36} />
          </a>
          <div className="header-profile">
            <img src="/logo.png" alt="Broke" className="header-avatar" />
            <span className="header-name-badge">Broke 💸</span>
          </div>
        </div>
        {debugMode && <span className="debug-badge">debug</span>}
      </header>

      <div className="chat-messages" ref={chatContainerRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>hey, i&apos;m broke. ask me about jonathan.</p>
            <p className="hint">type /help for commands</p>
          </div>
        )}

        {messages.map((message, i) => {
          const isPlaceholder = isLoading && i === messages.length - 1 && message.role === 'assistant' && !message.content
          if (isPlaceholder) return null

          const prevMsg = messages[i - 1]
          const showTimestamp = i === 0 || (message.type === 'chat' && prevMsg?.type !== 'chat')
          const nextMsg = messages[i + 1]
          const isLastInGroup = !nextMsg || nextMsg.role !== message.role || nextMsg.type !== message.type
          const lastUserChatIndex = messages.reduce((last, m, idx) => (m.role === 'user' && m.type === 'chat' ? idx : last), -1)
          const isLastUserMessage = message.role === 'user' && message.type === 'chat' && i === lastUserChatIndex
          const isUserAfterAssistant = message.role === 'user' && prevMsg?.role === 'assistant'

          return (
            <div key={message.id} className={isUserAfterAssistant ? 'message-block message-after-assistant' : 'message-block'}>
              {showTimestamp && (
                <div className="timestamp">
                  Today {new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                </div>
              )}
              <ChatMessage message={message} debug={debugMode} isLastInGroup={isLastInGroup} />

              {isLastUserMessage && (
                <div className="delivered-status">Delivered</div>
              )}
            </div>
          )
        })}

        {streamStatus && <div className="stream-status">{streamStatus}</div>}

        {isLoading && messages.length > 0 && messages[messages.length - 1]?.role === 'assistant' && !messages[messages.length - 1]?.content && (
          <div className="typing-indicator-wrap">
            <img src="/logo.png" alt="" className="assistant-avatar" />
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      <div className="input-bar-blur" aria-hidden="true" />
      <ChatInput value={input} onChange={setInput} onsubmit={handleSubmit} disabled={isLoading} />
      </div>
    </>
  )
}
