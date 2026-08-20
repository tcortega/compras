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

const LOCAL_DATE = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return copy.noValue
  const calendar = LOCAL_DATE.exec(iso)
  if (calendar) {
    const [, year, month, day] = calendar
    return `${day}/${month}/${year}`
  }
  const instant = new Date(iso)
  if (Number.isNaN(instant.getTime())) return copy.noValue
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(instant)
}

export function formatQuarter(quarter: string | null): string {
  if (!quarter) return 'vários trimestres'
  const q = /^(\d{4})-Q([1-4])$/.exec(quarter)
  if (q) return `${q[2]}º trim. ${q[1]}`
  if (/^\d{4}$/.test(quarter)) return `${quarter} (vários trimestres)`
  return quarter
}

export function formatSource(source: string): string {
  if (source === 'pncp') return 'PNCP'
  if (source === 'compras.gov.br') return 'Compras.gov.br'
  return source
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
