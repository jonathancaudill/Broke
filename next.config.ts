import type { NextConfig } from 'next'
import path from 'path'

const nextConfig: NextConfig = {
	transpilePackages: ['liquid-glass'],
	webpack: (config) => {
		config.module.rules.push(
			{
				test: /\.glsl$/,
				resourceQuery: /raw/,
				type: 'asset/source',
			},
			{
				test: /\.(mp4|webm|png|jpg|jpeg|gif|webp|svg)$/,
				include: [path.join(process.cwd(), 'node_modules/liquid-glass')],
				type: 'asset/resource',
			}
		)
		return config
	},
}

export default nextConfig
