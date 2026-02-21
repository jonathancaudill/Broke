'use client'

import { Agentation } from 'agentation'

export default function AgentationWrapper() {
	if (process.env.NODE_ENV !== 'development') return null
	return <Agentation />
}
