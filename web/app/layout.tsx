import { IBM_Plex_Mono, IBM_Plex_Sans, Newsreader } from 'next/font/google'
import { SITE_NAME, SITE_TAG, SLICE_LABEL, copy } from '@/lib/copy'
import type { Metadata } from 'next'
import './globals.css'

const serif = Newsreader({
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap',
})

const sans = IBM_Plex_Sans({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-sans',
  display: 'swap',
})

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: {
    default: `${SITE_NAME} · ${SITE_TAG}`,
    template: `%s · ${SITE_NAME}`,
  },
  description: `Consulta pública a órgãos, fornecedores, contratações e itens. Recorte ${SLICE_LABEL}. ${copy.coverageIncomplete}`,
  robots: { index: true, follow: true },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={`${serif.variable} ${sans.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
