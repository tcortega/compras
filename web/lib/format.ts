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

function asNumber(value: number | string | null | undefined): number | null {
  if (value == null || value === '') return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  const n = Number(value.trim().replace(/\s/g, '').replace(',', '.'))
  return Number.isFinite(n) ? n : null
}

export function formatMoney(value: number | string | null | undefined): string {
  const n = asNumber(value)
  if (n == null) return copy.noValue
  return moneyFmt.format(n)
}

export function formatNumber(value: number | string | null | undefined): string {
  const n = asNumber(value)
  if (n == null) return copy.noValue
  return intFmt.format(n)
}

export function formatDecimal(value: number | string | null | undefined): string {
  const n = asNumber(value)
  if (n == null) return copy.noValue
  return decFmt.format(n)
}

export function formatCnpj(raw: string): string {
  const d = raw.replace(/\D/g, '')
  if (d.length !== 14) return raw
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

const LOCAL_DATE = /^(\d{4})-(\d{2})-(\d{2})$/
const UTC_MIDNIGHT = /^(\d{4})-(\d{2})-(\d{2})T00:00:00(?:\.\d+)?(?:Z|[+-]00:00)$/

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return copy.noValue
  const calendar = LOCAL_DATE.exec(iso) ?? UTC_MIDNIGHT.exec(iso)
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
  if (source === 'compras.gov.br' || source === 'compras_gov') return 'Compras.gov.br'
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

export function hasCanonicalUnit(unit: string | null | undefined): unit is string {
  return Boolean(unit) && unit !== 'unknown'
}

export function formatCanonicalUnit(unit: string | null | undefined): string {
  return hasCanonicalUnit(unit) ? unit : 'não mapeada'
}

export function formatUnitPair(
  unidadeMedida: string,
  unidadeCanonica: string | null | undefined,
): string {
  return hasCanonicalUnit(unidadeCanonica) ? `${unidadeMedida} · ${unidadeCanonica}` : unidadeMedida
}

export function hasWarehouseBasePrice(row: {
  unidadeCanonica?: string | null
  valorPorUnidadeCanonica?: number | null
}): boolean {
  return hasCanonicalUnit(row.unidadeCanonica) && row.valorPorUnidadeCanonica != null
}
