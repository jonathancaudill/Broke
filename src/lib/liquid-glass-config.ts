/**
 * Single source of truth for liquid-glass styling (liquid-glass-studio–compatible params).
 * Edit `liquidGlassConfig.controls` for global defaults and `elementOverrides` for per-element overrides.
 */

export interface LiquidGlassTint {
	r: number
	g: number
	b: number
	a: number
}

export interface LiquidGlassShadowPosition {
	x: number
	y: number
}

export interface LiquidGlassControls {
	language?: string[]
	refThickness: number
	refFactor: number
	refDispersion: number
	refFresnelRange: number
	refFresnelHardness: number
	refFresnelFactor: number
	glareRange: number
	glareHardness: number
	glareFactor: number
	glareConvergence: number
	glareOppositeFactor: number
	glareAngle: number
	blurRadius: number
	blurEdge: boolean
	tint: LiquidGlassTint
	shadowExpand: number
	shadowFactor: number
	shadowPosition: LiquidGlassShadowPosition
	bgType: number
	shapeWidth: number
	shapeHeight: number
	shapeRadius: number
	shapeRoundness: number
	mergeRate: number
	showShape1: boolean
	springSizeFactor: number
	step: number
}

export type LiquidGlassElementKey =
	| 'headerBadge'
	| 'backButton'
	| 'input'
	| 'plusButton'
	| 'assistantBubble'
	| 'typingIndicator'

export interface LiquidGlassConfig {
	version: string
	timestamp?: string
	controls: LiquidGlassControls
	elementOverrides?: Partial<Record<LiquidGlassElementKey, Partial<LiquidGlassControls>>>
}

const defaultControls: LiquidGlassControls = {
	language: ['en-US'],
	refThickness: 20,
	refFactor: 1.4,
	refDispersion: 7,
	refFresnelRange: 30,
	refFresnelHardness: 20,
	refFresnelFactor: 20,
	glareRange: 30,
	glareHardness: 20,
	glareFactor: 90,
	glareConvergence: 50,
	glareOppositeFactor: 80,
	glareAngle: -45,
	blurRadius: 10,
	blurEdge: true,
	tint: { r: 255, g: 255, b: 255, a: 0.69 },
	shadowExpand: 25,
	shadowFactor: 15,
	shadowPosition: { x: 0, y: -10 },
	bgType: 0,
	shapeWidth: 200,
	shapeHeight: 200,
	shapeRadius: 80,
	shapeRoundness: 5,
	mergeRate: 0.05,
	showShape1: true,
	springSizeFactor: 10,
	step: 9,
}

export const liquidGlassConfig: LiquidGlassConfig = {
	version: '1.0.0',
	timestamp: '2026-02-21T02:10:04.063Z',
	controls: defaultControls,
	elementOverrides: {
		headerBadge: {
			tint: { r: 255, g: 255, b: 255, a: 0.4 },
			blurRadius: 10,
			shadowExpand: 8,
			shadowFactor: 6,
			shadowPosition: { x: 0, y: 2 },
		},
		backButton: {
			tint: { r: 255, g: 255, b: 255, a: 0.2 },
			blurRadius: 1,
			shadowExpand: 8,
			shadowFactor: 6,
			shadowPosition: { x: 0, y: 2 },
		},
		input: {
			tint: { r: 255, g: 255, b: 255, a: 0.65 },
			blurRadius: 1,
			shadowExpand: 12,
			shadowFactor: 4,
			shadowPosition: { x: 0, y: 2 },
		},
		plusButton: {
			tint: { r: 255, g: 255, b: 255, a: 0.25 },
			blurRadius: 1,
			shadowExpand: 8,
			shadowFactor: 5,
			shadowPosition: { x: 0, y: 2 },
		},
		assistantBubble: {
			tint: { r: 229, g: 229, b: 234, a: 0.6 },
			blurRadius: 1,
			shadowExpand: 12,
			shadowFactor: 4,
			shadowPosition: { x: 0, y: 2 },
		},
		typingIndicator: {
			tint: { r: 229, g: 229, b: 234, a: 0.45 },
			blurRadius: 8,
			shadowExpand: 8,
			shadowFactor: 3,
			shadowPosition: { x: 0, y: 2 },
		},
	},
}

function mergeControls(
	base: LiquidGlassControls,
	overrides?: Partial<LiquidGlassControls>
): LiquidGlassControls {
	if (!overrides) return base
	return {
		...base,
		...overrides,
		tint: { ...base.tint, ...overrides.tint },
		shadowPosition: { ...base.shadowPosition, ...overrides.shadowPosition },
	}
}

export function getGlassControlsForElement(
	elementKey: LiquidGlassElementKey
): LiquidGlassControls {
	const base = liquidGlassConfig.controls
	const overrides = liquidGlassConfig.elementOverrides?.[elementKey]
	return mergeControls(base, overrides)
}

export function tintToRgba(t: LiquidGlassTint): string {
	return `rgba(${t.r}, ${t.g}, ${t.b}, ${t.a})`
}

export function shadowToCss(
	expand: number,
	factor: number,
	pos: LiquidGlassShadowPosition
): string {
	const a = factor / 100
	return `${pos.x}px ${pos.y}px ${expand}px rgba(0, 0, 0, ${a})`
}
