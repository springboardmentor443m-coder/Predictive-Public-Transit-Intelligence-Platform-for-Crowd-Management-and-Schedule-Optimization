import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MetroFlow AI - G-Line Fleet Intelligence',
  description: 'G-Line Two-Way Fleet Management & Operational Analytics Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  )
}