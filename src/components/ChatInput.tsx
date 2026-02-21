'use client'

import { useRef, useCallback } from 'react'
import { PlusCircleIcon } from '@/components/Icons'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onsubmit: (text: string) => void
  disabled?: boolean
}

export default function ChatInput({ value, onChange, onsubmit, disabled = false }: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const handleKeydown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }, [value, disabled])

  const submit = useCallback(() => {
    const text = value.trim()
    if (!text || disabled) return
    onsubmit(text)
    onChange('')
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
    }
  }, [value, disabled, onsubmit, onChange])

  const autoResize = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
  }, [])

  return (
    <div className="input-bar">
      <button className="plus-button icon-button" aria-label="More options">
        <PlusCircleIcon size={36} />
      </button>
      <textarea
        ref={inputRef}
        value={value}
        onChange={(e) => {
          onChange(e.target.value)
          autoResize(e)
        }}
        onKeyDown={handleKeydown}
        placeholder="iMessage"
        rows={1}
        disabled={disabled}
      />
      <div className={`send-button-wrap ${value.trim().length > 0 ? 'has-text' : ''}`}>
        <button 
          onClick={submit} 
          disabled={disabled || !value.trim()} 
          className="send-button" 
          aria-label="Send message"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
            <path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
