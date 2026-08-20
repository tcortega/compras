import { formatMoney } from '@/lib/format'

export function Money({ value }: { value: number | null | undefined }) {
  return <span className="num">{formatMoney(value)}</span>
}
