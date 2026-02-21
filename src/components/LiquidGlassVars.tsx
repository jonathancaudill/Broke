'use client'

import { useMemo } from 'react'
import {
	liquidGlassConfig,
	getGlassControlsForElement,
	tintToRgba,
	shadowToCss,
	type LiquidGlassElementKey,
} from '@/lib/liquid-glass-config'

const ELEMENT_SELECTORS: Record<LiquidGlassElementKey, string> = {
	headerBadge: '.header-name-badge',
	backButton: '.back-button',
	input: '.input-bar textarea',
	plusButton: '.plus-button',
	assistantBubble: '.bubble-assistant',
	typingIndicator: '.typing-indicator',
}

export default function LiquidGlassVars() {
	const css = useMemo(() => {
		const defaultC = liquidGlassConfig.controls
		const lines: string[] = [
			`.chat-app {`,
			`  --glass-blur: ${defaultC.blurRadius}px;`,
			`  --glass-tint: ${tintToRgba(defaultC.tint)};`,
			`  --glass-shadow: ${shadowToCss(defaultC.shadowExpand, defaultC.shadowFactor, defaultC.shadowPosition)};`,
			`  --glass-saturate: 180%;`,
			`  --glass-border-color: rgba(255, 255, 255, 0.3);`,
			`}`,
		]
		const keys: LiquidGlassElementKey[] = [
			'headerBadge',
			'backButton',
			'input',
			'plusButton',
			'assistantBubble',
			'typingIndicator',
		]
		for (const key of keys) {
			const c = getGlassControlsForElement(key)
			const sel = ELEMENT_SELECTORS[key]
			lines.push(
				`${sel} {`,
				`  --glass-blur: ${c.blurRadius}px;`,
				`  --glass-tint: ${tintToRgba(c.tint)};`,
				`  --glass-shadow: ${shadowToCss(c.shadowExpand, c.shadowFactor, c.shadowPosition)};`,
				`  --glass-border-color: rgba(255, 255, 255, ${Math.min(0.5, c.tint.a + 0.2)});`,
				`}`
			)
		}
		return lines.join('\n')
	}, [])

	return <style dangerouslySetInnerHTML={{ __html: css }} />
}
