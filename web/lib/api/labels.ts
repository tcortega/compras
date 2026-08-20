import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { LABEL_RUBRIC, type LabelRubric } from '@/lib/flags'

export type TriageLabelRow = {
  flag_id: string
  item_id: string
  label: LabelRubric
  evidence_url: string
  notes: string
  kind: string
}

const HEADER = 'flag_id,item_id,label,evidence_url,notes,kind'

function isRubric(raw: string): raw is LabelRubric {
  return LABEL_RUBRIC.some((row) => row.value === raw)
}

export function labelsPath(): string {
  const configured = process.env.TRIAGE_LABELS_PATH?.trim()
  if (configured) return configured
  return path.resolve(process.cwd(), '..', 'labels', 'triage-labels.csv')
}

function csvEscape(value: string): string {
  if (/[",\n\r]/.test(value)) return `"${value.replaceAll('"', '""')}"`
  return value
}

function parseLine(line: string): string[] {
  const out: string[] = []
  let cur = ''
  let quoted = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (quoted) {
      if (ch === '"' && line[i + 1] === '"') {
        cur += '"'
        i += 1
        continue
      }
      if (ch === '"') {
        quoted = false
        continue
      }
      cur += ch
      continue
    }
    if (ch === '"') {
      quoted = true
      continue
    }
    if (ch === ',') {
      out.push(cur)
      cur = ''
      continue
    }
    cur += ch
  }
  out.push(cur)
  return out
}

export async function readTriageLabels(): Promise<TriageLabelRow[]> {
  try {
    const text = await readFile(labelsPath(), 'utf8')
    return text
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && line !== HEADER)
      .flatMap((line) => {
        const cols = parseLine(line)
        const label = cols[2] ?? ''
        if (!isRubric(label)) return []
        return [
          {
            flag_id: cols[0] ?? '',
            item_id: cols[1] ?? '',
            label,
            evidence_url: cols[3] ?? '',
            notes: cols[4] ?? '',
            kind: cols[5] ?? '',
          },
        ]
      })
  } catch {
    return []
  }
}

export async function appendTriageLabel(row: TriageLabelRow): Promise<TriageLabelRow> {
  if (!isRubric(row.label)) throw new Error('rótulo fora da rubrica')
  const file = labelsPath()
  await mkdir(path.dirname(file), { recursive: true })
  let existing = ''
  try {
    existing = await readFile(file, 'utf8')
  } catch {
    existing = ''
  }
  const prefix = existing.trim().length === 0 ? `${HEADER}\n` : existing.endsWith('\n') ? existing : `${existing}\n`
  const line = [
    csvEscape(row.flag_id),
    csvEscape(row.item_id),
    csvEscape(row.label),
    csvEscape(row.evidence_url),
    csvEscape(row.notes),
    csvEscape(row.kind),
  ].join(',')
  await writeFile(file, `${prefix}${line}\n`, 'utf8')
  return row
}
