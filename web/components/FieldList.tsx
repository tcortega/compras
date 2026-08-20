import type { ReactNode } from 'react'

export type Field = {
  label: string
  value: ReactNode
  mono?: boolean
}

export function FieldList({ fields }: { fields: Field[] }) {
  return (
    <dl className="fields">
      {fields.map((f) => (
        <div key={f.label}>
          <dt>{f.label}</dt>
          <dd className={f.mono ? 'mono' : undefined}>{f.value}</dd>
        </div>
      ))}
    </dl>
  )
}
