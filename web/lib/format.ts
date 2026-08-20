import { copy } from '@/lib/copy'

const moneyFmt = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})

const intFmt = new Intl.NumberFormat('pt-BR')

const decFmt = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 4,
})

export function formatMoney(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return copy.noValue
  return moneyFmt.format(value)
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return copy.noValue
  return intFmt.format(value)
}

export function formatDecimal(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return copy.noValue
  return decFmt.format(value)
}

export function formatCnpj(raw: string): string {
  const d = raw.replace(/\D/g, '')
  if (d.length !== 14) return raw
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return copy.noValue
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return copy.noValue
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(d)
}

export function formatQuarter(quarter: string | null): string {
  if (!quarter) return 'vários trimestres'
  const m = /^(\d{4})-Q([1-4])$/.exec(quarter)
  if (!m) return quarter
  return `${m[2]}º trim. ${m[1]}`
}

export function formatEsfera(esfera: string): string {
  if (esfera === 'federal') return 'Federal'
  if (esfera === 'estadual') return 'Estadual'
  if (esfera === 'municipal') return 'Municipal'
  return esfera
}

export function formatPoder(poder: string): string {
  const map: Record<string, string> = {
    executivo: 'Executivo',
    legislativo: 'Legislativo',
    judiciario: 'Judiciário',
  }
  return map[poder] ?? poder
}

export function yearFromQuarter(quarter: string | null): string | null {
  if (!quarter) return null
  const m = /^(\d{4})/.exec(quarter)
  return m?.[1] ?? null
}
