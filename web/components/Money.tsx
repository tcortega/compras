import { formatMoney } from '@/lib/format'

export function Money({ value }: { value: number | string | null | undefined }) {
  return <span className="num">{formatMoney(value)}</span>
}
