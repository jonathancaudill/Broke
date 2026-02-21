import type { Metadata, Viewport } from 'next'
import './globals.css'
import AgentationWrapper from '@/components/AgentationWrapper'

export const metadata: Metadata = {
  title: 'broke',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#333',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <div className="phone-frame">
          {children}
        </div>
        <AgentationWrapper />
      </body>
    </html>
  )
}
